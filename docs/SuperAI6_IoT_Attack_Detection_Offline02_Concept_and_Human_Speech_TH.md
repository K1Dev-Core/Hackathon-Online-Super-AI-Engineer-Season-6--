# แนวคิดการทำงานและประโยคพูดแบบภาษาคน

เอกสารนี้ใช้เป็น script หลักสำหรับอธิบาย presentation ของไฟล์:

`submission_offline_02_hedge_payload132.csv`

เนื้อหาเน้น 2 ส่วน:

1. แนวคิดเบื้องหลังว่าเลือกวิธีนี้เพราะอะไร
2. ประโยคพูดที่ใช้พรีเซนต์ให้ฟังเป็นธรรมชาติ

## ภาพรวมวิธีทำในประโยคเดียว

เราเริ่มจากเรียนรู้ว่า Normal Traffic มีพฤติกรรมแบบใด แล้วใช้ TCP, MQTT, stream context และ hard negative ตรวจว่าความแตกต่างที่พบเป็น Attack จริง หรือเป็นเพียง Normal รูปแบบใหม่

## ข้อมูลที่ต้องพูดให้ตรงกัน

- Train มี 100,000 แถว และมี Normal เท่านั้น
- Test มี 10,000 แถว
- ไฟล์ผลลัพธ์ใช้คอลัมน์ `Id,label`
- ไฟล์ที่เลือกมี label=1 จำนวน 2,811 แถว
- Structural addition: `Id=9816`
- Payload hedge: `Id=1145`
- Private F1: `0.97198`
- Public F1: `0.96267`

คะแนน Private/Public เป็นคะแนนที่ผู้ใช้รายงานจาก Kaggle ควรพูดให้ชัดว่าเป็น leaderboard result ไม่ใช่คะแนนที่คำนวณจาก CSV เพียงอย่างเดียว

---

## Slide 1: เปิดเรื่อง

### แนวคิดที่ต้องการสื่อ

งานนี้คือการตรวจจับการโจมตีใน IoT Network Traffic โดยใช้ข้อมูลจาก TCP และ MQTT เป็นหลัก จุดสำคัญไม่ได้อยู่ที่การทำโมเดลให้ซับซ้อนที่สุด แต่อยู่ที่การอ่านข้อมูลให้เข้าใจว่า packet กำลังทำอะไร และความผิดปกตินั้นมีเหตุผลพอจะเรียกว่า Attack หรือไม่

เพราะ Train มีแต่ Normal วิธีทำจึงต้องเริ่มจาก Normal behavior ก่อน เราไม่สามารถเริ่มจากการจำตัวอย่าง Attack แบบ supervised learning ได้เหมือนโจทย์ทั่วไป

### สิ่งที่ทำจริง

1. อ่าน schema และความหมายของ feature
2. แยก feature ตาม TCP, MQTT และ connection context
3. สร้าง Normal profile จาก Train
4. ตรวจ candidate ใน Test ด้วย rule และ context
5. ทำ hard-negative filtering
6. สร้างไฟล์ label และประเมินผลจาก leaderboard

### ประโยคพูดแบบคน

งานนี้เป็นโจทย์ตรวจจับการโจมตีของอุปกรณ์ IoT จาก Network Traffic ครับ ตอนแรกดูเหมือนเป็นงาน Classification ทั่วไป แต่พอเปิดข้อมูลจริง เราพบว่า Train มีแต่ Normal ไม่มีตัวอย่าง Attack ให้เรียนรู้เลย วิธีคิดจึงต้องเปลี่ยนจากการจำ Attack มาเป็นการทำความเข้าใจ Normal ให้ละเอียดก่อน

### ประโยคเชื่อมไปสไลด์ถัดไป

ก่อนจะคุยเรื่องโมเดล เราต้องเข้าใจก่อนว่าโจทย์นี้ให้ข้อมูลอะไร และทำไมข้อจำกัดของข้อมูลถึงสำคัญมาก

---

## Slide 2: ทำไมโจทย์นี้ไม่ใช่ Classification ปกติ

### แนวคิดที่ต้องการสื่อ

ถ้า Train มีทั้ง Normal และ Attack เราสามารถสอนโมเดลให้แยกสองกลุ่มได้ แต่โจทย์นี้ Train มี Normal เท่านั้น จึงไม่มี Attack pattern ที่ยืนยันแล้วให้โมเดลเรียนรู้โดยตรง

