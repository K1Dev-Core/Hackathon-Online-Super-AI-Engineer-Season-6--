# IoT Attack Detection — Technical Deep Dive

เอกสารเชิงเทคนิคสำหรับแชร์ความรู้และใช้ประกอบการพรีเซนต์ โฟกัสที่ข้อมูล, feature engineering, model design, training/inference, tuning, validation และข้อจำกัดของระบบตรวจจับ

เอกสารนี้ **ไม่อธิบายกระบวนการส่งไฟล์, quota หรือ leaderboard** เนื้อหาหลักคือวิธีสร้าง detector จากข้อมูล network traffic ที่มี Normal labels เป็นหลัก

## 1. Executive Summary

โจทย์เป็น anomaly detection แบบ Normal-only:

- `X_train.csv` มี 100,000 records ที่เป็น Normal
- `X_test.csv` มี 10,000 records ที่ผสม Normal และ Attack
- ไม่มี attack label ที่เชื่อถือได้ใน train
- มี 22 predictive features และ 1 `Id` column
- protocol หลักคือ TCP และ MQTT

ระบบหลักที่สร้างสำเร็จไม่ใช่ deep neural network และไม่มี serialized weight file ระบบเป็น **deterministic rule engine** ที่ fit normal profile จาก `X_train` แล้วใช้ Boolean rules ตรวจ test traffic:

```text
Normal profile
    + TCP/MQTT protocol signatures
    + stream and packet context
    + hard-negative exclusions
    = interpretable attack detector
```

มีการทดลอง ML models เพิ่มเติมเพื่อจัดอันดับ residual candidates และตรวจความสอดคล้องของหลักฐาน ได้แก่ ExtraTrees, RandomForest, HistGradientBoosting และ IsolationForest แต่ไม่ใช้เป็น decision maker หลัก เพราะ pseudo labels และ external PCAP labels มีความเสี่ยงเรื่อง label leakage และ domain shift

## 2. Problem Formulation

ให้ feature vector ของ packet เป็น `x` และ label เป็น `y ∈ {0,1}`:

- `y=0`: Normal communication
- `y=1`: Network attack

ใน supervised classification ปกติ เราจะเรียนรู้ `P(y|x)` จากตัวอย่างทั้งสอง class แต่โจทย์นี้มี `y=0` เป็นหลักใน train จึงไม่มี attack distribution ที่สมบูรณ์ให้เรียนโดยตรง

เป้าหมายจึงเปลี่ยนเป็น:

1. สร้าง approximation ของ Normal support จาก train
2. ตรวจ feature combinations ที่อยู่นอก Normal support
3. เพิ่ม protocol signatures ที่มีความหมายเชิง attack
4. ตรวจ context เพื่อลด rare-normal false positives
5. ใช้ hard negatives หักล้าง candidate ที่ดูแปลกแต่เป็น Normal

### F1 และ trade-off

```text
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 * Precision * Recall / (Precision + Recall)
```

เมื่อ baseline มี precision สูง การเพิ่ม positive labels จำนวนมากไม่จำเป็นต้องทำให้ F1 ดีขึ้น กลุ่ม candidate ใหม่ต้องมี precision สูงพอที่จะชดเชย false positives ที่เพิ่มขึ้น

## 3. Dataset Schema

### 3.1 Files

| File | Rows | Role |
|---|---:|---|
| `data/X_train.csv` | 100,000 | Normal reference |
| `data/X_test.csv` | 10,000 | unlabeled inference set |

### 3.2 Columns

`Id` ไม่ใช้เป็น predictive feature ใช้รักษา row identity เท่านั้น

| Group | Columns |
|---|---|
| Frame / protocol | `frame.len`, `frame.protocols` |
| TCP identity / timing | `tcp.stream`, `tcp.analysis.initial_rtt`, `tcp.len`, `tcp.window_size` |
| TCP flags | `tcp.flags.syn`, `tcp.flags.reset`, `tcp.flags.ack` |
| MQTT message | `mqtt.msgtype`, `mqtt.qos`, `mqtt.len`, `mqtt.topic_len` |
| MQTT session | `mqtt.conflag.qos`, `mqtt.conflag.cleansess`, `mqtt.kalive` |
| MQTT credentials | `mqtt.username_len`, `mqtt.passwd_len` |
| MQTT flags | `mqtt.retain`, `mqtt.conflag.retain`, `mqtt.conflag.willflag` |
| MQTT response | `mqtt.conack.val` |

