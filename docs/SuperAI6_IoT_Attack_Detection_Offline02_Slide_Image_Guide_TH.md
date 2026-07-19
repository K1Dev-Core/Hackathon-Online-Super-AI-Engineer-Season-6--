# คู่มือเตรียมภาพประกอบสไลด์

## โปรเจกต์

เอกสารนี้ใช้เตรียมภาพสำหรับ presentation:

`submission_offline_02_hedge_payload132.csv`

ข้อมูลสำคัญที่ต้องใช้ให้ตรงกันทุกภาพและทุกสไลด์:

- Train มีข้อมูล Normal เท่านั้น
- Test มี 10,000 แถว
- ไฟล์ผลลัพธ์มี `Id,label`
- label=1 จำนวน 2,811 แถว
- Private F1: `0.97198`
- Public F1: `0.96267`
- เพิ่ม structural pattern ที่ `Id=9816`
- เพิ่ม payload hedge ที่ `Id=1145`

คะแนน Private/Public เป็นคะแนนที่ผู้ใช้รายงานจาก Kaggle ควรใส่ caption กำกับว่าเป็นผลจาก leaderboard ไม่ใช่คะแนนที่คำนวณจากไฟล์ CSV โดยตรง

## หลักการเลือกภาพ

ภาพต้องช่วยตอบคำถามของสไลด์ ไม่ใช่แค่ทำให้สไลด์เต็มขึ้น

- ใช้ภาพหลัก 1 ภาพต่อสไลด์
- Crop เฉพาะส่วนสำคัญ
- ขยายตัวหนังสือให้คนแถวหลังอ่านได้
- ซ่อนชื่อผู้ใช้, token, path ส่วนตัว และข้อมูลที่ไม่เกี่ยวข้อง
- ใช้สีของภาพไม่เกิน 2–3 สีหลัก เพื่อไม่ชนกับธีมดำ–เทา
- ถ้าเป็น code ให้แคปเฉพาะ function ที่กำลังอธิบาย
- ถ้าเป็นคะแนน ให้เห็นชื่อไฟล์และตัวเลขในภาพเดียวกัน
- ใส่ caption สั้น ๆ ใต้ภาพ เช่น `Train: Normal only` หรือ `Kaggle result reported by user`

---

## Slide 1: IOT ATTACK DETECTION THROUGH TCP + MQTT

### เป้าหมายการเล่า

เปิดเรื่องให้คนฟังรู้ทันทีว่าโปรเจกต์เกี่ยวกับอะไร ใช้ข้อมูลประเภทไหน และ presentation จะเล่าจากวิธีคิดจริง ไม่ใช่แค่โชว์คะแนน

### คำอธิบายที่ใช้พูด

งานนี้เป็นการตรวจจับความผิดปกติใน Network Traffic ของอุปกรณ์ IoT โดยเน้นข้อมูลจาก TCP และ MQTT ครับ ผมจะเล่าตั้งแต่ข้อจำกัดของข้อมูล วิธีสร้าง Normal profile การอ่าน protocol context ไปจนถึงเหตุผลที่เลือกไฟล์ `offline_02` เป็นตัวอย่างสำหรับอธิบาย

### ภาพที่ควรใช้

ไม่จำเป็นต้องเพิ่มภาพ ถ้าใช้ภาพ IoT/Network จาก template อยู่แล้ว

ถ้าต้องการเปลี่ยนภาพ ให้ใช้ภาพแนว:

- อุปกรณ์ IoT เชื่อมต่อผ่าน gateway
- Network packet ไหลระหว่าง device และ server
- ภาพรวม TCP + MQTT

### ไม่ควรใช้

- ภาพ hacker หรือ cyber security ที่ไม่เกี่ยวกับ IoT
- ภาพ leaderboard ตั้งแต่หน้าเปิดเรื่อง
- ภาพที่มีตัวเลขคะแนนหลายชุด

---

## Slide 2: THE PROBLEM IN ONE SENTENCE

### เป้าหมายการเล่า

ทำให้ผู้ฟังเข้าใจข้อจำกัดสำคัญที่สุด: Train ไม่มี Attack label

### คำอธิบายที่ใช้พูด

โจทย์ให้เราดู Network Traffic ใน Test 10,000 แถว แล้วตอบว่าแต่ละแถวเป็น Normal หรือ Attack แต่ Train 100,000 แถวมีเฉพาะ Normal เท่านั้นครับ เราจึงไม่สามารถสอนโมเดลแบบ Binary Classification ตามปกติได้ เพราะโมเดลไม่เคยเห็นตัวอย่าง Attack ที่ยืนยันแล้ว

