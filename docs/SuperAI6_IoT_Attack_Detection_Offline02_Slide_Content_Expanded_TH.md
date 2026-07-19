# เนื้อหาสไลด์แบบขยาย

เอกสารนี้เป็นเนื้อหาสำหรับนำไปวางในสไลด์และใช้พูดประกอบ โดยขยายจาก deck `SuperAI6_IoT_Attack_Detection_Offline02_Presentation_TH.pptx` ให้มีรายละเอียดมากขึ้น

หัวข้อทั้งหมดอิงจากไฟล์:

`submission_offline_02_hedge_payload132.csv`

ข้อมูลที่ต้องใช้ให้ตรงกัน:

- Train: 100,000 แถว, มี Normal เท่านั้น
- Test: 10,000 แถว
- Feature: network features 22 คอลัมน์ และ `Id`
- Submission schema: `Id,label`
- label=1 ในไฟล์ที่เลือก: 2,811 แถว
- Private F1: `0.97198`
- Public F1: `0.96267`
- Structural addition: `Id=9816`
- Payload hedge: `Id=1145`

คะแนน Private/Public เป็นผลที่ผู้ใช้รายงานจาก Kaggle ควรเขียนกำกับทุกครั้งว่าเป็น leaderboard score ไม่ใช่คะแนนที่คำนวณจาก CSV โดยตรง

---

## Slide 1: IoT Attack Detection through TCP + MQTT

### ข้อความหลักบนสไลด์

```text
IOT ATTACK DETECTION
THROUGH TCP + MQTT

การตรวจจับการโจมตีจากพฤติกรรมของ Network Traffic
ด้วยข้อมูล Normal-only และ protocol context
```

### ข้อความรอง

```text
จากข้อมูลดิบ สู่ Normal profile
จาก Normal profile สู่ evidence ที่ตรวจสอบได้
```

### คำอธิบายเพิ่มเติม

โปรเจกต์นี้มองการตรวจจับการโจมตีของ IoT จากพฤติกรรมการสื่อสารบนเครือข่าย โดยใช้ข้อมูลระดับ packet และ connection เช่น ขนาดของ frame, TCP window, flag ของ connection และข้อมูล MQTT

จุดสำคัญคือระบบไม่ได้เริ่มจากการจำคำตอบว่า Attack มีหน้าตาแบบใด เพราะ Train ไม่มี Attack label ที่เชื่อถือได้ แต่เริ่มจากการเรียนรู้ว่า Normal Traffic ที่พบจริงมีรูปแบบแบบใด แล้วค่อยค้นหาความแตกต่างที่มีเหตุผลรองรับ

### ประโยคพูด

วันนี้ผมจะเล่าวิธีคิดในการทำ IoT Attack Detection จากข้อมูล Network Traffic จริงครับ จุดที่น่าสนใจคือ Train มี Normal เท่านั้น ทำให้เราไม่สามารถใช้วิธี Classification แบบปกติได้ ผมจึงใช้แนวคิด Normal profile ร่วมกับความหมายของ TCP และ MQTT เพื่อหาความผิดปกติที่มีหลักฐานมากพอ

### สิ่งที่ผู้ฟังควรจำ

`งานนี้ไม่ใช่การเดา Attack จากค่าที่หายาก แต่เป็นการเรียนรู้พฤติกรรมปกติแล้วตรวจสอบความเบี่ยงเบนด้วย protocol context`

---

## Slide 2: The Problem in One Sentence

### ข้อความหลักบนสไลด์

```text
โจทย์ต้องการคำตอบเพียง 2 ค่า

0 = Normal
1 = Attack

แต่ข้อมูล Train มี Normal เท่านั้น
ไม่มีตัวอย่าง Attack ให้เรียนรู้โดยตรง
```

### ตารางอธิบายโจทย์

| ส่วนข้อมูล | จำนวน | สิ่งที่มีให้ | สิ่งที่ต้องทำ |
|---|---:|---|---|
| Train | 100,000 | Normal | สร้าง Normal profile |
| Test | 10,000 | ยังไม่รู้ label | ทำนาย 0 หรือ 1 |

### ปัญหาที่เกิดขึ้น