### 3.3 Missing values

MQTT columns ที่หายบน TCP control packet เป็น **missing by design**:

- packet บางชนิดไม่มี MQTT layer
- missing ไม่ได้แปลว่า malformed
- core rule engine ไม่เติมค่า missing แบบ arbitrary
- ML experiments ใช้ `SimpleImputer(strategy="constant", fill_value=-1)` เพื่อให้ tree models รับ input ได้ แต่ต้องตีความ `-1` เป็น “ไม่มี field” ไม่ใช่ค่าทาง protocol จริง

### 3.4 Stream dependency

`tcp.stream` เป็น identity ภายใน capture หรือ connection context:

- packet ใน stream เดียวกันมี dependency สูง
- random row split อาจทำให้ packet ที่อยู่ติดกันรั่วข้าม train/validation
- validation ที่ถูกต้องกว่าคือ split ตาม capture หรือ session
- ห้ามตีความ stream number เป็น global identity ข้ามไฟล์

## 4. Data Pipeline

```text
CSV input
   |
   v
Schema check + dtype inspection
   |
   v
Normal profile / feature statistics
   |
   +--> protocol rules
   |
   +--> frequency and novelty features
   |
   +--> optional ML audit models
   |
   v
Context gate + hard-negative exclusion
   |
   v
Binary attack decision + validation report
```

### Step 1: Load data

```python
train = pd.read_csv(TRAIN, low_memory=False)
test = pd.read_csv(TEST, low_memory=False)
```

เก็บ `Id` แยกจาก feature matrix และรักษา row order เดิมตลอด pipeline

### Step 2: Build Normal profile

แกนหลักใช้ set membership:

```python
normal_windows = set(train["tcp.window_size"].dropna().unique())
normal_frame_windows = pd.MultiIndex.from_frame(
    train[["frame.len", "tcp.window_size"]]
)
```

profile นี้ไม่ใช่ probability distribution เต็มรูปแบบ แต่เป็น support set ที่ตอบคำถามว่า:

```text
ค่าหรือ pair นี้เคยเกิดใน Normal train หรือไม่?
```

### Step 3: Preserve protocol semantics

อย่า encode field เป็นตัวเลขโดยลืมความหมาย:

- `mqtt.msgtype=1` คือ CONNECT ไม่ใช่เลข category ธรรมดา
- `mqtt.msgtype=3` คือ PUBLISH ซึ่งมี payload diversity สูง
- `tcp.flags.syn=1` และ `tcp.flags.ack=0` คือ state pattern
- `tcp.window_size` สะท้อน transport stack และ capture behavior

## 5. Core Model: Deterministic Rule Engine

### 5.1 สิ่งที่ “เทรน” จริง

คำว่า training ใน core system หมายถึงการสร้าง reference profile และเลือกกฎจาก Normal data กับ protocol knowledge:

- ไม่มี gradient descent
- ไม่มี neural network weights
- ไม่มี `.pkl` หรือ checkpoint ที่ต้องโหลด
- reproducibility มาจาก source code + input CSV + deterministic rules
- การเปลี่ยน train data อาจเปลี่ยน `normal_windows` และ normal shape set

ชื่อ source หลัก: `outputs/predict_final_model.py`

### 5.2 Rule 1: unseen TCP window

```python
attack_stack = ~test["tcp.window_size"].isin(normal_windows)
```

เหตุผล:

- attack capture บาง family ใช้ TCP stack หรือ window values ที่ไม่ปรากฏใน Normal
- rule นี้มี recall สูง แต่ไม่ควรใช้เดี่ยวๆ
- อุปกรณ์ใหม่หรือ operating system ใหม่อาจทำให้เกิด unseen window แบบ benign

### 5.3 Rule 2: unseen frame/window pair

```python
attack_packet_shape = (
    ~test_frame_windows.isin(normal_frame_windows)
    & test["mqtt.msgtype"].ne(3)
)
```

การใช้ pair ดีกว่าใช้ field เดี่ยว เพราะ packet shape เป็น interaction ระหว่าง frame length และ TCP window

