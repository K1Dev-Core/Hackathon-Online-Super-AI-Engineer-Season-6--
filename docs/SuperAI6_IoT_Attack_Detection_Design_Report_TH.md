# The IoT Attack Detection Challenge

**คำอธิบาย:** รายงานการออกแบบ detector สำหรับข้อมูลฝึกแบบ Normal-only ด้วย Protocol Rules, Stream Structure และ PCAP Evidence  
**ผู้จัดทำ:** 610686-วชิรวิทย์  
**วันที่:** กรกฎาคม 2569

# บทสรุปผู้บริหาร

โจทย์นี้ให้ `X_train.csv` จำนวน 100,000 records ซึ่งเป็น Normal ทั้งหมด แต่ `X_test.csv` จำนวน 10,000 records มีทั้ง Normal และ Attack การไม่มีตัวอย่าง Attack ที่ติด label ทำให้ supervised binary classifier ทั่วไปใช้ไม่ได้โดยตรง ปัญหาจึงเป็น one-class anomaly detection ที่ต้องแยก attack ออกจาก rare-normal ให้แม่น

แนวทางออกแบบใช้ high-precision anchors จากความหมายของ TCP และ MQTT ก่อน แล้วเพิ่ม recall ผ่าน structural completion ภายใน TCP stream และ controlled leaderboard experiments ทุก candidate ต้องผ่าน normal exclusion, hard-negative checks และ source/PCAP falsification ก่อนถูกรวมใน submission หลัก

ไฟล์ที่เลือกได้ Public F1 `0.96267` และ Private F1 `0.97198` สูงกว่า baseline ผู้จัดซึ่งได้ Public `0.62303` และ Private `0.65030` อย่างมาก การสแกนหลักฐานต้นทางครอบคลุม attack PCAP 313 ไฟล์และ normal PCAP 49 ไฟล์ รวมมากกว่า 37 GB หรือประมาณ 260.9 ล้าน TCP packets

## ภาพรวม

| มิติ | ผลลัพธ์ | ความหมาย |
|---|---:|---|
| Public F1 | 0.96267 | คะแนนสูงสุดของไฟล์ที่เลือก |
| Private F1 | 0.97198 | คะแนนตัดสินของไฟล์ที่เลือก |
| Positive labels | 2,811 / 10,000 | detector แบบ precision-first |
| PCAP coverage | 362 files | 313 attack + 49 normal |

## บริบทและเป้าหมาย

ระบบต้องทำนาย `0` สำหรับ Normal communication และ `1` สำหรับ Network attack โดยประเมินด้วย F1-score ซึ่งสมดุล Precision กับ Recall ข้อมูล test แบ่ง Public และ Private อย่างละครึ่ง และส่งได้ 5 ครั้งต่อวัน การออกแบบจึงต้องใช้ submission quota เป็น controlled experiment ไม่ใช่ brute-force search

ชุดข้อมูลครอบคลุม Dictionary Attack, Invalid Subscription Attack, Dictionary Attack with Will Payload, Publish Attack และ TCP SYN Flooding Attack การโจมตีแต่ละชนิดอยู่คนละชั้นของ protocol: บางชนิดแสดงที่ CONNECT fields บางชนิดแสดงที่ MQTT transaction และ SYN Flood แสดงที่ TCP state

# ข้อค้นพบหลัก

แนวทางที่ได้ผลไม่ใช่ anomaly score เดี่ยว แต่เป็น rule–evidence system ซึ่งใช้ protocol semantics เป็น anchor และยอมยกเลิกสมมติฐานเมื่อผลจริงขัดแย้ง

## เงื่อนไขข้อมูลที่กำหนดการออกแบบ

ข้อมูล 23 features แบ่งเป็น 3 กลุ่ม ได้แก่ frame/protocol fields, TCP fields และ MQTT fields ค่า missing ใน MQTT เป็น missing by design เมื่อ packet ไม่มี MQTT layer ไม่ควรตีความเป็นข้อมูลเสีย ส่วน `tcp.stream` เป็น identity ภายใน capture ไม่ใช่ global identity ข้ามไฟล์

