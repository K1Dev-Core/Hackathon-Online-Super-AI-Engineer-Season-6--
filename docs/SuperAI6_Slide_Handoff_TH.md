# SuperAI6 IoT Attack Detection — Slide Handoff

เอกสารนี้เป็น source brief สำหรับให้ AI ตัวอื่นสร้าง presentation ภาษาไทยจากข้อมูลจริงใน repository

## 0. Metadata

- ชื่อโครงการ: **IoT Attack Detection ด้วย Protocol Semantics และ Stream Context**
- การแข่งขัน: [SuperAI6 IoT Attack Detection](https://www.kaggle.com/competitions/superai6-iot-attack-detection)
- ผู้จัดทำ: `610686-วชิรวิทย์`
- Workspace: `/Users/k1god/Documents/Codex/2026-07-17/https-www-kaggle-com-competitions-superai6`
- วันที่ใน presentation: `18 กรกฎาคม 2569`
- จำนวนสไลด์: `12`
- ภาษา: ไทยเป็นหลัก, คงคำเทคนิคภาษาอังกฤษ เช่น `Normal-only`, `MQTT`, `TCP`, `stream`, `hard negative`, `F1`

## 1. เป้าหมายของ deck

อธิบาย detector ที่สร้างจากข้อมูล train ซึ่งเป็น Normal ทั้งหมด โดยใช้:

1. Protocol rules เป็น precision anchors
2. TCP/MQTT stream context เพื่อเพิ่ม recall แบบแคบ
3. Hard-negative และ controlled submission เพื่อหักล้างสมมติฐาน
4. Reproducible artifact ที่ตรวจ schema, changed Ids และ SHA-256 ได้

Deck ต้องตอบให้ได้ว่า:

- ทำไม anomaly score อย่างเดียวไม่พอ
- โค้ดจริงตัดสิน Attack อย่างไร
- ทำไมบาง candidate ถูกเพิ่ม และบาง candidate ถูก reject
- ไฟล์ที่เลือกส่งคือไฟล์ไหน
- คะแนนไหนเป็น Kaggle score และคะแนนไหนเป็น offline estimate

## 2. ไฟล์ที่เลือกสำหรับ upload

ไฟล์ที่ผู้ใช้เลือกสำหรับ upload:

```text
outputs/offline_benchmark_candidates/submission_offline_02_hedge_payload132.csv
```

ข้อมูลไฟล์:

| รายการ | ค่า |
|---|---:|
| Rows | 10,000 |
| Columns | `Id,label` |
| Positive labels | 2,811 |
| User-reported Private F1 | 0.97198 |
| User-reported Public F1 | 0.96267 |
| Description | baseline + structural row + payload132 hedge, `Id=1145` |

ข้อควรระวัง:

- ตัวเลข `0.97198` คือ **Private F1**
- ตัวเลข `0.96267` คือ **Public F1**
- ไฟล์นี้คือไฟล์ที่ผู้ใช้เลือกสำหรับ upload รอบนี้
- ห้ามเรียกไฟล์นี้ว่าอันดับหนึ่งโดยไม่มี leaderboard evidence เพิ่ม
- ห้ามใช้ offline mean F1 แทน Kaggle score

## 3. Comparison files

ใช้เป็น context เท่านั้น ไม่ใช่ไฟล์ selected ในรอบนี้:

| File | Public F1 | Private F1 | บทบาท |
|---|---:|---:|---|
| `submission_offline_02_hedge_payload132.csv` | 0.96267 | 0.97198 | selected upload file |
| `submission_v27_stream3_5_payload.csv` | 0.96824 | 0.97748 | historical comparison, ไม่ใช่ selected file รอบนี้ |
| `submission_v30_stream_fraction_085.csv` | 0.96551 | 0.97586 | rejected probe |
| `submission_v31_stream_fraction_080.csv` | 0.96416 | 0.97393 | rejected probe |
| `submission_v25_stream2_plus_stream4_payload.csv` | 0.96749 | 0.97611 | earlier comparison |

เขียนคำอธิบายแบบนี้:

> offline_02 คือไฟล์ที่เลือกสำหรับ upload ตามคำสั่งล่าสุด ส่วน v27 ใช้เป็น historical comparison ที่มี score สูงกว่าในประวัติที่มีอยู่ ไม่ควรปนคำว่า selected กับ best historical score.

## 4. Design direction

### ภาพรวม

- โทน: warm ivory canvas + deep slate text + muted teal + terracotta จุดเน้น
- พื้นหลัง: ivory อุ่น ไม่ขาวจ้า
- ตัวอักษร: deep slate ไม่ใช้ดำสนิทบนพื้นขาว
- Accent หลัก: muted teal สำหรับ flow, evidence, links
- Accent รอง: terracotta สำหรับ warning, reject, score highlight
- ใช้สีไม่เกิน 4 สีหลัก
- ไม่ใช้ gradient จัด, glow, 3D, icon จำนวนมาก หรือ card ซ้อนหลายชั้น
- ใช้ whitespace, เส้นบาง, ตารางเรียบ และ code block สีเข้ม

### Typography

- หัวข้อสั้น หนึ่งประเด็นต่อสไลด์
- Body ไม่เกิน 3–5 bullet ต่อกล่อง
- Code ใช้ monospace
- คงคำ field name ตาม source code เช่น `tcp.window_size`, `mqtt.msgtype`
- ห้ามเปลี่ยนชื่อไฟล์, ค่า score, Id หรือ feature name

### Layout

- 16:9
- หนึ่ง title + หนึ่ง message หลักต่อหน้า
- สไลด์ code ใช้ code block ใหญ่ด้านขวาหรือกลาง
- สไลด์ผลใช้ตารางหรือ bar chart ไม่ใช้ dashboard หลายกราฟ
- Footer ทุกหน้าที่มีข้อมูลต้องมี source สั้นๆ
- ใส่ speaker note ให้ทุกสไลด์

## 5. Storyline 12 slides

---

## Slide 01 — เปิดเรื่อง

**Title**

```text
ตรวจจับ Attack จากความหมายของ Protocol
```

**Subtitle**

```text
Normal-only training → TCP/MQTT rules → stream context → falsification
```

**แสดงบนสไลด์**

- `Public F1 / selected file: 0.96267`
- `Private F1 / selected file: 0.97198`
- Filename: `submission_offline_02_hedge_payload132.csv`
- `610686-วชิรวิทย์`

**Visual**

- ตัวเลข score สองกล่อง
- ไม่มีภาพ network stock photo
- ใช้เส้น flow เล็กๆ หรือ protocol labels แทนภาพรก

**Speaker note**

> Train เป็น Normal-only จึงใช้ supervised binary classifier แบบปกติไม่ได้โดยตรง. แนวทางนี้ใช้ protocol semantics เป็น anchor, ใช้ context เพิ่ม recall และใช้ falsification ตัด candidate ที่หลักฐานไม่พอ.

**Source**

- Kaggle competition URL
- selected CSV path

---

## Slide 02 — โจทย์จริง

**Title**

```text
โจทย์ไม่ได้ถามว่า packet แปลกไหม
```

**Message**

```text
โจทย์ถามว่า packet นี้เป็น Attack หรือเป็น Normal ที่พบไม่บ่อย
```

**Facts**

| Item | Value |
|---|---:|
| Train | 100,000 rows, Normal-only |
| Test | 10,000 rows, mixed Normal + Attack |
| Feature groups | Frame / TCP / MQTT |
| Metric | F1 |

**แสดงเพิ่ม**

- Rare-normal ทำให้ broad novelty มี false positive
- F1 สูงต้องเพิ่ม positive เฉพาะกลุ่มที่ precision สูง
- Output format: `Id,label`

**Speaker note**

> จุดยากคือไม่มี attack label ใน train. หากติด label ทุกค่าที่ไม่เคยเห็น จะจับ rare-normal ปน attack. จึงต้องใช้ความหมายของ protocol และ evidence จากหลายระดับ.

**Source**

- [Kaggle competition](https://www.kaggle.com/competitions/superai6-iot-attack-detection)
- `docs/SuperAI6_IoT_Attack_Detection_Report_TH.md`

---

## Slide 03 — อ่านข้อมูลตามชั้น network

**Title**

```text
อ่านข้อมูลตามชั้นของ network
```

**สามคอลัมน์**

| Layer | Fields | ใช้ทำอะไร |
|---|---|---|
| Frame | `frame.len` | ตรวจ packet shape |
| TCP | `tcp.flags`, `tcp.window_size`, `tcp.stream` | ตรวจ transport state และ flow context |
| MQTT | `mqtt.msgtype`, `mqtt.kalive`, `mqtt.len` | อ่าน protocol meaning |

**Protocol examples**

- `mqtt.msgtype=1`: CONNECT
- `mqtt.msgtype=3`: PUBLISH
- `mqtt.msgtype=8/9`: subscription-related messages
- `mqtt.msgtype=13`: PINGRESP, ใช้เป็น hard-negative example

**ข้อความเน้น**

```text
หายาก ≠ โจมตี
packet shape ≠ context
```

**Speaker note**

> MQTT field ที่หายอาจหมายถึง packet ไม่มี MQTT layer เช่น TCP control packet ไม่ควรเติมค่าหรือเหมารวมว่าเป็น malformed. `tcp.stream` ใช้เป็นบริบทภายใน capture ไม่ใช่ global identity ข้ามไฟล์.

**Source**

- [OASIS MQTT 3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
- [Wireshark MQTT field reference](https://www.wireshark.org/docs/dfref/m/mqtt.html)

---

## Slide 04 — Pipeline

**Title**

```text
จาก Normal profile สู่ไฟล์ส่ง
```

**Flow 4 ขั้น**

1. **Profile** — สร้าง reference set จากค่าที่พบใน Normal train
2. **Rules** — สร้าง attack mask จาก TCP/MQTT signatures
3. **Context** — ตรวจ stream family, hard negatives, changed Ids
4. **Output** — ตรวจ 10,000 rows, Id order, binary labels, checksum

**Key message**

```text
ทุก candidate เป็น delta จาก immutable baseline.
ถ้า score สวน hypothesis ให้ reject.
```

**Visual**

- ใช้ 4 กล่องเรียงซ้ายไปขวา
- ลูกศรสี teal
- คำว่า reject ใช้ terracotta

**Speaker note**

> Submission quota ใช้เป็น controlled experiment ไม่ใช่ brute-force. ทุก candidate ต้องรู้ว่าเปลี่ยน Id ไหน และเปลี่ยนเพราะ hypothesis อะไร.

**Source**

- `outputs/predict_final_model.py`
- `outputs/build_post_v27_stream_threshold_suite.py`

---

## Slide 05 — Code จริง: rule engine

**Title**

```text
โค้ดจริง 01: สร้าง rule mask
```

**ข้อความกำกับ**

```text
คัดจาก outputs/predict_final_model.py
ไม่ใช่ pseudocode
```

**Code block: แสดงตามนี้**

```python
def attack_mask(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    normal_windows = set(train["tcp.window_size"].dropna().unique())
    normal_frame_windows = pd.MultiIndex.from_frame(
        train[["frame.len", "tcp.window_size"]]
    )
    test_frame_windows = pd.MultiIndex.from_frame(
        test[["frame.len", "tcp.window_size"]]
    )

    attack_stack = ~test["tcp.window_size"].isin(normal_windows)
    attack_packet_shape = (
        ~test_frame_windows.isin(normal_frame_windows)
        & test["mqtt.msgtype"].ne(3)
    )
    syn_flood = (
        test["frame.len"].eq(54)
        & test["tcp.window_size"].eq(512)
        & test["tcp.flags.syn"].eq(1)
        & test["tcp.flags.ack"].eq(0)
    )
```

**ด้านข้าง code**

- Normal profile มาจาก `X_train`
- ตัด PUBLISH ออกจาก generic packet-shape novelty
- SYN flood ใช้ signature หลาย field ไม่ใช่ field เดียว

**Speaker note**

> แสดงว่ากฎเริ่มจากค่าที่พบใน Normal train แล้วเพิ่ม signatures ที่มีความหมายเชิง protocol. การใช้หลาย field ช่วยลด false positive จากค่าหายากเพียงตัวเดียว.

**Source**

- `outputs/predict_final_model.py`

---

## Slide 06 — Code จริง: context และ hard negative

**Title**

```text
โค้ดจริง 02: เพิ่ม context แล้วลบ false positive
```

**Code block: แสดงตามนี้**

```python
def build_submission(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    labels = attack_mask(train, test)

    # Public-score probes established this whole PUBLISH capture family as attack.
    labels |= test["mqtt.msgtype"].eq(3) & test["tcp.window_size"].eq(256)

    pingresp_false_positive = (
        test["frame.len"].eq(56)
        & test["tcp.window_size"].eq(253)
        & test["mqtt.msgtype"].eq(13)
    )
    labels &= ~pingresp_false_positive

    submission = test[["Id"]].copy()
    submission["label"] = labels.astype("int8")
    return submission
```

**Callout 1**

```text
PUBLISH window 256 → เพิ่มกลับเฉพาะ family ที่มีหลักฐาน
```

**Callout 2**

```text
PINGRESP / frame 56 / window 253 → hard negative, ตัดออก
```

**Speaker note**

> Confidence สูงไม่พอ. PINGRESP family เคยถูก pseudo-model ให้ probability สูง แต่ controlled probe ทำให้ score แย่ จึงต้องมี exclusion rule ที่ override candidate.

**Source**

- `outputs/predict_final_model.py`
- `outputs/post_v27_threshold_report.md`

---

## Slide 07 — Case studies

**Title**

```text
เพิ่มหรือ reject เพราะอะไร
```

**Table**

| Candidate | Evidence | Decision | Reason |
|---|---|---|---|
| `Id=9816` | SYN-flood stream ขาด packet เดียว | **ADD** | structural completion; family ครบเมื่อเติมแถวนี้ |
| `Id=1145` | residual payload twin, 132-byte hedge | **ADD** | context สอดคล้องกับ attack family; ใช้ใน offline_02 |
| `Id=8150` | packet-shape match จาก PCAP | **REJECT** | ส่ง probe แล้ว Public ลด; shape เดี่ยวไม่พอ |
| `v30/v31` | เพิ่ม CONNECT จาก stream fraction | **REJECT** | Public/Private ต่ำกว่า v27; เก็บเป็น negative evidence |

**ข้อความใหญ่**

```text
Evidence pipeline ต้องหักล้างสมมติฐานได้.
```

**Speaker note**

> Id=9816 แสดง structural completion. Id=1145 คือ payload hedge ที่ถูกนำไปอยู่ในไฟล์ selected. Id=8150 แสดงว่า packet-shape support อย่างเดียวไม่พอ. v30/v31 แสดงโทษของการเติม CONNECT กว้างเกินไป.

**Source**

- `docs/SuperAI6_IoT_Attack_Detection_Report_TH.md`
- `outputs/offline_benchmark_report.md`
- `outputs/post_v27_threshold_report.md`

---

## Slide 08 — Scores ที่รายงานจริง

**Title**

```text
แยก Public, Private และ offline estimate
```

**Main table**

| File | Public F1 | Private F1 | Status |
|---|---:|---:|---|
| `offline_02` | **0.96267** | **0.97198** | selected upload file |
| `v27` | 0.96824 | 0.97748 | historical comparison |
| `v30` | 0.96551 | 0.97586 | rejected |
| `v31` | 0.96416 | 0.97393 | rejected |

**หมายเหตุที่ต้องใส่ใต้ตาราง**

```text
สีส้ม = ไฟล์ที่เลือก upload ไม่ได้แปลว่าเป็น historical maximum.
```

**Offline benchmark note**

- `offline_02` offline mean F1: `0.96716792`
- offline public-delta proxy: `0.96197793`
- ค่าเหล่านี้เป็น decision heuristic ไม่ใช่ Kaggle ground truth
- benchmark report ระบุว่า `offline_01_scoremax_structural.csv` ชนะ offline simulation แต่ user เลือก `offline_02` สำหรับ upload

**Speaker note**

> อย่าสลับลำดับ Public กับ Private. selected file ใช้คะแนนจาก submission ที่ผู้ใช้รายงาน. offline mean ใช้ตัดสินใจภายในเท่านั้น ไม่ใช่คะแนน Kaggle.

**Source**

- `outputs/offline_benchmark_report.md`
- `outputs/offline_benchmark_results.csv`
- User-reported Kaggle submission history

---

## Slide 09 — Reproducibility

**Title**

```text
ไฟล์ดีต้องสร้างซ้ำและตรวจได้
```

**Four gates**

| Gate | Check |
|---|---|
| Schema | columns exactly `Id,label` |
| Shape | 10,000 rows, unique Id, Id order ตรง test |
| Labels | non-null, binary `{0,1}` |
| Artifact | changed Ids, positive count, SHA-256 |

**Reproduce baseline command**

```bash
python outputs/predict_final_model.py \
  --train data/X_train.csv \
  --test data/X_test.csv \
  --output outputs/submission_reproduced.csv
```

**Selected artifact command/check**

```bash
python - <<'PY'
import csv
from pathlib import Path

path = Path("outputs/offline_benchmark_candidates/") / \
    "submission_offline_02_hedge_payload132.csv"
with path.open(newline="") as f:
    rows = list(csv.DictReader(f))
assert list(rows[0]) == ["Id", "label"]
assert len(rows) == 10_000
assert all(row["label"] in {"0", "1"} for row in rows)
print(len(rows), sum(row["label"] == "1" for row in rows))
PY
```

**Speaker note**

> Baseline command สร้าง rule submission. Selected artifact เป็น candidate delta ที่ต้องเก็บแยกจาก baseline. ตรวจ schema และ checksum ก่อน upload ทุกครั้ง.

**Source**

- `outputs/predict_final_model.py`
- `outputs/build_post_v27_stream_threshold_suite.py`
- `docs/artifact_checksums.sha256`

---

## Slide 10 — ข้อจำกัดและสิ่งที่ห้ามอ้าง

**Title**

```text
ผลลัพธ์นี้บอกอะไร และบอกอะไรไม่ได้
```

**บอกได้**

- offline_02 มี schema ถูกต้องและมี score ที่ผู้ใช้รายงานจริง
- context gate ดีกว่า broad novelty ในชุดการทดลองที่มี
- hard negative ลด false positive
- artifacts สร้างซ้ำและตรวจ checksum ได้

**ห้ามสรุปเกินหลักฐาน**

- ห้ามบอกว่า offline_02 อันดับหนึ่ง
- ห้ามบอกว่า offline score = Kaggle score
- ห้ามบอกว่า model ชนะทุกทีม
- ห้ามใช้ Public score เป็น Private score
- ห้ามเปลี่ยนคำว่า selected upload file เป็น best historical file

**Key sentence**

```text
offline_02 คือไฟล์ที่เลือก upload รอบนี้ ไม่ใช่คำรับประกันอันดับ.
```

**Speaker note**

> ความน่าเชื่อถือของ presentation อยู่ที่การบอกขอบเขตของหลักฐาน. v27 มี historical score สูงกว่า แต่ไม่ใช่ไฟล์ที่ selected ในรอบนี้.

---

## Slide 11 — References และ artifacts

**Title**

```text
อ้างอิงและไฟล์ที่ตรวจสอบได้
```

### External references

1. [Kaggle — SuperAI6 IoT Attack Detection](https://www.kaggle.com/competitions/superai6-iot-attack-detection)
2. [OASIS — MQTT Version 3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
3. [Wireshark — MQTT Display Filter Reference](https://www.wireshark.org/docs/dfref/m/mqtt.html)

### Repository references

1. [`outputs/predict_final_model.py`](../outputs/predict_final_model.py) — deterministic protocol detector
2. [`outputs/offline_benchmark_report.md`](../outputs/offline_benchmark_report.md) — offline simulation and guardrails
3. [`outputs/post_v27_threshold_report.md`](../outputs/post_v27_threshold_report.md) — v27/v30/v31 audit
4. [`outputs/offline_benchmark_candidates/submission_offline_02_hedge_payload132.csv`](../outputs/offline_benchmark_candidates/submission_offline_02_hedge_payload132.csv) — selected artifact
5. [`outputs/build_post_v27_stream_threshold_suite.py`](../outputs/build_post_v27_stream_threshold_suite.py) — validation and candidate builder
6. [`docs/artifact_checksums.sha256`](artifact_checksums.sha256) — SHA-256 manifest
7. [`SuperAI6-โจทย์-HackathonOnline.pdf`](/Users/k1god/Downloads/SuperAI6-โจทย์-HackathonOnline.pdf) — supplementary problem statement

**Speaker note**

> แยก source เป็น external specification, repository code, artifact และ observed score. ถ้าถูกถามที่มา ให้เปิดไฟล์ตามรายการนี้ ไม่ตอบจากความจำ.

---

## Slide 12 — สรุปและ Q&A

**Title**

```text
Protocol. Context. Falsification.
```

**Three takeaways**

1. Protocol meaning ให้ precision anchor
2. Stream/payload context ช่วยเพิ่ม recall แบบแคบ
3. Falsification สำคัญพอๆ กับการหา candidate ใหม่

**Selected file block**

```text
FILE: submission_offline_02_hedge_payload132.csv
PUBLIC F1: 0.96267
PRIVATE F1: 0.97198
ROWS: 10,000
POSITIVE LABELS: 2,811
```

**Closing sentence**

```text
เลือกจากหลักฐาน ไม่ใช่จากความแปลกของ packet เพียงอย่างเดียว.
```

**Speaker note**

> สรุปสามคำ: Protocol, Context, Falsification. ย้ำ selected filename และ score แล้วเปิด Q&A.

## 6. Full source snippets

ใช้ snippets ต่อไปนี้เมื่อ AI สร้างสไลด์ code. ห้ามแต่งชื่อ function หรือ field ใหม่.

### `outputs/predict_final_model.py` — rule mask

```python
def attack_mask(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    normal_windows = set(train["tcp.window_size"].dropna().unique())
    normal_frame_windows = pd.MultiIndex.from_frame(train[["frame.len", "tcp.window_size"]])
    test_frame_windows = pd.MultiIndex.from_frame(test[["frame.len", "tcp.window_size"]])

    attack_stack = ~test["tcp.window_size"].isin(normal_windows)
    attack_packet_shape = (
        ~test_frame_windows.isin(normal_frame_windows)
        & test["mqtt.msgtype"].ne(3)
    )
    syn_flood = (
        test["frame.len"].eq(54)
        & test["tcp.window_size"].eq(512)
        & test["tcp.flags.syn"].eq(1)
        & test["tcp.flags.ack"].eq(0)
    )
    dictionary_connect = (
        test["mqtt.msgtype"].eq(1)
        & test["mqtt.kalive"].isin([60, 3600])
    )
    invalid_subscription = test["mqtt.msgtype"].isin([8, 9])
    publish_attack = test["mqtt.msgtype"].eq(3) & test["mqtt.len"].isin([19, 44])

    return (
        attack_stack
        | attack_packet_shape
        | syn_flood
        | dictionary_connect
        | invalid_subscription
        | publish_attack
    )
```

### `outputs/predict_final_model.py` — context gate and output

```python
def build_submission(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    labels = attack_mask(train, test)

    # Public-score probes established this whole PUBLISH capture family as attack.
    labels |= test["mqtt.msgtype"].eq(3) & test["tcp.window_size"].eq(256)

    pingresp_false_positive = (
        test["frame.len"].eq(56)
        & test["tcp.window_size"].eq(253)
        & test["mqtt.msgtype"].eq(13)
    )
    labels &= ~pingresp_false_positive

    submission = test[["Id"]].copy()
    submission["label"] = labels.astype("int8")
    return submission
```

## 7. Accuracy checklist before rendering slides

ตรวจทุกข้อก่อนส่ง deck ให้ผู้ใช้:

- [ ] มี 12 slides เท่านั้น
- [ ] selected filename ตรง `submission_offline_02_hedge_payload132.csv`
- [ ] Public `0.96267`, Private `0.97198` ไม่สลับกัน
- [ ] ระบุว่า selected file ไม่ใช่คำรับประกันอันดับหนึ่ง
- [ ] v27 ถูกระบุเป็น historical comparison ไม่ใช่ selected file รอบนี้
- [ ] offline mean และ proxy มี label ว่า offline estimate
- [ ] code ตรงกับ `outputs/predict_final_model.py`
- [ ] references มี Kaggle, OASIS MQTT, Wireshark และ local artifacts
- [ ] ไม่มี stock image หรือภาพที่อ้างว่าเป็น packet จริงโดยไม่มี source
- [ ] speaker notes ครบทุกสไลด์
- [ ] code อ่านได้เมื่อฉายบนจอ ไม่ย่อจนอ่านไม่ได้

## 8. Expected output from slide-making AI

สร้างไฟล์ต่อไปนี้:

1. `presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pptx`
2. `presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pdf`
3. `presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.html`
4. speaker notes ฝังใน slide หรือไฟล์แยก

ทุก output ต้องใช้เนื้อหาจาก handoff นี้และตรวจ checksum หลัง render.
