# Speaker Notes: IoT Attack Detection through TCP + MQTT

เอกสารนี้เป็นคำพูดประกอบสไลด์สำหรับไฟล์ `submission_offline_02_hedge_payload132.csv` โดยตั้งใจเขียนให้พูดได้จริง ไม่ใช่การอ่านรายงานแบบเป็นทางการ

## ข้อมูลที่ใช้พูด

- ไฟล์: `outputs/offline_benchmark_candidates/submission_offline_02_hedge_payload132.csv`
- รูปแบบไฟล์: `Id,label`
- จำนวนแถว: 10,000
- label=1: 2,811 แถว
- Private F1: `0.97198`
- Public F1: `0.96267`
- การเปลี่ยนหลัก: baseline + structural `Id=9816` + payload hedge `Id=1145`
- หมายเหตุ: คะแนน Private/Public เป็นผลที่ผู้ใช้รายงานจาก Kaggle ไม่ใช่คะแนนที่คำนวณจากไฟล์ CSV เพียงอย่างเดียว

## Slide 1: เปิดเรื่อง

วันนี้ผมจะเล่าวิธีคิดในการตรวจจับการโจมตีของ IoT Network Traffic โดยใช้ TCP และ MQTT เป็นหลักครับ จุดสำคัญของงานนี้ไม่ใช่แค่ทำให้ได้ label แต่คือการอธิบายให้ได้ว่า ทำไมแถวหนึ่งถึงถูกมองว่าเป็น Attack และทำไมอีกแถวหนึ่งถึงไม่ควรถูกตัดสินแบบนั้น

## Slide 2: โจทย์จริง

โจทย์คือให้ดูข้อมูล Network Traffic ใน Test 10,000 แถว แล้วตอบว่าแต่ละแถวเป็น Normal หรือ Attack แต่ข้อจำกัดคือ Train 100,000 แถวมีเฉพาะ Normal เท่านั้น เราจึงไม่มีตัวอย่าง Attack ให้โมเดลเรียนรู้โดยตรง วิธีคิดที่เหมาะกว่าคือเรียนรู้รูปแบบ Normal ก่อน แล้วค่อยหาความเบี่ยงเบนที่มีหลักฐานรองรับ

## Slide 3: ความท้าทายของข้อมูล

ข้อมูลมีทั้ง feature ของ TCP, MQTT และ timing ครับ ดังนั้นค่าในแถวหนึ่งอาจไม่ได้ผิดปกติเมื่อดูแยกกัน แต่จะเห็นความหมายเมื่อดูร่วมกับ stream หรือ packet family ตัวอย่างเช่น TCP window ที่แปลกอาจเป็นแค่รูปแบบใหม่ของ Normal ถ้าไม่มี protocol context ก็ไม่ควรรีบสรุปว่าเป็น Attack

## Slide 4: แนวคิด One-Class

ผมเปรียบเทียบวิธีนี้กับ รปภ. ที่รู้จักพฤติกรรมปกติของคนในอาคาร แม้ไม่เคยเห็นผู้บุกรุกมาก่อน ก็ยังสังเกตพฤติกรรมที่แตกต่างได้ โมเดลจึงไม่ได้จำภาพ Attack แบบตายตัว แต่สร้างขอบเขตของ Normal แล้วตรวจว่าความแตกต่างนั้นมีความหมายจริงหรือเป็นเพียง Normal รูปแบบใหม่

## Slide 5: Feature ที่มีความหมาย

ผมให้ความสำคัญกับสองกลุ่มครับ กลุ่มแรกคือ TCP เช่น `frame.len`, `tcp.len`, `tcp.window_size`, SYN, ACK, RST และ `tcp.stream` กลุ่มที่สองคือ MQTT เช่น `mqtt.msgtype`, `mqtt.kalive`, `mqtt.len` และความยาว topic เพราะ feature เหล่านี้ช่วยบอกทั้งขนาด packet และ state ของการสื่อสาร ไม่ใช่แค่บอกว่าค่านั้นหายาก

## Slide 6: Pipeline ที่ใช้จริง