### ภาพที่ควรแคป

แคปตารางหรือ notebook output ที่เห็นข้อมูล 2 ส่วน:

- `X_train`: 100,000 rows และมีเฉพาะ Normal
- `X_test`: 10,000 rows ที่ยังไม่มี label ให้ดู

ถ้าไม่มีภาพจริง ให้ทำตารางเล็ก ๆ:

| Dataset | Rows | Label ที่มี |
|---|---:|---|
| Train | 100,000 | Normal only |
| Test | 10,000 | ต้องทำนาย |

### จุดวางภาพ

วางภาพด้านขวา ให้เหลือพื้นที่ด้านซ้ายสำหรับ title และด้านล่างสำหรับคำพูด

### Caption แนะนำ

`Train มี Normal เท่านั้น จึงต้องใช้ One-Class Anomaly Detection`

### ไม่ควรใช้

- ภาพ confusion matrix ตั้งแต่สไลด์นี้
- ภาพที่เขียนว่า Train มี Attack label
- ตัวเลขที่ไม่ได้มาจาก dataset จริง

---

## Slide 3: DATA CHALLENGE

### เป้าหมายการเล่า

อธิบายว่าข้อมูลไม่ได้มีแค่ตัวเลข แต่มีความหมายของ network protocol ซ่อนอยู่

### คำอธิบายที่ใช้พูด

แต่ละแถวประกอบด้วย feature จาก TCP, MQTT และ timing ครับ ค่าใดค่าหนึ่งอาจดูแปลกเมื่อดูเดี่ยว ๆ แต่ไม่ได้แปลว่าเป็น Attack ทันที เราต้องดูว่าค่านั้นเกิดขึ้นใน stream ไหน เกิดร่วมกับ packet แบบใด และสอดคล้องกับ state ของ protocol หรือไม่

### ภาพที่ควรแคป

เลือกหนึ่งแบบ:

- ภาพ `df.head()` ที่เห็นชื่อคอลัมน์จริง
- ภาพรายชื่อ feature แบ่งเป็น TCP และ MQTT
- ภาพ output `train.shape`, `test.shape` และจำนวนคอลัมน์

ควร highlight คอลัมน์สำคัญ เช่น:

`frame.len`, `tcp.len`, `tcp.window_size`, `tcp.stream`, `mqtt.msgtype`, `mqtt.kalive`, `mqtt.len`

### จุดวางภาพ

วางภาพด้านขวา หรือวางเป็น card 2 ใบ: `TCP Features` กับ `MQTT Features`

### Caption แนะนำ

`Network row ต้องอ่านทั้ง packet shape และ protocol context`

### ไม่ควรใช้

- ตารางเต็มทุกคอลัมน์จนอ่านไม่ออก
- ภาพ raw CSV ที่ไม่มีการ highlight
- อธิบาย feature โดยไม่บอกว่าช่วยตัดสินอะไร

---

## Slide 4: MAIN IDEA ONE-CLASS DETECTION

### เป้าหมายการเล่า

อธิบายภาพรวมวิธีคิดให้คนที่ไม่ใช่สาย machine learning เข้าใจได้

### คำอธิบายที่ใช้พูด

ผมเปรียบเทียบวิธีนี้กับ รปภ. ที่รู้จักพฤติกรรมปกติของคนในอาคารครับ แม้ไม่เคยเห็นผู้บุกรุกมาก่อน ก็ยังสังเกตพฤติกรรมที่แตกต่างได้ โมเดลจึงเริ่มจากการเรียนรู้ขอบเขตของ Normal แล้วค่อยตรวจความเบี่ยงเบนที่มีหลักฐานรองรับ

### ภาพที่ควรแคปหรือทำเพิ่ม

ควรมี diagram 4 ขั้น:

```text
Normal Train
     ↓
Normal Profile
     ↓
Test Traffic
     ↓
Meaningful Deviation
```

หรือใช้ scatter plot ที่แบ่งจุดเป็น:

- จุดสีเทา: Normal ที่พบใน Train
- จุดขาว: Normal รูปแบบใหม่
- จุดแดง: candidate Attack

### จุดวางภาพ

วางภาพตรงพื้นที่ขวา ให้ลูกศรอ่านจากบนลงล่างหรือซ้ายไปขวา

### Caption แนะนำ

`เรียนรู้ Normal ก่อน ไม่ได้จำ Attack แบบตายตัว`

### ไม่ควรใช้

- เขียนว่า anomaly ทุกจุดคือ Attack
- ใช้ภาพ neural network ที่ไม่เชื่อมกับวิธีทำจริง
- แสดง decision boundary โดยไม่มีคำอธิบาย