1. ไม่มี Attack label ที่ใช้เป็น ground truth ใน Train
2. โมเดลไม่รู้ว่า Attack จริงมีลักษณะใด
3. ค่าแปลกใน Test อาจเป็น Normal รูปแบบใหม่
4. ถ้าทำนาย Attack มากเกินไป False Positive จะเพิ่ม
5. ถ้าระวังมากเกินไป Attack จริงอาจถูกมองข้าม

### คำอธิบายเพิ่มเติม

ถ้ามีทั้ง Normal และ Attack ใน Train เราอาจใช้ Binary Classification ได้ แต่โจทย์นี้ไม่ใช่สถานการณ์นั้นครับ เราต้องใช้วิธีคิดแบบ One-Class หรือ Normal-only Detection โดยนิยามขอบเขตของ Normal จากข้อมูลที่มี แล้วตรวจว่าข้อมูล Test อยู่นอกขอบเขตนั้นหรือไม่

อย่างไรก็ตาม การอยู่นอกขอบเขตไม่ได้แปลว่าเป็น Attack ทันที เพราะข้อมูลเครือข่ายสามารถมีรูปแบบใหม่ที่ยังปลอดภัยได้ ระบบจึงต้องใช้ protocol และ context มาช่วยยืนยันอีกชั้น

### ประโยคพูด

ความยากของโจทย์ไม่ได้อยู่ที่การสร้าง label อย่างเดียวครับ แต่อยู่ที่เราไม่มีตัวอย่าง Attack ให้ดูตั้งแต่ต้น ดังนั้นคำถามที่ผมใช้จึงไม่ใช่ “แถวนี้เหมือน Attack หรือไม่” แต่เป็น “แถวนี้แตกต่างจาก Normal เพราะอะไร และมีหลักฐานจาก protocol รองรับหรือเปล่า”

### สรุปสั้นท้ายสไลด์

`Normal-only data เปลี่ยนวิธีทำจาก Classification เป็น One-Class Anomaly Detection`

---

## Slide 3: Data Challenge

### ข้อความหลักบนสไลด์

```text
ข้อมูลหนึ่งแถวไม่ใช่แค่ตัวเลข
แต่เป็นส่วนหนึ่งของการสื่อสารบน network
```

### โครงสร้างข้อมูล

```text
Train: 100,000 rows
Test: 10,000 rows
Network features: 22 columns
Identifier: Id
Protocols: TCP / MQTT
Target: label 0 หรือ 1
```

### แบ่ง feature ตามความหมาย

#### TCP layer

- `frame.len`: ขนาด frame ทั้งหมด
- `tcp.len`: ขนาด TCP payload
- `tcp.window_size`: TCP receive window
- `tcp.flags.syn`: จุดเริ่มต้น connection
- `tcp.flags.ack`: การตอบรับ packet
- `tcp.flags.reset`: การ reset connection
- `tcp.stream`: กลุ่มของ connection เดียวกัน

#### MQTT layer

- `mqtt.msgtype`: CONNECT, PUBLISH, SUBSCRIBE หรือ PINGRESP
- `mqtt.kalive`: ค่า keep-alive ของ client
- `mqtt.len`: ความยาว MQTT message
- `mqtt.topic_len`: ความยาว topic

### ทำไมดู feature เดี่ยวไม่ได้

ค่า `tcp.window_size` ที่ไม่เคยปรากฏใน Train อาจดูเป็น anomaly แต่ถ้าเกิดใน packet ที่เป็น PINGRESP และอยู่ใน stream ปกติ ก็ไม่ควรรีบตีความเป็น Attack

ในทางกลับกัน packet ที่แต่ละค่าดูปกติ อาจเป็นส่วนหนึ่งของ SYN pattern ที่เกิดซ้ำผิดธรรมชาติเมื่อดูทั้ง stream ดังนั้นจุดสำคัญคือความสัมพันธ์ระหว่าง feature ไม่ใช่ค่าคอลัมน์เดียว

### ประโยคพูด

ข้อมูลชุดนี้ต้องอ่านเหมือนเราดูบทสนทนาของ network ครับ TCP บอกสถานะการเชื่อมต่อ ส่วน MQTT บอกความหมายของ message ถ้าอ่านแยกกัน เราอาจมอง Normal เป็น Attack หรือมอง Attack เป็น packet ธรรมดาได้

### สรุปสั้นท้ายสไลด์

`Protocol meaning + packet shape + stream context สำคัญกว่าความหายากของค่าหนึ่งค่า`

---

## Slide 4: Main Idea: One-Class Detection