record ใน stream เดียวกันสัมพันธ์สูง การ split แบบ random row จะทำให้ packet ใกล้กันรั่วข้าม train/validation จึงเหมาะกับการวิเคราะห์เชิงโครงสร้าง แต่การพัฒนา model รอบถัดไปต้องใช้ group-held-out split ตาม capture หรือ session

## Finding 1 — Protocol rules ให้ precision anchors

Normal profile ถูกสร้างจากค่าที่เกิดจริงใน `X_train` จากนั้น detector ใช้กฎหลัก 6 กลุ่ม:

1. TCP window ที่ไม่เคยพบใน Normal
2. คู่ `frame.len + tcp.window_size` ใหม่ โดยตัด PUBLISH ออกจาก novelty rule
3. SYN flood signature: `frame.len=54`, `window=512`, `SYN=1`, `ACK=0`
4. Dictionary CONNECT: `mqtt.msgtype=1` และ keep-alive 60 หรือ 3600
5. Invalid subscription: MQTT type 8 หรือ 9
6. Publish signature: MQTT type 3 และ message length 19 หรือ 44

การรวมกฎด้วย OR ช่วย Recall แต่ต้องมี exclusion rules เพื่อรักษา Precision โดยเฉพาะ PUBLISH ซึ่งมี payload length หลากหลายและสร้าง rare-normal ได้มาก

## Finding 2 — Hard negatives สำคัญกว่า model confidence

Pseudo-label model เคยให้ attack probability ประมาณ 0.99 กับ PINGRESP บางกลุ่ม แต่ controlled probe แสดงว่าเป็น false positive detector จึงตัดทุกแถวที่มี `frame.len=56`, `tcp.window_size=253` และ `mqtt.msgtype=13`

กรณีนี้แสดงว่า model confidence ไม่ใช่ evidence ที่เพียงพอ Candidate ต้องผ่าน known-negative check และ score delta ต้องสอดคล้องกับสมมติฐาน

## Finding 3 — Structural completion ปิดช่องว่างแบบแถวเดียว

การตรวจ SYN-flood positives พบว่า stream 0–599 ถูกครอบคลุม 599 streams และขาด stream 194 เพียง stream เดียว ภายใน stream 194 มี normal template 9 packets และมี packet ส่วนเกินเพียง `Id=9816` การเพิ่มแถวนี้ทำให้ Public F1 เพิ่มจาก `0.96193` เป็น `0.96230`

Structural reasoning มี precision สูงกว่า broad anomaly search เพราะไม่ได้อาศัยเพียงความแปลกของ feature แต่ใช้ความครบถ้วนของ family และตำแหน่ง packet ใน stream

## Finding 4 — Residual payload twin เพิ่ม Public score

Residual ranking พบ packet ขนาด frame 189 bytes, TCP payload 135 bytes และ window 5738 ใน stream ที่มี attack fraction สูง การเพิ่ม `Id=1145` ทำให้ Public F1 เพิ่มจาก `0.96230` เป็น `0.96267`

`Id=5244` มีทุก feature นอกจาก Id เหมือน `Id=1145` จึงถูกบันทึกเป็น candidate ถัดไป แต่ไม่ได้ส่งเพราะ quota หมด การรักษา candidate เป็นไฟล์แยกจาก immutable baseline ทำให้ตรวจ changed Id และ checksum ได้ตรง

## Finding 5 — PCAP support ต้องมี context และ normal falsifier

สแกน attack PCAP ครบ 313/313 ไฟล์ ประมาณ 30.4 GB และ 215.6 ล้าน TCP packets พร้อมสแกน normal PCAP ครบ 49/49 ไฟล์ ประมาณ 7.0 GB และ 45.4 ล้าน TCP packets ระบบ hash หลายระดับตั้งแต่ `tcp_shape`, `packet`, `packet_stream`, `packet_rtt` ถึง `packet_full`