---

## Slide 5: FEATURES THAT MATTER

### เป้าหมายการเล่า

แสดงว่าการเลือก feature อิงจากความหมายของ TCP/MQTT ไม่ใช่เลือกจากค่า importance อย่างเดียว

### คำอธิบายที่ใช้พูด

ผมแบ่ง feature เป็นสองกลุ่มครับ กลุ่ม TCP บอกขนาด packet และ state ของ connection ส่วน MQTT บอกชนิดของ message และรายละเอียดของ application protocol การอ่านสองกลุ่มร่วมกันช่วยลด false positive จากค่าที่หายากแต่ยังเป็น Normal

### ภาพที่ควรแคป

ควรแคปตาราง feature แบบอ่านง่าย:

| กลุ่ม | ตัวอย่าง | ความหมาย |
|---|---|---|
| TCP | `frame.len`, `tcp.len` | ขนาด packet |
| TCP | `tcp.window_size` | รูปแบบ flow control |
| TCP | SYN/ACK/RST | state ของ connection |
| MQTT | `mqtt.msgtype` | CONNECT/PUBLISH/SUBSCRIBE |
| MQTT | `mqtt.kalive` | keep-alive |
| MQTT | `mqtt.len` | ความยาว message |

ถ้ามี packet capture ให้แคปหนึ่ง packet แล้ววงกลม field ที่ใช้จริง

### จุดวางภาพ

วางภาพเป็นตารางสองคอลัมน์ `TCP` และ `MQTT` ด้านขวา

### Caption แนะนำ

`Feature ที่ดีต้องอธิบายพฤติกรรมของ protocol ได้`

### ไม่ควรใช้

- กราฟ feature importance ที่ไม่มีชื่อ feature อ่านได้
- บอกว่า feature ที่มีค่าสูงสุดสำคัญที่สุดเสมอ
- แปะทุก feature ใน dataset

---

## Slide 6: FROM RULES TO A ROBUST MODEL

### เป้าหมายการเล่า

แสดง pipeline ที่ใช้จริง และทำให้ผู้ฟังเห็นว่าระบบไม่ได้ใช้ rule เดียวตัดสิน

### คำอธิบายที่ใช้พูด

ผมเริ่มจากกฎที่อธิบายได้ก่อนครับ เพราะไม่มี Attack label ที่เชื่อถือได้ จากนั้นเพิ่ม protocol rules, stream context และ hard-negative filter กฎแต่ละชั้นมีหน้าที่ต่างกัน และช่วยลดการทำนาย Attack มากเกินไป

### ภาพที่ควรแคป

ภาพหลักควรเป็น code จาก:

`outputs/predict_final_model.py`

แคปอย่างน้อย 3 ส่วน:

1. Normal profile หรือชุดของ window/packet shape
2. SYN / CONNECT / SUBSCRIBE / PUBLISH rules
3. PINGRESP hard-negative filter

ถ้าแคป code เดียว ให้เลือกส่วนที่มีชื่อ function และเงื่อนไขครบ ไม่เอาเฉพาะบรรทัดกลาง function

### Code ที่ควรเห็นในภาพ

```python
is_hard_negative = (
    frame_len == 56
    and tcp_window_size == 253
    and mqtt_msgtype == 13
)
```

### จุดวางภาพ

วาง code ด้านขวา ใช้พื้นหลังเข้ม ตัวอักษรขาว และ highlight เฉพาะเงื่อนไขสำคัญ

### Caption แนะนำ

`หลายหลักฐานร่วมกัน ดีกว่า anomaly score เดี่ยว`

### ไม่ควรใช้

- แคป code ยาวจนอ่านไม่ได้
- ใช้คำว่า model trained ถ้าเป็น deterministic rule engine
- แสดงกฎโดยไม่อธิบายว่ากฎลด false positive อย่างไร

---

## Slide 7: AI + HUMAN VALIDATION

### เป้าหมายการเล่า

อธิบายบทบาทของ AI ให้ตรงความจริง: AI ช่วยตั้งสมมติฐานและทดลอง แต่คนตรวจ protocol และตัดสินใจ

### คำอธิบายที่ใช้พูด

AI ช่วยให้ผมอธิบาย feature เสนอ rule สร้าง code และจัดอันดับ residual rows ได้เร็วขึ้นครับ แต่ผมไม่ใช้ผลจาก AI ครั้งเดียวแล้วเชื่อทันที ทุกแนวคิดต้องกลับมาตรวจด้วย protocol meaning, stream context และ hard negatives

### ภาพที่ควรแคป