ตัด PUBLISH ออกจาก generic novelty rule เพราะ PUBLISH payload มีความหลากหลายสูงและสร้าง rare-normal false positives ได้ง่าย

### 5.4 Rule 3: SYN flood signature

```python
syn_flood = (
    test["frame.len"].eq(54)
    & test["tcp.window_size"].eq(512)
    & test["tcp.flags.syn"].eq(1)
    & test["tcp.flags.ack"].eq(0)
)
```

หลาย field ต้องตรงพร้อมกัน จึง precision สูงกว่า rule ที่ใช้เพียง `SYN=1`

### 5.5 Rule 4: Dictionary CONNECT

```python
dictionary_connect = (
    test["mqtt.msgtype"].eq(1)
    & test["mqtt.kalive"].isin([60, 3600])
)
```

`mqtt.msgtype=1` ต้องตีความร่วมกับ keep-alive และ session context ไม่ใช่ label ทุก CONNECT packet

### 5.6 Rule 5: Invalid subscription

```python
invalid_subscription = test["mqtt.msgtype"].isin([8, 9])
```

ใช้ message type เพื่อจับ subscription family แต่ควรตรวจความถี่และ stream context เพิ่มในระบบ production

### 5.7 Rule 6: Publish signature

```python
publish_attack = (
    test["mqtt.msgtype"].eq(3)
    & test["mqtt.len"].isin([19, 44])
)
```

PUBLISH ต้องวิเคราะห์ payload length, stream, TCP window และ transaction state ร่วมกัน เพราะ PUBLISH ปกติมีรูปแบบหลากหลาย

### 5.8 Rule union

```python
labels = (
    attack_stack
    | attack_packet_shape
    | syn_flood
    | dictionary_connect
    | invalid_subscription
    | publish_attack
)
```

OR union เพิ่ม recall แต่เปิดช่อง false positive จึงต้องมี correction layer

## 6. Context และ Hard Negatives

### 6.1 Context gate

PUBLISH family ที่มี `mqtt.msgtype=3` และ `tcp.window_size=256` ถูกพิจารณาเป็น family-level context ไม่ใช่ single-row anomaly:

```python
labels |= (
    test["mqtt.msgtype"].eq(3)
    & test["tcp.window_size"].eq(256)
)
```

หลักการ:

- เพิ่มเฉพาะ homogeneous family
- ใช้ stream support และ source evidence ประกอบ
- ไม่ย้ายกฎจาก stream หนึ่งไปทุก stream แบบอัตโนมัติ

### 6.2 PINGRESP hard negative

```python
pingresp_false_positive = (
    test["frame.len"].eq(56)
    & test["tcp.window_size"].eq(253)
    & test["mqtt.msgtype"].eq(13)
)
labels &= ~pingresp_false_positive
```

นี่คือ precedence ที่สำคัญ:

```text
positive rule union
    -> exclusion rule
    -> final label
```

เหตุผลคือ pseudo-model เคยให้ score สูงกับ PINGRESP family แต่หลักฐานเชิงทดลองชี้ว่าเป็น Normal family

### 6.3 Structural context

สำหรับ flow หรือ attack family ให้ตรวจ:

- stream มี packet template ครบหรือไม่
- packet อยู่ตำแหน่งใดใน sequence
- มี packet ขาดหรือเกินจาก family หรือไม่
- window/flags/state transition สอดคล้องกันหรือไม่
- candidate ชน Normal corpus หรือไม่

Structural completion มักปลอดภัยกว่า broad novelty เพราะใช้ relation ระหว่าง packet ไม่ใช่ความแปลกของ packet เดี่ยว

## 7. Feature Engineering สำหรับ Candidate Analysis

core detector ใช้ raw protocol rules แต่ candidate analysis เพิ่ม frequency features เพื่อจัดอันดับ residual rows

### 7.1 Frequency features

จาก `work/analyze_candidates.py`:

- `packet_train_count`
- `packet_test_count`
- `tcp_train_count`
- `tcp_test_count`
- `mqtt_train_count`
- `mqtt_test_count`
- `stream_packet_train_count`
- `stream_packet_test_count`

สร้างด้วย hash ของ column combinations:

```python
train_hash = pd.util.hash_pandas_object(train[columns], index=False)
test_hash = pd.util.hash_pandas_object(test[columns], index=False)
train_counts = train_hash.value_counts()
test_counts = test_hash.value_counts()
test["packet_train_count"] = (
    test_hash.map(train_counts).fillna(0).astype("int32")
)
```

### 7.2 Excess score

heuristic residual score ใช้ความแตกต่างระหว่าง train frequency และ test frequency:

```python
test[f"{prefix}_excess"] = (
    1 - normal_ratio * train_count / test_count
).clip(0, 1)
```

ใน experiment นี้ `normal_ratio = 0.07138` เป็น prior สำหรับ normal fraction ไม่ใช่ probability ที่ calibrate จาก attack labels

### 7.3 Candidate ranking score

```python
candidate_score = (
    0.45 * packet_excess
    + 0.25 * tcp_excess
    + 0.20 * stream_packet_excess
    + 0.10 * rtt_novel
)
```

น้ำหนักเป็น heuristic ranking ไม่ใช่ trained classifier และไม่ควรนำไปอ้างเป็น calibrated attack probability

## 8. Experimental ML Models

ML models ถูกใช้เป็น audit tools และ residual ranking models ไม่ใช่แกนหลักของ final detector

### 8.1 Pseudo-label ensemble

สร้าง pseudo attack reference จาก rows ที่ rule/control pipeline ติด label แล้วรวมกับ Normal train:

```text
Normal train + pseudo-positive rows
                 |
                 v
          imputer / numeric encoding
                 |
       ExtraTrees + RandomForest + HistGradientBoosting
                 |
          mean predict_proba ensemble
```

Hyperparameters จาก `work/train_pseudo_model.py`:

| Model | Configuration |
|---|---|
| ExtraTrees | `n_estimators=500`, `min_samples_leaf=2`, `max_features=0.9`, `class_weight="balanced"` |
| RandomForest | `n_estimators=350`, `min_samples_leaf=2`, `max_features=0.8`, `class_weight="balanced_subsample"` |
| HistGradientBoosting | `learning_rate=0.06`, `max_iter=350`, `max_leaf_nodes=31`, `l2_regularization=2.0`, `class_weight="balanced"` |

ทุก model ใช้ `random_state=20260717` และ `n_jobs=-1` เมื่อรองรับ

### 8.2 External-reference ensemble

`work/train_external_model.py` normalize external PCAP CSV fields ให้เข้ากับ competition schema แล้ว train ensemble แบบเดียวกันบน:

```text
competition Normal rows + external attack reference rows
```

ข้อควรระวัง:

- external capture อาจใช้ TCP stack คนละแบบ
- model อาจเรียนรู้ source/capture environment แทน attack semantics
- field normalization อาจทำให้ missing pattern ต่างกัน
- external model จึงเป็น supporting evidence ไม่ใช่ label oracle

### 8.3 IsolationForest

ใช้เป็น one-class anomaly baseline:

| Parameter | Value |
|---|---:|
| `n_estimators` | 350 |
| `max_samples` | 4096 |
| `contamination` | `"auto"` |
| `random_state` | 20260719 |

IsolationForest จับ geometric outlier แต่ไม่รู้ MQTT semantics และไม่รู้ stream family จึงต้องตรวจ hard negatives เสมอ

### 8.4 ทำไม ML ไม่ใช่ final decision

1. pseudo positives มาจาก rule engine จึงเกิด circularity
2. attack class coverage ไม่สมบูรณ์
3. rare-normal ได้ probability สูง
4. external data มี domain shift
5. probability สูงไม่ได้พิสูจน์ causal attack context

การใช้ ML ที่ถูกต้องใน setup นี้คือ:

```text
ML score = candidate ranking / audit signal
protocol + context + falsification = decision
```

## 9. Training, Tuning และ Validation

### 9.1 Training stage ของ core engine

```python
normal_windows = set(train["tcp.window_size"].dropna().unique())
normal_frame_windows = pd.MultiIndex.from_frame(
    train[["frame.len", "tcp.window_size"]]
)
```

หลังสร้าง profile ให้ตรวจ self-consistency:

```python
train_labels = attack_mask(train, train)
if int(train_labels.sum()) != 0:
    raise RuntimeError("Rules flagged normal training rows")
```

นี่คือ guardrail ไม่ใช่ performance proof เพราะ train ไม่มี attack labels และ rule อาจ under-detect attack ได้

### 9.2 Tuning axis

การปรับระบบควรแยกเป็น axis:

| Axis | ตัวอย่างการปรับ | ความเสี่ยง |
|---|---|---|
| Rule strictness | เพิ่ม/ลด field ใน signature | precision-recall trade-off |
| Normal profile | packet shape, window, RTT set | device/capture shift |
| Context width | packet, stream, transaction | leakage หรือ overgeneralization |
| Candidate size | single row, family, broad batch | false-positive accumulation |
| ML threshold | probability cutoff | pseudo-label bias |
| Imputation | sentinel `-1`, median, model-based | missing semantics distortion |

### 9.3 Validation layers

**Layer 1 — schema validation**

- rows and columns ถูกต้อง
- Id unique และ order ตรง input
- labels non-null และ binary

**Layer 2 — train self-check**

- core rules ไม่ flag Normal train
- exclusion rules ไม่ลบข้อมูลที่ต้องการใน known attack signatures

**Layer 3 — group validation**

- split ตาม capture/session
- ไม่สุ่ม packet ที่อยู่ใน stream เดียวกันข้าม fold
- รายงาน mean, standard deviation และ worst fold

**Layer 4 — hard-negative validation**

- known PINGRESP family
- normal PUBLISH family
- common TCP handshake/control packet

**Layer 5 — source evidence**

- exact match
- packet shape match
- stream-aware match
- RTT/full-feature match

ไม่ควรสรุปว่า candidate เป็น attack จาก Layer 5 เพียงระดับเดียว

## 10. Error Analysis

### False positive patterns

- rare PINGRESP
- normal PUBLISH ที่ payload ยาวหรือ window ใหม่
- TCP window shift จาก device stack
- external capture shape ที่ไม่ตรง competition domain
- packet shape ที่ attack-like แต่ไม่มี stream context

### False negative patterns

- attack ที่ใช้ packet format เหมือน Normal
- attack ที่เห็นจาก sequence/frequency มากกว่า field value
- MQTT transaction ที่ต้องดูหลาย packet ต่อเนื่อง
- flow burst ที่ raw packet ไม่ต่างจาก Normal

### Debug table

| Symptom | Likely cause | Fix |
|---|---|---|
| positives เยอะผิดปกติ | novelty rule กว้าง | เพิ่ม pair/context gate |
| PINGRESP ติด attack | model confidence แทน semantics | hard-negative exclusion |
| SYN family ขาดบาง row | packet-level rule ไม่มอง stream | structural completion |
| external model score สูงทุกแถว | domain shift | source normalization + grouped validation |
| train self-check fail | rule โดน Normal | ตรวจ missing, profile และ signature |

## 11. Reproducible Research Structure

โครงสร้างที่ควรแชร์กับทีม:

```text
data/
  X_train.csv
  X_test.csv

outputs/
  predict_final_model.py

work/
  submit_improved.py
  analyze_candidates.py
  train_pseudo_model.py
  train_external_model.py
  deep_audit.py

docs/
  SuperAI6_IoT_Attack_Detection_Technical_DeepDive_TH.md
```

หลัก reproducibility:

- pin Python/dependency versions
- fix random seeds ใน ML experiments
- preserve raw data schema
- log feature list and transformations
- log rule version
- log positive count and validation results
- checksum code and input artifacts

ตัวอย่าง environment:

```text
Python 3.10+
pandas
numpy
scikit-learn  # เฉพาะ experimental ML audit models
```

## 12. Limitations

ระบบนี้มีข้อจำกัดที่ต้องบอกผู้ฟังตรงๆ:

1. train ไม่มี attack labels จึงวัด true recall ของ attack class จาก local data ไม่ได้เต็มรูปแบบ
2. rules มี interpretability สูง แต่ coverage ของ attack family จำกัด
3. `tcp.window_size` และ packet lengths อาจเรียนรู้ environment มากกว่า behavior
4. stream-based analysis ผูกกับ capture structure
5. pseudo-label models มี circularity
6. external PCAP มี domain shift
7. random row split ทำให้ validation optimistic ได้
8. rule union เพิ่ม recall แต่มี false-positive accumulation