### ข้อความหลักบนสไลด์

```text
เรียนรู้ Normal ก่อน
ตรวจความเบี่ยงเบนทีหลัง
และยืนยันด้วย protocol evidence
```

### ขั้นตอนแนวคิด

```text
Normal Train
    ↓
Normal Profile
    ↓
Test Traffic
    ↓
Candidate Deviations
    ↓
Protocol + Context Validation
    ↓
Final label
```

### Normal profile คืออะไร

Normal profile คือชุดรูปแบบที่สังเกตได้จาก Train เช่น:

- ค่า window ที่พบใน Normal
- คู่ของ `frame.len` และ `tcp.window_size`
- รูปแบบ SYN ที่เกิดใน connection ปกติ
- MQTT message type ที่พบตามบริบท
- packet family ที่เกิดร่วมกันใน stream

ระบบไม่ได้เก็บเพียงค่าเฉลี่ยของทุกคอลัมน์ แต่เก็บรูปแบบที่มีความหมายต่อการสื่อสารด้วย

### เปรียบเทียบให้เข้าใจง่าย

เปรียบเหมือน รปภ. ที่รู้จักพฤติกรรมของคนในอาคารครับ รปภ. ไม่จำเป็นต้องเคยเห็นผู้บุกรุกทุกแบบ แต่รู้ว่าเวลาปกติคนควรเข้าทางไหน อยู่บริเวณใด และมีพฤติกรรมแบบใด เมื่อมีพฤติกรรมผิดจากบริบท จึงค่อยตรวจสอบเพิ่ม

### สิ่งที่ระบบไม่ทำ

- ไม่ประกาศว่า rare = Attack
- ไม่ใช้ anomaly score เดี่ยว
- ไม่ตัดสินจาก packet เดี่ยวทุกกรณี
- ไม่เพิ่ม positive label ทุกแถวที่อยู่นอก Normal profile

### ประโยคพูด

ผมไม่ได้ให้ระบบจำว่า Attack ต้องมีหน้าตาแบบเดียวครับ เพราะในโลกจริง Attack เปลี่ยนรูปแบบได้ แต่พฤติกรรมของ protocol และ connection ยังมีโครงสร้างบางอย่างให้ตรวจสอบได้ เราจึงเริ่มจากขอบเขต Normal แล้วใช้หลักฐานหลายชั้นประกอบการตัดสิน

### สรุปสั้นท้ายสไลด์

`One-Class Detection = รู้จัก Normal ให้ดี ก่อนค้นหาสิ่งที่ผิดจาก Normal`

---

## Slide 5: Features That Matter

### ข้อความหลักบนสไลด์

```text
เลือก feature จากความหมายของ protocol
ไม่ใช่เลือกเพราะค่านั้นหายากอย่างเดียว
```

### Feature table สำหรับวางบนสไลด์

| Feature | ชั้นข้อมูล | สิ่งที่บอก | ใช้ตรวจอะไร |
|---|---|---|---|
| `frame.len` | TCP/frame | ขนาด frame | packet shape |
| `tcp.len` | TCP | ขนาด payload | packet มีข้อมูลหรือไม่ |
| `tcp.window_size` | TCP | flow control | connection pattern |
| SYN/ACK/RST | TCP flags | สถานะ connection | handshake / reset |
| `tcp.stream` | TCP context | กลุ่ม connection | ลำดับและบริบท |
| `mqtt.msgtype` | MQTT | ประเภท message | CONNECT/PUBLISH/SUBSCRIBE |
| `mqtt.kalive` | MQTT | keep-alive | client behavior |
| `mqtt.len` | MQTT | ความยาว message | payload pattern |
| `mqtt.topic_len` | MQTT | ความยาว topic | publish/subscribe shape |

### กลุ่ม TCP

TCP ช่วยบอกว่า packet อยู่ในช่วงใดของ connection เช่น กำลังเริ่มเชื่อมต่อ กำลังตอบรับ หรือกำลัง reset การดู SYN/ACK/RST ร่วมกับ window size และ stream ทำให้เห็นรูปแบบที่ละเอียดกว่าการดู flag เดี่ยว

### กลุ่ม MQTT