คำถามจึงเปลี่ยนจาก:

```text
แถวนี้เหมือน Attack หรือไม่
```

เป็น:

```text
แถวนี้แตกต่างจาก Normal อย่างไร
และความแตกต่างนั้นมีหลักฐานจาก protocol หรือไม่
```

### สิ่งที่ทำจริง

- อ่าน Train เพื่อดูขอบเขตของ Normal
- เก็บค่าหรือรูปแบบที่พบใน Normal
- ตรวจ Test ว่ามีรูปแบบใดหลุดจาก Normal profile
- ไม่ประกาศทุกค่าใหม่ว่าเป็น Attack
- ใช้ context ช่วยยืนยันก่อนสร้าง label=1

### ทำไมต้องระวัง False Positive

Normal Train อาจไม่ครอบคลุม Normal ทุกแบบในโลกจริง ดังนั้น Test ที่แตกต่างจาก Train อาจเป็นแค่ Normal รูปแบบใหม่ ถ้าเรา label ทุกแถวที่ไม่เคยเจอเป็น Attack จำนวน positive จะมากเกินไป และ F1 อาจลดลงเพราะ False Positive เพิ่ม

### ประโยคพูดแบบคน

ความยากอยู่ตรงนี้ครับ เราไม่ได้มีคำตอบตัวอย่างให้ดูว่า Attack หน้าตาเป็นอย่างไร ถ้าเห็นค่าใหม่แล้วรีบ label เป็น Attack เราจะจับ Normal รูปแบบใหม่ติดไปด้วย ผมเลยเริ่มจากคำถามที่ปลอดภัยกว่า คือแถวนี้ต่างจาก Normal เพราะอะไร และมีหลักฐานพอหรือยัง

### ประโยคเชื่อม

เมื่อรู้แล้วว่าเราต้องเรียนรู้ Normal ต่อไปคือดูว่าในข้อมูลหนึ่งแถวมีสัญญาณอะไรให้เราอ่านได้บ้าง

---

## Slide 3: อ่านข้อมูลเหมือนอ่าน network conversation

### แนวคิดที่ต้องการสื่อ

ข้อมูลหนึ่งแถวไม่ใช่ตัวเลขที่แยกขาดจากกัน แต่เป็นส่วนหนึ่งของการสื่อสารบน network การอ่านให้ถูกต้องต้องแบ่งเป็น 3 ระดับ:

1. Packet shape: packet มีขนาดและรูปแบบอย่างไร
2. Protocol meaning: packet กำลังทำหน้าที่อะไร
3. Connection context: packet นี้อยู่ใน stream หรือ flow แบบใด

### สิ่งที่ทำจริง

#### ระดับ packet

ดู `frame.len`, `tcp.len`, `tcp.window_size` และ TCP flags เพื่อเข้าใจขนาดและ state เบื้องต้น

#### ระดับ protocol

ดู `mqtt.msgtype`, `mqtt.kalive`, `mqtt.len` และ `mqtt.topic_len` เพื่อแยก CONNECT, PUBLISH, SUBSCRIBE หรือ PINGRESP

#### ระดับ stream

ดู `tcp.stream` และ packet family เพื่อไม่ตัดสินจาก packet เดี่ยวที่อาจไม่มีบริบทเพียงพอ

### ตัวอย่างการตีความ

```text
tcp.len = 0
```

ค่านี้ยังบอกไม่ได้ว่าเป็น Attack หรือไม่ ต้องดูต่อว่าเป็น SYN, ACK, PINGRESP หรือ packet ในช่วงใดของ stream ถ้าเป็น PINGRESP ที่เกิดใน flow ปกติ ก็ไม่ควร label เป็น Attack เพียงเพราะ payload เป็นศูนย์

### ประโยคพูดแบบคน

ผมพยายามไม่มองข้อมูลเป็นตารางตัวเลขอย่างเดียวครับ ผมมองแต่ละแถวเป็นส่วนหนึ่งของบทสนทนาบน network TCP ช่วยบอกสถานะการเชื่อมต่อ ส่วน MQTT ช่วยบอกว่าข้อความนั้นกำลังทำอะไร พอเอาสองส่วนนี้มาดูร่วมกัน เราจะลดการตีความผิดได้มาก