เลือกหนึ่งแบบ:

- workflow `Hypothesis → Code → Test → Review`
- ภาพ notebook ที่แสดงการทดลองโมเดลหลายแบบ
- ภาพตารางเปรียบเทียบ ExtraTrees, RandomForest, HistGradientBoosting และ IsolationForest

ถ้าใช้ภาพ workflow ให้แยกสี:

- สีเทา: AI ช่วยเสนอ
- สีขาว: คนตรวจสอบ
- สีเขียวอ่อน: ผลที่ผ่าน validation

### จุดวางภาพ

วาง workflow ทางขวา ให้เห็นลูกศรย้อนกลับจาก validation ไปปรับ rule

### Caption แนะนำ

`AI ช่วยค้นหาไอเดีย แต่ evidence เป็นคนตัดสิน`

### ไม่ควรใช้

- แคป chat ที่มีข้อความส่วนตัวหรือ token
- เขียนว่า AI เป็นผู้ตัดสินผลลัพธ์
- แสดงโมเดล ML เป็น production model ทั้งที่ใช้เพื่อทดลอง

---

## Slide 8: THE RESULT WE EXPLAIN

### เป้าหมายการเล่า

ยืนยันว่า presentation กำลังอธิบายไฟล์ใด และผลลัพธ์ที่รายงานเป็นเท่าไร

### คำอธิบายที่ใช้พูด

ไฟล์ที่เลือกมาอธิบายคือ `submission_offline_02_hedge_payload132.csv` ครับ ไฟล์นี้ต่อยอดจาก baseline ด้วย structural pattern ที่ `Id=9816` และ payload hedge ที่ `Id=1145` โดยตั้งใจเพิ่มเฉพาะกลุ่มที่มีเหตุผล ไม่ได้เพิ่มทุกแถวที่ดูผิดปกติ

### ภาพที่ต้องแคป

แคปหน้า Kaggle ที่เห็นพร้อมกัน:

- ชื่อไฟล์ `submission_offline_02_hedge_payload132.csv`
- Private Score `0.97198`
- Public Score `0.96267`
- สถานะ submission สำเร็จ ถ้ามี

ถ้าแคปหน้า Kaggle แล้วตัวเลขอยู่คนละส่วน ให้รวมเป็นภาพเดียวด้วยการ crop สองบริเวณ ห้ามใช้ภาพจากคนละ submission

### ภาพเสริมที่แนะนำ

แคป `head()` ของ CSV ให้เห็น:

```text
Id,label
...
```

ภาพนี้ช่วยยืนยันว่าไฟล์พร้อมใช้และมี schema ถูกต้อง แต่ไม่ต้องแปะใหญ่กว่าภาพคะแนน

### จุดวางภาพ

วางภาพ Kaggle ด้านขวา และวางชื่อไฟล์/คะแนนแบบตัวอักษรใหญ่ด้านซ้ายหรือใต้ภาพ

### Caption แนะนำ

`Kaggle result reported by user: Private F1 0.97198, Public F1 0.96267`

### ไม่ควรใช้

- ภาพของ `submission_v27` หรือ version อื่น
- เอาคะแนน offline benchmark ไปเรียกว่า Kaggle score
- เขียนว่าอันดับ 1 ถ้าไม่มีหลักฐานจาก leaderboard ชุดเดียวกัน

---

## Slide 9: WHAT WE LEARNED

### เป้าหมายการเล่า

สรุปบทเรียนจากการทดลอง ให้ผู้ฟังจำหลักการได้ ไม่ใช่จำแค่คะแนน

### คำอธิบายที่ใช้พูด

Anomaly ไม่ได้แปลว่า Attack เสมอไปครับ Normal รูปแบบใหม่ก็แตกต่างจาก Train ได้เหมือนกัน ถ้าทำนาย Attack มากเกินไป False Positive จะเพิ่มและ F1 อาจลดลง ดังนั้นระบบที่ดีต้องรักษาสมดุลระหว่าง Precision และ Recall

### ภาพที่ควรแปะ

เลือกหนึ่งภาพ:

- confusion matrix
- กราฟ Precision–Recall
- กราฟเปรียบเทียบจำนวน positive labels กับ F1
- ตัวอย่าง false positive เช่น PINGRESP ที่ดูแปลกแต่เป็น Normal

ภาพที่ดีที่สุดคือ case study หนึ่งตัวอย่าง:

```text
ดูแปลกจาก feature เดี่ยว
        ↓
ตรวจ stream context
        ↓
พบว่าเป็น Normal
        ↓
ตัดออกด้วย hard negative
```

### จุดวางภาพ