Candidate `Id=8150` มี attack support ระดับ packet shape และไม่พบใน normal subset ที่สแกนระหว่างทดลอง แต่ไม่มี full/RTT context เมื่อส่งจริง Public F1 ลดจาก `0.96230` เป็น `0.96196` จึงถูกยกเลิกทันที ผลนี้ชี้ว่าความเหมือนระดับ packet เดี่ยวไม่พอ ต้องใช้ flow หรือ transaction context

> Key takeaway — Evidence pipeline ต้องหักล้างสมมติฐานได้ ไม่ใช่สะสมเหตุผลสนับสนุน candidate อย่างเดียว

## รูปแบบในหลักฐาน

| Theme | Observation | Implication |
|---|---|---|
| Protocol semantics | กฎ TCP/MQTT แยก attack family ได้ชัด | ใช้เป็น high-precision anchors |
| Stream structure | Id=9816 เติม family ที่ขาดเพียงแถวเดียว | structural completion มี value สูง |
| PCAP evidence | Exact matches 422 แถวอยู่ใน positives เดิมทั้งหมด | สนับสนุน precision แต่ไม่เพิ่ม recall |
| Falsification | Id=8150 ทำ Public score ลด | packet-shape support เดี่ยวไม่เพียงพอ |

## ผลการทดลองแบบควบคุม

| รอบ | Public F1 | Private F1 | บทเรียน |
|---|---:|---:|---|
| First submission | 0.54898 | 0.56584 | detector เริ่มต้นยังไม่สมดุล |
| Protocol rules | 0.93152 | 0.93907 | domain rules ให้ gain ใหญ่ |
| Broad novelty pair | 0.91143 | 0.92637 | rare-normal ทำ false positives สูง |
| Rollback control | 0.95649 | 0.96648 | ตัดกลุ่มเสี่ยงแล้ว score ฟื้น |
| PUBLISH probe | 0.95834 | 0.96856 | capture family เพิ่ม recall |
| PUBLISH complete | 0.96193 | — | precision-first baseline |
| + Id=9816 | 0.96230 | 0.97198 | structural hypothesis สำเร็จ |
| + Id=8150 | 0.96196 | 0.97198 | packet-shape hypothesis ล้มเหลว |
| v8 micro best | 0.96193 | 0.97232 | Private ดีกว่า Public-best |
| + Id=1145 | 0.96267 | 0.97198 | Public-best selected file |

## ผลกระทบและการตีความ

### F1 ต้องการ candidate precision สูง

เมื่อ baseline F1 สูง การเพิ่ม positive predictions จะช่วยก็ต่อเมื่อ precision ของกลุ่ม residual สูงกว่าจุด break-even ซึ่งประเมินไว้ราว 0.486 ดังนั้น broad candidate sets มี expected loss แม้ anomaly score สูง การทดลอง Monte Carlo 20,000 รอบและ conservative stress cases ใช้เป็น guardrail แต่ไม่ถูกนำไปอ้างแทนคะแนน Kaggle

### Public leaderboard มี sampling variance

ไฟล์ `v8_micro_best` ได้ Private `0.97232` สูงกว่า selected file `0.00034` แม้ Public ต่ำกว่า `0.00074` แสดงว่า Public split 50% มี noise การเลือกโมเดลจาก Public สูงสุดเพียงอย่างเดียวทำให้เลือกไฟล์ที่ไม่ได้ Private สูงสุด

### External data มี domain shift

โมเดลที่เรียน external attack captures แยก source จาก competition normal ได้ง่าย แต่ส่วนหนึ่งมาจาก TCP stack และ capture environment ไม่ใช่ attack semantics เมื่อย้อนกลับมา competition test ความน่าเชื่อถือลดลง External data จึงใช้เป็น supporting evidence ไม่ใช่ label oracle

# ข้อเสนอแนะ

แนวทางต่อไปควรขยาย context โดยยังรักษา precision gate และ reproducibility ของระบบเดิม