### ประโยคเชื่อม

เมื่อเข้าใจความหมายของข้อมูลแล้ว เราจึงสร้างตัวแทนของพฤติกรรมปกติขึ้นมาได้

---

## Slide 4: สร้าง Normal profile

### แนวคิดที่ต้องการสื่อ

Normal profile คือภาพรวมของรูปแบบที่พบใน Train ซึ่งประกอบด้วยค่าที่พบจริงและความสัมพันธ์ของค่าเหล่านั้น ไม่ใช่แค่ค่าเฉลี่ยของแต่ละคอลัมน์

### สิ่งที่เก็บใน Normal profile

- ชุด TCP window ที่พบใน Normal
- คู่ `frame.len` และ `tcp.window_size`
- SYN pattern ที่พบใน connection
- MQTT message type ที่เกิดในบริบทปกติ
- PUBLISH หรือ CONNECT shape ที่พบจริง
- stream/family ที่ช่วยอธิบายลำดับ packet

### เหตุผลที่ไม่ใช้ค่าเฉลี่ยอย่างเดียว

ค่าเฉลี่ยบอกค่ากลาง แต่ไม่บอกลำดับหรือความสัมพันธ์ของ packet การโจมตีบางแบบอาจใช้ค่าแต่ละคอลัมน์ที่ดูไม่ผิด แต่สร้าง sequence ที่ผิดจาก Normal เมื่อมองเป็น stream

### เปรียบเทียบง่าย ๆ

เหมือน รปภ. ที่ไม่ได้จำหน้าผู้บุกรุกทุกคน แต่รู้จักวิถีชีวิตปกติของคนในอาคาร รู้ว่าเวลาไหนคนควรอยู่ตรงไหน และพฤติกรรมใดควรตรวจเพิ่ม

### ประโยคพูดแบบคน

ผมสร้าง Normal profile เหมือนการทำแผนที่ของพฤติกรรมปกติครับ ไม่ได้เก็บแค่ว่าคอลัมน์นี้มีค่าอะไร แต่เก็บด้วยว่าค่าเหล่านั้นมักเกิดคู่กันหรือเกิดใน stream แบบไหน พอเจอ Test ที่ต่างออกไป เราจึงพออธิบายได้ว่าต่างตรงไหน

### ประโยคเชื่อม

Normal profile อย่างเดียวบอกได้ว่าอะไรต่าง แต่ยังต้องรู้ว่า feature ไหนช่วยอธิบายความต่างนั้น

---

## Slide 5: เลือก feature จากความหมาย ไม่ใช่ความหายาก

### แนวคิดที่ต้องการสื่อ

Feature ที่มีประโยชน์ต้องช่วยอธิบายพฤติกรรมของ connection หรือ message ได้ ไม่ใช่แค่มีค่า rare แล้วถูกเลือกเข้ามา

### กลุ่ม TCP

- `frame.len`: ขนาด frame รวม
- `tcp.len`: ขนาด TCP payload
- `tcp.window_size`: รูปแบบ flow control
- SYN/ACK/RST: state ของ connection
- `tcp.stream`: กลุ่มของ connection

TCP จึงเหมาะกับการดู packet shape, handshake, reset และลำดับของ connection

### กลุ่ม MQTT

- `mqtt.msgtype`: ความหมายของ message
- `mqtt.kalive`: ค่า keep-alive
- `mqtt.len`: ความยาว message
- `mqtt.topic_len`: ความยาว topic

MQTT ช่วยแยก message ที่ดูคล้ายกันจากมุม TCP แต่จริง ๆ มีหน้าที่ต่างกัน เช่น CONNECT, PUBLISH, SUBSCRIBE และ PINGRESP

### สิ่งที่ทำจริง

เราใช้ feature เป็นหลักฐานหลายชั้น เช่น:

```text
TCP shape
   + MQTT message type
   + stream context
   + ความถี่/การเกิดซ้ำ
   = หลักฐานที่แข็งแรงขึ้น
```

### ประโยคพูดแบบคน

ผมไม่ได้เลือก feature เพราะมันมีค่า importance สูงอย่างเดียวครับ ผมถามก่อนว่า feature นี้ช่วยอธิบายอะไรได้บ้าง ถ้าเป็น TCP ก็ช่วยอธิบาย connection ถ้าเป็น MQTT ก็ช่วยอธิบาย message เมื่อเอามาประกอบกัน เราจะรู้ว่า packet นี้ผิดปกติเพราะ protocol หรือแค่เป็นค่าที่หายาก