ขั้นแรกคือสร้าง Normal profile จาก window และ packet shape ที่พบจริง ขั้นต่อมาคืออ่าน protocol rules เช่น SYN, CONNECT, SUBSCRIBE และ PUBLISH จากนั้นใช้ context gate ดู stream และ family ไม่ตัดสินจาก packet เดี่ยว สุดท้ายคือ hard-negative filter ซึ่งช่วยตัดกรณีอย่าง PINGRESP ที่ดูแปลกแต่ตรวจแล้วเป็น Normal ออกไป

## Slide 7: AI ช่วยอย่างไร

AI ช่วยให้ผมอธิบาย feature เสนอ rule และ code จัดอันดับ residual rows และทดลองโมเดลอย่าง ExtraTrees, RandomForest, HistGradientBoosting และ IsolationForest ได้เร็วขึ้น แต่ผลจาก AI ไม่ใช่หลักฐานสุดท้าย ทุกแนวคิดต้องกลับมาตรวจด้วย protocol meaning, stream context และ hard negatives โดยเฉพาะโมเดลที่ใช้ pseudo-label เพราะมีความเสี่ยงเรื่อง circularity

## Slide 8: ไฟล์และผลลัพธ์

ไฟล์ที่เลือกมาอธิบายคือ `submission_offline_02_hedge_payload132.csv` ครับ ไฟล์นี้ต่อยอดจาก baseline ด้วย structural row ที่ช่วยเติมรูปแบบ SYN stream และ payload hedge ที่ `Id=1145` โดยเลือกเพิ่มเฉพาะกลุ่มที่มีเหตุผล ไม่ได้กวาดทุกแถวที่ดูผิดปกติ ผลที่รายงานคือ Private F1 `0.97198` และ Public F1 `0.96267`

## Slide 9: บทเรียน

บทเรียนที่สำคัญที่สุดคือ anomaly ไม่ได้แปลว่า Attack เสมอไปครับ Normal รูปแบบใหม่ก็แตกต่างจาก Train ได้เหมือนกัน การทำนาย Attack มากเกินไปอาจทำให้ False Positive เพิ่มและ F1 ลดลง ดังนั้น ML score ควรเป็นตัวช่วยจัดลำดับ ไม่ใช่หลักฐานสุดท้าย กฎที่อธิบายได้และตรวจสอบย้อนกลับจึงสำคัญมาก

## Slide 10: สรุป

สรุปคือผมเปลี่ยนข้อจำกัดของข้อมูล Normal-only ให้เป็นวิธีคิดแบบ protocol-first ครับ เริ่มจากเรียนรู้พฤติกรรมปกติ ใช้ TCP และ MQTT เป็นหลักฐาน เพิ่ม context ระดับ stream และใช้ hard negatives ป้องกัน False Positive นี่คือเหตุผลที่ไฟล์ offline_02 อธิบายได้ทั้งวิธีทำและเหตุผลของผลลัพธ์

## Slide 11: ปิดการนำเสนอ

ขอบคุณครับ ถ้ามีคำถาม ผมอธิบายต่อได้ทั้งส่วนของ Normal profile, protocol rules, การเลือก Id 9816 กับ Id 1145 และเหตุผลที่ไม่ใช้ anomaly score เดี่ยวในการตัดสิน

## จุดอ้างอิงสำหรับตอบคำถามเชิงเทคนิค

- โมเดลและกฎหลัก: `outputs/predict_final_model.py`
- ไฟล์ผลลัพธ์ที่ใช้พูด: `outputs/offline_benchmark_candidates/submission_offline_02_hedge_payload132.csv`
- รายงานเชิงเทคนิค: `docs/SuperAI6_IoT_Attack_Detection_Technical_DeepDive_TH.md`
- รายงานออกแบบระบบ: `docs/SuperAI6_IoT_Attack_Detection_Design_Report_TH.md`

ตัวอย่างโครงสร้างกฎที่ใช้จริงในระบบมีลักษณะประมาณนี้:

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
    and mqtt_msgtype == 13  # PINGRESP ที่พบใน Normal
)
```

แนวคิดสำคัญคือไม่ใช้เงื่อนไขเดียวตัดสิน แต่รวม packet shape, protocol state, stream context และ hard-negative filter แล้วจึงสร้าง label สุดท้าย