## 13. Improvements สำหรับระบบ production

### 13.1 Flow-level model

เปลี่ยนหน่วยจาก packet เป็น flow/session:

- packet count / byte count ต่อช่วงเวลา
- direction ratio
- inter-arrival time distribution
- burstiness
- SYN/ACK/RESET transition
- connection duration
- MQTT message sequence

### 13.2 Transaction-level MQTT features

สร้าง event sequence:

```text
CONNECT -> CONNACK -> PUBLISH
CONNECT -> CONNACK -> SUBSCRIBE -> SUBACK
PINGREQ -> PINGRESP
```

features ที่ควรเพิ่ม:

- valid/invalid transition
- response latency
- repeated CONNECT count
- publish-before-connect
- unusual keep-alive transition
- topic/payload change rate

### 13.3 Group-held-out learning

แบ่ง validation ตาม capture/session และฝึก model บน flow aggregates เพื่อป้องกัน leakage จาก packet ที่อยู่ใน connection เดียวกัน

### 13.4 Hybrid architecture

```text
Protocol rules      -> high-precision anchors
Flow model          -> context and recall
Sequence model      -> transaction semantics
Hard-negative bank  -> precision guardrail
```

ไม่ควรแทนที่ rule engine ทั้งหมดด้วย black-box model เพราะ protocol rules มีประโยชน์ในการอธิบาย incident และตรวจ drift

## 14. Key Takeaways

1. Normal-only ไม่ได้แปลว่าต้องใช้ anomaly score เดี่ยว
2. Protocol semantics ช่วยสร้าง precision anchors ที่อธิบายได้
3. Packet novelty ต้องถูกจำกัดด้วย stream/transaction context
4. Hard negatives สำคัญพอๆ กับ attack examples
5. ML ensemble เหมาะกับ ranking/audit เมื่อ labels ไม่สมบูรณ์
6. Core detector ของงานนี้คือ deterministic normal-profile rule engine
7. Validation ต้องตรวจทั้ง schema, self-consistency, group leakage และ domain shift

## 15. Source Files and References

### Repository sources

- [`outputs/predict_final_model.py`](../outputs/predict_final_model.py) — core deterministic rules
- [`work/submit_improved.py`](../work/submit_improved.py) — train self-check and rule baseline
- [`work/analyze_candidates.py`](../work/analyze_candidates.py) — frequency features and residual ranking
- [`work/train_pseudo_model.py`](../work/train_pseudo_model.py) — pseudo-label tree ensemble
- [`work/train_external_model.py`](../work/train_external_model.py) — external-reference ensemble
- [`work/deep_audit.py`](../work/deep_audit.py) — ExtraTrees, IsolationForest and source support audit
- [`docs/SuperAI6_IoT_Attack_Detection_Report_TH.md`](./SuperAI6_IoT_Attack_Detection_Report_TH.md) — project report and evidence history

### External references

- [Kaggle — SuperAI6 IoT Attack Detection](https://www.kaggle.com/competitions/superai6-iot-attack-detection)
- [OASIS — MQTT Version 3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
- [Wireshark — MQTT Display Filter Reference](https://www.wireshark.org/docs/dfref/m/mqtt.html)

## 16. Presentation Summary

ข้อความสรุปสำหรับพูด 60–90 วินาที:

> ระบบนี้แก้โจทย์ Normal-only ด้วยการสร้าง normal profile จาก TCP/MQTT traffic แล้วใช้ protocol rules ที่อธิบายได้ เช่น unseen TCP window, SYN signature, CONNECT, subscription และ PUBLISH signatures. จากนั้นเพิ่ม stream context และ hard-negative exclusions เพื่อไม่ให้ rare-normal ถูกติด label เป็น attack. เราทดลอง tree ensembles และ IsolationForest เป็น audit tools แต่ไม่ใช้ probability เป็นคำตัดสินหลัก เพราะ pseudo labels และ external captures มี domain shift. ผลลัพธ์คือ detector ที่ reproducible, inspectable และต่อยอดไปสู่ flow/transaction-level detection ได้.