วางภาพด้านขวา ไม่ต้องใช้ภาพใหญ่เต็มพื้นที่ เพราะข้อความบทเรียนด้านซ้ายสำคัญกว่า

### Caption แนะนำ

`Rare ไม่ได้แปลว่า Attack ต้องตรวจ context ก่อน`

### ไม่ควรใช้

- กราฟที่ไม่มีแกนหรือ legend
- confusion matrix จาก validation ที่ไม่มี label จริง
- สรุปว่า model แม่นยำจาก anomaly count อย่างเดียว

---

## Slide 10: FINAL TAKEAWAY

### เป้าหมายการเล่า

ปิดเนื้อหาให้เหลือ workflow เดียวที่จำง่าย และเชื่อมกลับมาที่ไฟล์ `offline_02`

### คำอธิบายที่ใช้พูด

สรุปคือผมเปลี่ยนข้อจำกัดของข้อมูล Normal-only ให้เป็นวิธีคิดแบบ protocol-first ครับ เริ่มจากเรียนรู้พฤติกรรมปกติ ใช้ TCP และ MQTT เป็นหลักฐาน เพิ่ม context ระดับ stream และใช้ hard negatives ป้องกัน false positive จากนั้นจึงเลือกผลลัพธ์ที่มีเหตุผลไปสร้างไฟล์สุดท้าย

### ภาพที่ควรแปะ

ไม่จำเป็นต้องแปะภาพใหม่ ถ้าสไลด์มี pipeline ครบแล้ว

ถ้าต้องการภาพ ให้ใช้ summary card เดียว:

```text
Normal-only data
        ↓
Learn protocol behavior
        ↓
Validate with context
        ↓
offline_02
Private 0.97198 | Public 0.96267
```

### จุดวางภาพ

วาง summary card ด้านขวา ไม่ใช้ screenshot Kaggle ซ้ำจากสไลด์ 8

### Caption แนะนำ

`Protocol-first pipeline: เรียนรู้ ตรวจหลักฐาน แล้วค่อยตัดสิน`

### ไม่ควรใช้

- ภาพคะแนนชุดเดิมซ้ำเต็มหน้า
- เพิ่มเทคนิคใหม่ที่ไม่เคยพูดมาก่อน
- ใช้คำว่า guaranteed หรือชนะอันดับ 1

---

## Slide 11: THANK YOU

### เป้าหมายการเล่า

จบ presentation ให้สะอาดและเปิดทางถามตอบ

### ภาพที่ควรใช้

ไม่ต้องแปะภาพ ปล่อยพื้นที่โล่งช่วยให้จบอย่างมืออาชีพ

ถ้าต้องการเพิ่มข้อมูล ให้ใส่แค่:

- ชื่อผู้จัดทำ
- รหัส 610686
- ชื่อโปรเจกต์สั้น ๆ

### คำพูดปิด

ขอบคุณครับ ถ้ามีคำถาม ผมอธิบายต่อได้ทั้งส่วนของ Normal profile, protocol rules, context gate, hard negative และเหตุผลที่เลือกไฟล์ `offline_02`

---

## ลำดับภาพที่ควรเตรียมก่อน

ถ้ามีเวลาจำกัด ให้เตรียมตามลำดับนี้:

1. ภาพ Kaggle score ของ `offline_02`
2. ภาพ code rule engine
3. ภาพ Train/Test schema
4. ภาพ TCP/MQTT feature table
5. ภาพ One-Class Detection diagram
6. ภาพ hard-negative case
7. ภาพ ML experiment workflow

## ชื่อไฟล์ภาพแนะนำ

```text
slide-02-train-test-schema.png
slide-03-feature-overview.png
slide-04-one-class-flow.png
slide-05-tcp-mqtt-features.png
slide-06-rule-engine-code.png
slide-07-ai-human-validation.png
slide-08-offline02-kaggle-score.png
slide-09-hard-negative-case.png
slide-10-final-summary.png
```

## Final checklist

- ชื่อไฟล์ในภาพตรงกับ `submission_offline_02_hedge_payload132.csv`
- Private F1 ตรง `0.97198`
- Public F1 ตรง `0.96267`
- ภาพ code มาจาก `outputs/predict_final_model.py`
- ไม่มี API token หรือ credential ในภาพ
- ไม่มีภาพ version เก่าที่มีคะแนน `0.96193` ปะปน
- ทุกภาพอ่านได้เมื่อย่อเหลือความกว้างประมาณครึ่งสไลด์
- ภาพทุกภาพมีหน้าที่อธิบาย ไม่ใช่แค่ตกแต่ง