1. **เปลี่ยนจาก packet เป็น flow.** สร้าง inter-arrival time, packet direction, rolling packet/byte counts, TCP state transitions, SYN/ACK ratio และ burstiness
2. **สร้าง MQTT transaction context.** แปลงลำดับ CONNECT → CONNACK → PUBLISH/SUBSCRIBE เป็น sequence features เพื่อแยก valid-looking attack จาก normal transaction
3. **ใช้ group-held-out validation.** แบ่ง fold ตาม capture file หรือ session รายงาน mean, standard deviation และ worst-fold F1 หลีกเลี่ยง random packet split
4. **ทำ rule–model ensemble.** ให้ protocol rules เป็น high-precision anchors แล้วใช้ CatBoost/LightGBM หรือ sequence model เสริมเฉพาะ residual candidates
5. **บังคับ candidate gate.** Candidate ต้องมี attack support, ไม่ชน normal corpus, ผ่าน hard negatives, ผ่านหลาย grouped folds และมี expected precision สูงกว่า F1 break-even
6. **เก็บ baseline แบบ immutable.** ทุกเวอร์ชันต้องมี changed Id list, positive count, SHA-256 และ submission reference

## ลำดับงานที่แนะนำ

ระยะที่หนึ่งสร้าง flow table จาก source PCAP พร้อม capture/session groups ระยะที่สองฝึก grouped models และ calibrate threshold จาก out-of-fold predictions ระยะที่สามวิเคราะห์ residual candidates เทียบ current baseline ระยะที่สี่ส่ง controlled probe เฉพาะ homogeneous family ที่ผ่านทุก gate

## สรุป

ผลสำเร็จของโครงการมาจากการออกแบบกระบวนการตัดสินใจ ไม่ใช่ความซับซ้อนของ model เพียงอย่างเดียว Protocol rules ให้ anchors ที่อธิบายได้ Structural analysis ช่วยปิดช่องว่าง PCAP audit ใช้ยืนยันและหักล้างสมมติฐาน และ controlled submissions ทำหน้าที่เป็นการทดลองที่มี hypothesis ชัดเจน

ไฟล์ที่เลือกได้ Public `0.96267` และ Private `0.97198` สูงกว่า baseline ผู้จัดมาก ขณะเดียวกัน Public–Private gap ยืนยันว่ารอบต่อไปควรลงทุนกับ grouped validation และ flow context มากกว่าการไล่ Public score

# ภาคผนวก

## กฎตรวจจับฉบับย่อ

| Rule | เงื่อนไข | เป้าหมาย |
|---|---|---|
| Unseen window | window ไม่อยู่ใน Normal | attack stack novelty |
| New packet shape | frame+window ใหม่, ไม่ใช่ PUBLISH | malformed/attack packet |
| SYN flood | 54 bytes, win 512, SYN=1, ACK=0 | TCP SYN flooding |
| Dictionary CONNECT | type 1, keep-alive 60/3600 | dictionary attack |
| Invalid subscription | type 8/9 | SUBSCRIBE/SUBACK attack |
| Publish signature | type 3, mqtt.len 19/44 | publish attack |
| PINGRESP exclusion | 56 bytes, win 253, type 13 | hard false positive |

## Reproducibility

สร้าง deterministic rule submission:

```bash
python outputs/predict_final_model.py \
  --train data/X_train.csv \
  --test data/X_test.csv \
  --output outputs/submission_reproduced.csv
```

ไฟล์ที่เลือกคือ `outputs/submission_current_best_96267.csv` จำนวน 10,000 rows, 2,811 positives, SHA-256 `2fe54d9dd8fc524d605fb0115941e896c86d09a6be5485d1ab626f66375c03a4`, Kaggle reference `54808193`

## แหล่งข้อมูลและ artifacts

- เอกสารโจทย์ `SuperAI6-โจทย์-HackathonOnline.pdf`
- `outputs/predict_final_model.py` — deterministic detector
- `outputs/offline_benchmark_report.md` — Monte Carlo และ sensitivity analysis
- `outputs/pcap_attack_shape_support.csv` — attack PCAP multi-profile support
- `outputs/pcap_normal_shape_support.csv` — normal falsification corpus
- `outputs/strong_machine_handoff.md` — งานต่อสำหรับเครื่องแรง
- Kaggle final submission history และ Private leaderboard ตรวจเมื่อ 18 กรกฎาคม 2569