### ประโยคเชื่อม

จาก feature เหล่านี้ เราจึงเริ่มเขียนกฎที่ตรวจสอบย้อนหลังได้ แทนการปล่อยให้คะแนน anomaly ตัดสินทั้งหมด

---

## Slide 6: จากกฎพื้นฐานสู่ rule engine ที่ robust

### แนวคิดที่ต้องการสื่อ

ระบบหลักเป็น deterministic normal-profile rule engine กฎแต่ละชุดทำหน้าที่เป็น evidence anchor แล้วค่อยใช้ context ช่วยคุมความเสี่ยง

### ขั้นตอนที่ทำจริง

#### 1. Normal profile

สร้าง set ของ window และ packet shape ที่พบใน Normal

#### 2. Protocol signature

อ่าน pattern ที่มีความหมาย เช่น SYN, CONNECT, SUBSCRIBE และ PUBLISH

ตัวอย่าง SYN signature ที่ใช้ตรวจ:

```text
frame.len = 54
tcp.window_size = 512
SYN = 1
ACK = 0
```

#### 3. Context gate

ตรวจ `tcp.stream`, packet family และความสัมพันธ์ของ packet ใน window เดียวกัน ไม่ตัดสินจากแถวเดียวโดยไม่ดูบริบท

#### 4. Hard negative

ดึง Normal ที่ดูแปลกออกจาก candidate เช่น PINGRESP ที่มีรูปแบบ:

```text
frame.len = 56
tcp.window_size = 253
mqtt.msgtype = 13
```

### ทำไมต้องมี hard negative

การเพิ่ม rule เพื่อจับ Attack มักทำให้ระบบจับ Normal บางกลุ่มติดมาด้วย Hard negative ทำหน้าที่เป็นตัวเบรก ช่วยบอกว่า pattern นี้อาจดูผิดจาก profile แต่มีหลักฐานว่าเป็นพฤติกรรมปกติ

### ML ใช้ตรงไหน

ทดลอง ExtraTrees, RandomForest, HistGradientBoosting และ IsolationForest เพื่อสำรวจ residual rows และจัดอันดับ pattern แต่ใช้เป็นเครื่องมือช่วยวิเคราะห์ ไม่ใช่หลักฐานสุดท้าย เพราะ pseudo-label อาจทำให้ model เรียนจากความผิดพลาดของ rule เดิม

### ประโยคพูดแบบคน

ผมเริ่มจากกฎที่อธิบายได้ก่อนครับ เพราะเราไม่มี label Attack ที่มั่นใจ กฎแรกช่วยหากลุ่มที่น่าสงสัย กฎต่อมาดูว่าอยู่ใน stream แบบไหน แล้ว hard negative ช่วยดึงกรณีที่ดูแปลกแต่จริง ๆ เป็น Normal ออก วิธีนี้ทำให้เราไม่ได้เพิ่ม Attack แบบกว้างเกินไป

### ประโยคเชื่อม

กฎช่วยให้ระบบตรวจได้ แต่ในระหว่างพัฒนา AI ยังช่วยเราค้นหา pattern และทดลองแนวทางได้เร็วขึ้น

---

## Slide 7: AI ช่วยคิด คนช่วยตรวจ

### แนวคิดที่ต้องการสื่อ

AI เป็นผู้ช่วยด้านการค้นหาและการทดลอง ไม่ใช่ผู้ตัดสิน final label แทนคน

### AI ช่วยอะไร

- อธิบาย feature และ protocol field
- เสนอ hypothesis จาก residual pattern
- ร่าง code สำหรับทดลอง
- จัดอันดับแถวที่น่าสงสัย
- ช่วยเปรียบเทียบ model family
- ช่วยสรุป false positive ที่ควรตรวจต่อ

### คนตรวจอะไร

- ความหมายของ TCP state
- MQTT message semantics
- stream และ packet sequence
- Normal counterexample
- ผลกระทบต่อ Precision, Recall และ F1

### วงจรการทำงาน

```text
AI เสนอสมมติฐาน
        ↓
คนเลือกสิ่งที่มีเหตุผล
        ↓
ทดลองกับข้อมูลจริง
        ↓
อ่าน protocol context
        ↓
สร้าง hard negative
        ↓
ปรับ rule และทดสอบซ้ำ
```