MQTT ช่วยอธิบายความหมายของ application message เช่น CONNECT ใช้เริ่ม session, PUBLISH ใช้ส่งข้อมูล, SUBSCRIBE ใช้ขอรับ topic และ PINGRESP ใช้ตอบ keep-alive การแยก message type ช่วยให้ระบบไม่ตีความ packet ของระบบ keep-alive เป็น Attack ง่ายเกินไป

### ตัวอย่างการตีความ

```text
tcp.len = 0
ไม่ได้แปลว่า Attack เสมอไป

ต้องดูเพิ่มว่า:
- เป็น SYN หรือ ACK
- อยู่ใน tcp.stream ใด
- มี MQTT message หรือไม่
- เกิดซ้ำเป็น pattern หรือเกิดเดี่ยว ๆ
```

### ประโยคพูด

Feature ที่ดีสำหรับงานนี้ต้องช่วยตอบว่า packet กำลังทำอะไรอยู่ครับ ไม่ใช่แค่บอกว่าค่าของมันสูงหรือต่ำ เพราะค่าที่หายากอาจเป็นพฤติกรรมปกติของ MQTT ได้

### สรุปสั้นท้ายสไลด์

`อ่าน TCP เพื่อเข้าใจ connection อ่าน MQTT เพื่อเข้าใจความหมายของ message`

---

## Slide 6: From Rules to a Robust Model

### ข้อความหลักบนสไลด์

```text
เริ่มจากกฎที่อธิบายได้
เพิ่ม context เพื่อคุม false positive
ใช้ hard negative ป้องกันการตีความเกินจริง
```

### Pipeline เชิงเทคนิค

#### 1. Normal profile

เก็บรูปแบบที่พบใน Normal Train เช่น:

- ชุดค่า TCP window
- คู่ `frame.len` กับ `tcp.window_size`
- packet shape ที่พบซ้ำ
- stream/family ที่ผ่านการตรวจสอบ

#### 2. Protocol rules

ตรวจรูปแบบที่มีความหมาย:

- SYN signature
- MQTT CONNECT ที่มี keep-alive อยู่ในกลุ่มที่พบจริง
- SUBSCRIBE ที่มี message type ไม่ถูกต้อง
- PUBLISH ที่มี payload length หรือบริบทผิดจาก profile

#### 3. Context gate

ไม่ตัดสินจาก packet เดี่ยว แต่ตรวจ:

- `tcp.stream`
- packet family
- ลำดับของ packet
- ความสัมพันธ์ระหว่าง TCP และ MQTT
- รูปแบบที่เกิดซ้ำใน window เดียวกัน

#### 4. Hard-negative filter

ดึงกรณีที่ดูผิดปกติออกเมื่อมีหลักฐานว่าเป็น Normal เช่น PINGRESP ที่มี:

```python
frame_len == 56
tcp_window_size == 253
mqtt_msgtype == 13
```

### โค้ดตัวอย่างสำหรับวางบนสไลด์

```python
is_syn_signature = (
    frame_len == 54
    and tcp_window_size == 512
    and syn == 1
    and ack == 0
)

is_hard_negative = (
    frame_len == 56
    and tcp_window_size == 253
    and mqtt_msgtype == 13
)

predict_attack = is_syn_signature and not is_hard_negative
```

โค้ดบนสไลด์เป็นตัวอย่างเพื่ออธิบายแนวคิด ควรอธิบายว่าโค้ดจริงใช้หลายเงื่อนไขและ context มากกว่าตัวอย่างสั้นนี้

### ML ที่ใช้เป็นตัวช่วยทดลอง

มีการทดลอง ExtraTrees, RandomForest, HistGradientBoosting และ IsolationForest เพื่อจัดอันดับ residual rows และสำรวจ pattern เพิ่มเติม แต่ ML score ไม่ได้ถูกใช้เป็นหลักฐานเดียว เพราะ pseudo-label อาจทำให้เกิด circularity

### ประโยคพูด

ผมเริ่มจากกฎที่ตรวจสอบย้อนกลับได้ก่อนครับ เพราะเรายังไม่มี Attack label ที่มั่นใจ จากนั้นเพิ่ม context gate เพื่อไม่ให้ packet เดี่ยวลากผลลัพธ์ไปผิดทาง และใช้ hard negative ดึง Normal ที่ดูแปลกออกก่อนสร้าง label สุดท้าย

### สรุปสั้นท้ายสไลด์

`High-precision rules + context gate + hard negative = robust decision`

---

## Slide 7: AI + Human Validation

