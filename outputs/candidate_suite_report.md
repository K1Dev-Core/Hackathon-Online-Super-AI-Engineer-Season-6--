# รายงานชุด Submission Candidates

## คำแนะนำหลัก

เลือก `submission_rank1_structural_plus1.csv` เป็น challenger ที่ดีที่สุดสำหรับการส่งครั้งถัดไป ไฟล์นี้ต่อยอดจาก champion ที่ได้ Public F1 `0.96193` โดยเพิ่มเพียง `Id=9816` ทำให้มี positive label `2,810` แถว

leaderboard snapshot ที่บันทึกไว้แสดงว่า `0.96193` เสมออันดับ 1 และคะแนนถัดไปคือ `0.95934` โดยรายงานนี้ไม่อ้างว่าเป็นสถานะสดล่าสุด

ถ้าต้องการไฟล์ที่มีผล Kaggle ยืนยันแล้วโดยไม่รับความเสี่ยงใหม่ ให้ใช้ `submission_candidates/submission_candidate_01_champion.csv` ซึ่งเหมือน artifact เดิมทุกบิต

## อันดับไฟล์

| อันดับ | ไฟล์ | Positive | Public F1 | Private F1 ประเมิน | สถานะ |
|---:|---|---:|---:|---:|---|
| 1 | `submission_rank1_structural_plus1.csv` | 2,810 | ยังไม่ส่ง | 0.97179 | แนะนำ: structural challenger |
| 2 | `submission_candidate_01_champion.csv` | 2,809 | 0.96193 | 0.97162 | fallback ที่มีคะแนนจริง |
| 3 | `submission_candidate_02_lb_robust.csv` | 2,805 | 0.96119 | 0.97094 | rollback checkpoint |
| 4 | `submission_candidate_03_lb_conservative.csv` | 2,799 | 0.96045 | 0.96956 | rollback checkpoint |
| 5 | `submission_candidate_04_precision_floor.csv` | 2,794 | 0.95971 | 0.96853 | rollback checkpoint |
| 6 | `submission_candidate_05_micro_payload_hedge.csv` | 2,812 | ยังไม่ส่ง | 0.97124 | ไม่แนะนำ |
| 7 | `submission_candidate_06_capture_context_hedge.csv` | 2,849 | ยังไม่ส่ง | 0.96585 | ไม่แนะนำ |
| 8 | `submission_candidate_07_pu_top64_hedge.csv` | 2,873 | ยังไม่ส่ง | 0.96242 | ไม่แนะนำ |
| 9 | `submission_candidate_08_target3000_aggressive.csv` | 3,000 | ยังไม่ส่ง | 0.94348 | ไม่แนะนำ |

คะแนน Private เป็นค่าประเมิน ไม่ใช่ผล Kaggle โดยสมมติว่าชุด test มี attack รวม 3,000 แถวและ public/private แบ่งครึ่ง ดูสมมติฐานทุกเวอร์ชันใน `candidate_manifest.csv` และทุก precision scenario ใน `candidate_score_scenarios.csv`

## หลักฐาน Structural +1

- SYN-flood fingerprint มี 599 แถวและ 599 `tcp.stream` ไม่ซ้ำ ครอบคลุม stream `0-599` ทุกค่าจนขาดเพียง stream `194`
- Normal stream `194` ใน train มี packet template 9 แถว ส่วน test มี 10 แถว โดย 9 แถวตรง template เดิมเมื่อไม่นับค่า RTT ที่เปลี่ยนตาม capture
- แถวส่วนเกินเพียงแถวเดียวคือ `Id=9816`: PUBLISH, `frame.len=195`, `tcp.len=141`, `tcp.window_size=5728`, `mqtt.len=138`
- โครงสร้างนี้สอดคล้องกับ SYN capture ขนาด 600 แถวที่มี 599 SYN streams และ background MQTT packet หนึ่งแถวใน stream ที่ขาด
- ความเชื่อมั่น `0.98` ใน manifest เป็น structural estimate ไม่ใช่ probability ที่ calibrate จาก Kaggle

ถ้าสมมติ champion ไม่มี false positive และมี attack 3,000 แถว F1 เต็มชุดคือ `0.967120`. หาก `Id=9816` เป็น TP challenger จะเป็น `0.967298`; หากเป็น FP จะเป็น `0.966954`. จุดคุ้มของการเพิ่มแถวนี้คือโอกาสเป็น attack มากกว่า `0.48356`

ชุด benchmark ล่าสุดอยู่ใน `offline_benchmark_report.md` และ `offline_benchmark_winners.csv`. ผลจำลอง 20,000 รอบยังจัด `offline_benchmark_candidates/submission_offline_01_scoremax_structural.csv` เป็นอันดับ 1; ไฟล์นี้เหมือน `submission_rank1_structural_plus1.csv` ทุก label

## Validation

- ตรวจครบ 9 candidate submissions ทุกไฟล์มี 10,000 แถวและ schema `Id,label`
- Id ไม่ซ้ำ ลำดับตรง `X_test.csv`, label เป็น binary และไม่มี missing value
- Challenger ต่างจาก champion เพียง `Id=9816`
- Challenger SHA-256: `fa357be08880f7dbdf32e61052ad01eeae251c8706d2bc077818efaa7d9a73d7`
- Champion SHA-256: `2159bff8a7e8b12899562692a0b291a90200fb85e9efaaa18bcfd1d7ef650bfb`
- ไม่มีการ submit Kaggle ระหว่างการสร้าง challenger
- ไม่มี API token อยู่ในไฟล์หรือ bundle