### ความเสี่ยงของ pseudo-label

ถ้าใช้ rule สร้าง label ปลอม แล้วเอา label นั้นไป train model จากนั้นใช้ model มายืนยัน rule เดิม เราอาจได้ผลที่ดูดีแต่ไม่ได้เพิ่มความรู้จริง นี่คือเหตุผลที่ต้องกลับไปดู packet และ protocol ทุกครั้งที่ model เสนอ pattern ใหม่

### ประโยคพูดแบบคน

AI ช่วยให้ผมคิดและทดลองได้เร็วขึ้นครับ แต่ผมไม่เชื่อผลจาก AI ทันที ถ้า AI บอกว่าแถวหนึ่งน่าสงสัย ผมต้องกลับไปดูว่า packet นั้นอยู่ใน stream ไหน MQTT message type คืออะไร และมี Normal ตัวอย่างที่หักล้างได้หรือไม่

### ประโยคเชื่อม

หลังจากทดลองหลายแนวทาง เราเลือกไฟล์ที่มีเหตุผลเชิงโครงสร้างและมีคะแนน leaderboard สนับสนุนมาอธิบาย

---

## Slide 8: ทำไมเลือก offline_02

### แนวคิดที่ต้องการสื่อ

ไฟล์นี้เป็น candidate ที่ต่อยอดจาก baseline แบบ selective ไม่ได้เพิ่ม label ทุกแถวที่มี anomaly

### การเปลี่ยนแปลงของไฟล์

```text
Baseline
   ↓
เพิ่ม structural pattern ที่ Id=9816
   ↓
เพิ่ม payload hedge ที่ Id=1145
   ↓
submission_offline_02_hedge_payload132.csv
```

### ความหมายของ structural addition

`Id=9816` ถูกเลือกจากรูปแบบเชิงโครงสร้างของ TCP/stream ที่ช่วยเติม candidate ซึ่ง baseline อาจพลาด แต่ต้องอธิบายได้จากรูปแบบ connection ไม่ใช่เลือกจาก Id หรือความหายากเพียงอย่างเดียว

### ความหมายของ payload hedge

`Id=1145` เป็นการเพิ่มแบบ hedge คือเพิ่ม candidate ที่มี payload pattern สนับสนุน แต่ยังรักษาความระมัดระวังต่อ False Positive ไม่ได้ขยาย rule ให้จับ payload ที่แตกต่างทุกแบบ

### ผลลัพธ์ที่รายงาน

```text
Rows: 10,000
Positive labels: 2,811
Private F1: 0.97198
Public F1:  0.96267
```

### ประโยคพูดแบบคน

ไฟล์ที่ผมเลือกมาเล่าคือ offline_02 ครับ เหตุผลไม่ได้มีแค่คะแนน แต่เป็นเพราะเราพออธิบายได้ว่าไฟล์นี้ต่างจาก baseline ตรงไหน มี structural addition ที่ Id 9816 และ payload hedge ที่ Id 1145 แล้วค่อยดูผล Private กับ Public ประกอบกัน

คะแนนที่เห็นคือ Private F1 0.97198 และ Public F1 0.96267 ซึ่งเป็นคะแนนที่รายงานจาก Kaggle ผมจะไม่สรุปเกินกว่านี้ว่าเป็นคะแนนรับประกันของทุกชุดข้อมูล

### ประโยคเชื่อม

ผลคะแนนบอกว่าแนวทางนี้ใช้ได้ดีใน leaderboard แต่สิ่งที่สำคัญกว่าคือบทเรียนว่าอะไรทำให้ระบบดีขึ้น และอะไรทำให้ระบบพลาด

---

## Slide 9: บทเรียนจากการทำงาน

### แนวคิดที่ต้องการสื่อ

งานนี้สอนว่าใน Normal-only detection การเพิ่ม positive label ไม่ได้ทำให้ผลดีขึ้นเสมอ การเลือก candidate ต้องสมดุลระหว่างการจับ Attack ให้ครบกับการไม่ลาก Normal เข้ามาเป็น Attack

### บทเรียนสำคัญ

#### Rare ไม่ได้แปลว่า Attack