### ข้อความหลักบนสไลด์

```text
AI ช่วยค้นหาและเร่งการทดลอง
คนตรวจ protocol และตัดสินใจจากหลักฐาน
```

### AI ช่วยในขั้นตอนไหน

- อธิบายความหมายของ feature
- เสนอ hypothesis จาก pattern ที่พบ
- ร่าง rule และ code สำหรับทดลอง
- จัดอันดับ residual rows
- เปรียบเทียบโมเดลหลายชนิด
- ช่วยสรุป false positive และ false negative

### คนต้องตรวจอะไร

- อ่านความหมายของ TCP state
- อ่าน message type ของ MQTT
- ตรวจว่า pattern อยู่ใน stream ใด
- ตรวจว่าเกิดซ้ำหรือเกิดเพียงครั้งเดียว
- หา Normal counterexample
- ตัดสินว่า evidence เพียงพอหรือยัง

### วงจรการทำงาน

```text
ตั้งสมมติฐาน
      ↓
ให้ AI ช่วยร่าง rule/code
      ↓
รันกับข้อมูลจริง
      ↓
อ่าน protocol context
      ↓
สร้าง hard negative
      ↓
ปรับ rule และทดสอบใหม่
```

### เหตุผลที่ไม่เชื่อ AI ทันที

AI สามารถเสนอ pattern ที่ฟังดูสมเหตุผล แต่ยังผิดในบริบทของข้อมูลได้ เช่น เห็นค่า rare แล้วสรุปว่าเป็น Attack หรือใช้ pseudo-label จาก rule เดิมไป train model แล้วนำผล model กลับมายืนยัน rule เดิม ซึ่งเป็น circularity

### ประโยคพูด

AI ทำให้ผมทดลองได้เร็วขึ้นครับ แต่ไม่ได้แทนการตรวจสอบ ถ้า AI บอกว่าแถวหนึ่งน่าสงสัย ผมต้องกลับไปดู TCP, MQTT, stream และ Normal counterexample ก่อนเสมอ ผลสุดท้ายต้องอธิบายได้ว่าใช้หลักฐานใด ไม่ใช่ตอบว่าโมเดลบอกมา

### สรุปสั้นท้ายสไลด์

`AI ช่วยคิดเร็วขึ้น แต่ evidence เป็นคนตัดสิน`

---

## Slide 8: The Result We Explain

### ข้อความหลักบนสไลด์

```text
submission_offline_02_hedge_payload132.csv

Rows: 10,000
Positive labels: 2,811

Private F1: 0.97198
Public F1:  0.96267
```

### สิ่งที่ไฟล์นี้ต่อยอด

```text
Baseline
   + structural pattern: Id=9816
   + payload hedge: Id=1145
   = offline_02 candidate
```

### อธิบาย structural addition

`Id=9816` เป็นแถวที่ถูกพิจารณาจากรูปแบบเชิงโครงสร้างของ TCP/stream โดยเน้นว่ารูปแบบนั้นต้องมีเหตุผลเมื่อดูร่วมกับ connection ไม่ใช่เพียงเพราะเป็นค่าใหม่ใน Test

### อธิบาย payload hedge

`Id=1145` เป็นการเพิ่มแบบระมัดระวังจาก payload pattern ที่มีหลักฐานสนับสนุน จุดประสงค์คือเติม candidate ที่ baseline อาจพลาด แต่ไม่เพิ่มทุกแถวที่มี payload ต่างจาก Train

### ทำไมต้องใช้คำว่า hedge

คำว่า hedge สื่อว่าการเพิ่มนี้เป็นการตัดสินใจแบบระวังความเสี่ยงครับ เราต้องการเพิ่ม Recall ในกลุ่มที่มีเหตุผล โดยไม่แลกกับ False Positive จำนวนมากจน F1 ลดลง

### วิธีอธิบายคะแนน

Private F1 `0.97198` และ Public F1 `0.96267` เป็นคะแนนที่ผู้ใช้รายงานจาก Kaggle แยกให้ชัดว่า:

- Private score ใช้ประเมินบนชุดข้อมูลที่ผู้แข่งขันไม่เห็น
- Public score ใช้ประเมินบนส่วนที่ leaderboard เปิดให้วัด
- คะแนนสองส่วนอาจต่างกันเพราะ distribution ของข้อมูลไม่เหมือนกัน

### ประโยคพูด

ไฟล์ที่ผมนำมาอธิบายคือ offline_02 ครับ ไฟล์นี้ไม่ได้เพิ่ม label แบบกว้าง ๆ แต่ต่อยอดจาก baseline ด้วย structural row ที่ Id 9816 และ payload hedge ที่ Id 1145 ผลที่รายงานคือ Private F1 0.97198 และ Public F1 0.96267 ซึ่งควรอ่านเป็นผลของ submission บน leaderboard ไม่ใช่การรับประกันว่าทุกชุดข้อมูลจะได้คะแนนเท่ากัน

### สรุปสั้นท้ายสไลด์

`เลือกเพิ่มเฉพาะ anomaly ที่มี context และหลักฐานรองรับ`

---

## Slide 9: What We Learned

### ข้อความหลักบนสไลด์

```text
1. Rare ไม่ได้แปลว่า Attack
2. Context สำคัญกว่า packet เดี่ยว
3. ทำนาย Attack มากไป F1 อาจลด
4. ML score ไม่ใช่หลักฐานสุดท้าย
5. กฎที่อธิบายได้ช่วยลดความเสี่ยง
```

### บทเรียนที่ 1: Rare ไม่ได้แปลว่า Attack

Train อาจไม่ได้ครอบคลุม Normal ทุกแบบ ดังนั้นค่าที่ไม่เคยเจออาจเป็นเพียง Normal รูปแบบใหม่ การใช้ unseen value เป็นเงื่อนไข Attack โดยตรงทำให้ False Positive เพิ่มง่าย

### บทเรียนที่ 2: Context สำคัญกว่า packet เดี่ยว

packet เดียวบอกข้อมูลได้จำกัด ต้องดู stream, ลำดับ, packet family และ message type ร่วมกัน การตรวจระดับ context ช่วยแยก packet ที่ดูแปลกแต่เกิดใน flow ปกติออกจาก pattern ที่ผิดปกติจริง

### บทเรียนที่ 3: F1 ต้องรักษาสมดุล

การเพิ่มจำนวน Attack ที่ทำนายได้อาจช่วย Recall แต่ถ้าเพิ่ม False Positive มากเกินไป Precision จะลด และ F1 อาจแย่ลง ระบบจึงต้องเพิ่ม positive label แบบ selective ไม่ใช่เพิ่มให้มากที่สุด

### บทเรียนที่ 4: ML score ไม่ใช่หลักฐาน

Anomaly score ช่วยจัดอันดับแถวที่น่าสงสัย แต่ไม่บอกความหมายของ protocol การใช้ score เป็นตัวตัดสินทันทีอาจเลือก Normal ที่หายากเข้ามาเป็น Attack

### บทเรียนที่ 5: Explainability สำคัญ

กฎที่อธิบายได้ช่วยตอบคำถามว่าแถวนี้ถูกเลือกเพราะอะไร และช่วยสร้าง hard negative ได้ง่าย เมื่อพบ counterexample ก็รู้ว่าควรแก้กฎส่วนใด

### ประโยคพูด

บทเรียนสำคัญที่สุดคือ anomaly ไม่ได้แปลว่า attack เสมอไปครับ ระบบที่ดีไม่ใช่ระบบที่ทำนาย Attack เยอะที่สุด แต่เป็นระบบที่รู้ว่าเมื่อใดควรเพิ่ม Recall และเมื่อใดควรหยุดเพื่อป้องกัน False Positive

### สรุปสั้นท้ายสไลด์

`เป้าหมายไม่ใช่จับทุกสิ่งที่แปลก แต่จับความผิดปกติที่อธิบายได้`

---

## Slide 10: Final Takeaway

### ข้อความหลักบนสไลด์

```text
Normal-only data
        ↓
Learn protocol behavior
        ↓
Detect meaningful deviations
        ↓
Validate with stream context
        ↓
Create explainable labels
        ↓
offline_02
```

### สรุปเทคนิคทั้งหมด

1. เริ่มจาก Normal profile ที่สร้างจาก Train
2. ใช้ TCP feature อธิบาย connection และ packet shape
3. ใช้ MQTT feature อธิบาย message semantics
4. ใช้ stream context แทนการดู packet เดี่ยว
5. ใช้ hard negative ลด false positive
6. ใช้ ML เป็นเครื่องมือจัดอันดับและสำรวจ pattern
7. ตรวจผลด้วยหลักฐานก่อนสร้าง label สุดท้าย