Train อาจไม่ครอบคลุม Normal ทุกแบบ ค่าใหม่จึงต้องตรวจต่อ ไม่ควร label ทันที

#### Context สำคัญกว่า packet เดี่ยว

packet เดี่ยวอาจไม่มีข้อมูลพอ ต้องดู stream, sequence และ message type

#### F1 แพ้ False Positive ได้ง่าย

ถ้าเพิ่ม Attack มากเกินไป Precision ลด และ F1 อาจลดแม้ Recall สูงขึ้น

#### ML score ไม่ใช่หลักฐาน

score ใช้จัดอันดับได้ แต่ต้องตรวจ protocol semantics และ Normal counterexample

#### Explainability ช่วยแก้ระบบ

กฎที่อธิบายได้ช่วยให้รู้ว่าควรเพิ่มหรือลดเงื่อนไขตรงไหน และช่วยสร้าง hard negative ได้

### ประโยคพูดแบบคน

บทเรียนที่ชัดที่สุดคือ anomaly ไม่ได้แปลว่า attack เสมอไปครับ ตอนแรกเรามักอยากจับให้ได้เยอะ ๆ แต่พอเพิ่ม positive มากเกินไป Normal ที่หายากก็ถูกลากเข้ามา ทำให้ False Positive เพิ่มและ F1 ลด สุดท้ายระบบที่ดีจึงต้องรู้จักหยุด ไม่ใช่พยายามทำให้ทุกความผิดปกติเป็น Attack

### ประโยคเชื่อม

ทั้งหมดนี้นำไปสู่ข้อสรุปเดียวว่าเราต้องใช้วิธีคิดแบบ protocol-first ไม่ใช่ score-first

---

## Slide 10: สรุปแนวคิดทั้งหมด

### แนวคิดที่ต้องการสื่อ

Pipeline ที่ดีสำหรับโจทย์นี้ไม่จำเป็นต้องเริ่มจาก model ใหญ่ที่สุด แต่ต้องเริ่มจากคำถามที่ถูกต้องและ evidence ที่ตรวจสอบได้

### Pipeline สรุป

```text
Normal-only Train
        ↓
สร้าง Normal profile
        ↓
อ่าน TCP + MQTT behavior
        ↓
ตรวจ stream context
        ↓
ใช้ hard negative ลด false positive
        ↓
เลือก candidate ที่อธิบายได้
        ↓
สร้าง submission label
```

### สิ่งที่ได้จากแนวคิดนี้

- ใช้ข้อมูล Normal-only ได้อย่างมีระบบ
- ลดการตัดสินจากค่า rare เพียงอย่างเดียว
- อธิบายเหตุผลของ positive label ได้
- ตรวจ false positive จาก Normal counterexample ได้
- ใช้ AI/ML เป็นผู้ช่วย ไม่ให้ผลทดลองกลายเป็นหลักฐานปลอม

### ข้อจำกัดที่ควรพูดตรง ๆ

- ไม่มี Attack ground truth ใน Train
- Normal รูปแบบใหม่อาจถูกตรวจเป็น anomaly
- คะแนน Public และ Private อาจต่างกัน
- Rule engine ต้องปรับเมื่อ distribution เปลี่ยน
- คะแนน leaderboard ไม่ได้แทนความถูกต้องของทุกแถวโดยตรง

### ประโยคพูดแบบคน

ถ้าสรุปให้สั้นที่สุด ผมเริ่มจากเรียนรู้ Normal แล้วใช้ protocol เป็นหลักฐาน ไม่ได้ใช้ความแปลกของค่าเพียงอย่างเดียว จากนั้นดู stream context และใช้ hard negative กันไม่ให้ Normal ที่ดูแปลกถูก label เป็น Attack ง่ายเกินไป นี่คือแนวคิดที่อยู่เบื้องหลังไฟล์ offline_02 ครับ

### ประโยคปิดเนื้อหา

`Learn Normal → Read Protocol → Validate Context → Explain Result`

---

## Slide 11: ปิดการนำเสนอและตอบคำถาม

### แนวคิดที่ต้องการสื่อ

ปิดด้วยภาพรวมที่จำง่าย และเปิดทางให้ผู้ฟังถามต่อด้านข้อมูล เทคนิค หรือผลลัพธ์

### ประเด็นที่พร้อมตอบ

#### ถ้าถามเรื่องข้อมูล