### ข้อจำกัดที่ควรพูดตรง ๆ

- ไม่มี Attack label ใน Train ให้ตรวจสอบโดยตรง
- คะแนน leaderboard อาจต่างจาก offline benchmark
- Normal รูปแบบใหม่อาจถูกมองเป็น anomaly
- Rule engine ต้องดูแลเมื่อ protocol distribution เปลี่ยน
- ผลลัพธ์ต้องตรวจซ้ำเมื่อมีข้อมูลหรือ feature ใหม่

### สิ่งที่พัฒนาต่อได้

- เพิ่ม labeled validation set จากผู้เชี่ยวชาญ
- สร้าง stream-level feature ให้ละเอียดขึ้น
- ทำ calibration ของ anomaly score
- ทำ error analysis แยกตาม MQTT message type
- เก็บ evidence สำหรับทุก positive label
- เปรียบเทียบ rule engine กับ supervised model เมื่อมี label จริง

### ประโยคพูด

สรุปคือผมใช้ข้อจำกัดของข้อมูล Normal-only เป็นจุดตั้งต้นของวิธีคิดแบบ protocol-first ครับ เริ่มจากเรียนรู้ Normal ใช้ TCP และ MQTT เป็นหลักฐาน ดู context ระดับ stream แล้วค่อยเลือกความเบี่ยงเบนที่อธิบายได้ ไฟล์ offline_02 จึงไม่ได้มีแค่คะแนน แต่มีเหตุผลของการตัดสินใจประกอบด้วย

### สรุปสั้นท้ายสไลด์

`Learn Normal → Read Protocol → Validate Context → Explain Result`

---

## Slide 11: Thank You / Questions

### ข้อความหลักบนสไลด์

```text
THANK YOU

IoT Attack Detection through TCP + MQTT
Questions?
```

### ประเด็นที่พร้อมตอบคำถาม

ถ้าผู้ฟังถามต่อ สามารถอธิบายได้ 4 กลุ่ม:

#### 1. ข้อมูล

- ทำไม Train มีแต่ Normal
- ทำไมจึงใช้ One-Class Detection
- TCP และ MQTT ต่างกันอย่างไร

#### 2. เทคนิค

- Normal profile สร้างจากอะไร
- ทำไมต้องใช้ stream context
- hard negative ช่วยลด false positive อย่างไร

#### 3. ไฟล์ผลลัพธ์

- ทำไมเลือก `offline_02`
- Id 9816 และ Id 1145 เพิ่มเข้ามาเพราะอะไร
- Private/Public score ต่างกันอย่างไร

#### 4. ข้อจำกัด

- ไม่มี Attack label ใน Train
- คะแนน leaderboard ไม่ใช่ ground truth ทุกกรณี
- ต้องตรวจสอบ model เมื่อ distribution เปลี่ยน

### ประโยคปิด

ขอบคุณครับ ถ้ามีคำถาม ผมอธิบายต่อได้ทั้งวิธีสร้าง Normal profile, protocol rules, stream context, hard negative และเหตุผลที่เลือกไฟล์ offline_02

---

## เวอร์ชันสั้นสำหรับวางเป็นกล่องข้อความ

ถ้าพื้นที่สไลด์จำกัด ใช้ข้อความชุดนี้แทน paragraph ยาว:

### Problem

`Train มี Normal เท่านั้น จึงไม่มี Attack pattern ให้เรียนรู้โดยตรง ระบบต้องเรียนรู้ขอบเขต Normal แล้วตรวจความเบี่ยงเบนด้วย protocol context`

### Data

`ข้อมูลมี TCP, MQTT และ timing features การตัดสินต้องดูความสัมพันธ์ระหว่าง packet, message type และ stream`

### Method

`Normal profile → Protocol rules → Context gate → Hard negative → Final label`

### Features

`TCP บอกสถานะ connection, MQTT บอกความหมายของ message, stream บอกบริบทของ flow`

### Result

`offline_02: Private F1 0.97198, Public F1 0.96267, 10,000 rows, positive labels 2,811`

### Lesson

`Rare ไม่ได้แปลว่า Attack และ anomaly score ไม่ใช่หลักฐานสุดท้าย`

### Conclusion

`Learn Normal → Read Protocol → Validate Context → Explain Result`