Train มีแต่ Normal จึงต้องใช้ One-Class Detection และสร้าง Normal profile แทนการ train classifier แบบสองคลาส

#### ถ้าถามเรื่อง feature

TCP ช่วยอธิบาย connection และ packet shape ส่วน MQTT ช่วยอธิบายความหมายของ message การใช้ร่วมกันช่วยให้ระบบเข้าใจ flow มากขึ้น

#### ถ้าถามเรื่อง rule

ระบบใช้ Normal profile, protocol signature, stream context และ hard-negative filter ไม่ได้ใช้ anomaly score เดี่ยว

#### ถ้าถามเรื่องคะแนน

ไฟล์ที่เลือกคือ `submission_offline_02_hedge_payload132.csv` ได้ Private F1 `0.97198` และ Public F1 `0.96267` ตามผลที่ผู้ใช้รายงานจาก Kaggle

#### ถ้าถามเรื่องข้อจำกัด

ยังไม่มี Attack label ใน Train จึงต้องระวังการตีความ anomaly และควรมี labeled validation เพิ่มในอนาคต

### ประโยคพูดปิด

ขอบคุณครับ งานนี้ทำให้เห็นว่าเราสามารถเริ่มจากข้อมูลที่มีแค่ Normal ได้ ถ้าเราเข้าใจ protocol และไม่รีบตัดสินจากค่าแปลกเพียงอย่างเดียว ถ้ามีคำถาม ผมอธิบายต่อได้ทั้ง Normal profile, TCP/MQTT feature, context gate, hard negative และเหตุผลที่เลือก offline_02 ครับ

---

## เวอร์ชันพูดต่อเนื่อง 3 นาที

โจทย์นี้ให้ Train ที่มีข้อมูล Normal อย่างเดียว และให้ Test ที่ต้องทำนายว่าแต่ละแถวเป็น Normal หรือ Attack ครับ เพราะไม่มี Attack label เราจึงไม่สามารถเริ่มจากการสอนโมเดลให้จำ Attack ได้ วิธีที่ผมใช้คือเริ่มจากเรียนรู้ Normal profile ก่อน แล้วค่อยตรวจว่า Test แถวไหนแตกต่างจาก Normal อย่างมีเหตุผล

ข้อมูลมีทั้ง TCP และ MQTT feature ผมจึงอ่านข้อมูลเป็นสามระดับ คือ packet shape, protocol meaning และ stream context TCP ช่วยบอกขนาด packet และสถานะ connection ส่วน MQTT ช่วยบอกว่า message กำลัง CONNECT, PUBLISH, SUBSCRIBE หรือ PINGRESP การใช้สองส่วนร่วมกันช่วยลดการตีความผิดจาก feature เดี่ยว

จากนั้นผมสร้าง rule engine ที่เริ่มจาก Normal profile แล้วตรวจ protocol signature เช่น SYN, CONNECT, SUBSCRIBE และ PUBLISH กฎจะไม่ตัดสินจาก packet เดี่ยว แต่ดู stream และ packet family เพิ่มด้วย สุดท้ายมี hard-negative filter สำหรับกรณีที่ดูแปลกแต่มีหลักฐานว่าเป็น Normal เช่น PINGRESP บางรูปแบบ

AI และ ML ช่วยให้ทดลอง feature, rule และ residual rows ได้เร็วขึ้นครับ แต่ผมไม่ใช้ผลจาก AI เป็นหลักฐานสุดท้าย เพราะ pseudo-label อาจทำให้เกิด circularity ทุก pattern ต้องกลับมาตรวจด้วย protocol meaning และ Normal counterexample

ไฟล์ที่นำมาอธิบายคือ `submission_offline_02_hedge_payload132.csv` ซึ่งต่อยอดจาก baseline ด้วย structural addition ที่ Id 9816 และ payload hedge ที่ Id 1145 ไฟล์นี้มี 10,000 แถว และ label=1 จำนวน 2,811 แถว คะแนนที่ผู้ใช้รายงานคือ Private F1 0.97198 และ Public F1 0.96267

บทเรียนสำคัญคือ rare ไม่ได้แปลว่า Attack และการทำนาย Attack มากเกินไปอาจทำให้ F1 ลด สรุปวิธีคิดทั้งหมดคือ Learn Normal, Read Protocol, Validate Context และ Explain Result ครับ

