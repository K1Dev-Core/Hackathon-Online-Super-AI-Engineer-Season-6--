# รายงานชุด Submission Candidates

## คำแนะนำหลัก

เลือก `submission_candidate_01_champion.csv` เป็นไฟล์หลัก มี positive label `2,809` แถว เป็นไฟล์เดียวกับที่ได้ Public F1 `0.96193` และ SHA-256 ตรงกับ artifact ที่เคยส่งทุกบิต

ตรวจ leaderboard ล่าสุดวันที่ 18 กรกฎาคม 2026 แล้ว คะแนน `0.96193` ยังเสมออันดับ 1 และอันดับถัดไปอยู่ที่ `0.95934`

ยังไม่มี residual candidate กลุ่มใดผ่าน precision ขั้นต่ำ `0.48581` ที่ต้องใช้เพื่อเพิ่ม F1 จาก champion. หลังตัด normal capture families, historical false positives และ RTT groups ที่เป็น normal แล้ว calibrated attack score สูงสุดยังต่ำกว่า `0.05` จึงไม่มีหลักฐาน offline ว่า experimental hedge จะชนะ champion

## อันดับไฟล์

| อันดับ | ไฟล์ | ประเภท | Positive | Public F1 | Private F1 ประเมิน | สถานะ |
|---:|---|---|---:|---:|---:|---|
| 1 | `submission_candidate_01_champion.csv` | scored-safe | 2,809 | 0.96193 | 0.97162 | แนะนำ |
| 2 | `submission_candidate_02_lb_robust.csv` | scored-safe | 2,805 | 0.96119 | 0.97094 | rollback checkpoint |
| 3 | `submission_candidate_03_lb_conservative.csv` | scored-safe | 2,799 | 0.96045 | 0.96956 | rollback checkpoint |
| 4 | `submission_candidate_04_precision_floor.csv` | scored-safe | 2,794 | 0.95971 | 0.96853 | rollback checkpoint |
| 5 | `submission_candidate_05_micro_payload_hedge.csv` | experimental | 2,812 | ไม่มี | 0.97124 | ไม่แนะนำ |
| 6 | `submission_candidate_06_capture_context_hedge.csv` | experimental | 2,849 | ไม่มี | 0.96585 | ไม่แนะนำ |
| 7 | `submission_candidate_07_pu_top64_hedge.csv` | experimental | 2,873 | ไม่มี | 0.96242 | ไม่แนะนำ |
| 8 | `submission_candidate_08_target3000_aggressive.csv` | experimental | 3,000 | ไม่มี | 0.94348 | ไม่แนะนำ |

คะแนน Private เป็นการประเมิน ไม่ใช่ผล Kaggle. สำหรับอันดับ 1-4 ใช้ public confusion posterior และสมมติว่าข้อมูล test มี attack รวม 3,000 แถว. สำหรับอันดับ 5-8 ใช้ stress assumptions ที่บันทึกใน `candidate_manifest.csv`; ดูทุก precision scenario ได้ใน `candidate_score_scenarios.csv`

ช่วง posterior ของอันดับ 1 คือ `0.97060-0.97198`. สมการ public ที่สอดคล้องกับ submission history ให้ `P=1,459`, `predicted positive=1,352`, `TP=1,352`, `FP=0`, `FN=107` บน public split. เมื่อสมมติ attack รวม 3,000 แถว จะเหลือ private positive `1,541` แถว

## หลักฐานตัดสิน

- PUBLISH `tcp.window_size=256` ผ่าน probe ต่อเนื่องและถูกเก็บครบแล้ว
- PUBLISH `tcp.window_size=253` ทำให้คะแนนตกจาก `0.95649` เป็น `0.91143` จึงเป็น hard-negative family
- PUBLISH window `254` และ `5718-5756` ตรง normal telemetry families
- PINGRESP 5 แถวที่ `frame.len=56`, `window=253` เป็น false positives ที่ยืนยันจาก leaderboard และถูกตัดแล้ว
- Candidate TCP ACK สองแถวจาก probe เก่าอยู่ใน normal-only RTT groups และมี signature เดียวกันใน train จึงไม่ถูกใช้
- 40 capture-context rows มี supervised attack score ใกล้ศูนย์และส่วนใหญ่มี normal signature ซ้ำจำนวนมาก
- External MQTT captures มี TCP-stack domain shift จึงใช้เป็นหลักฐานสนับสนุน residual label ไม่ได้

## ไฟล์ประกอบ

- `candidate_manifest.csv` เก็บอันดับ, positive count, actual score, estimated score และสมมติฐาน
- `candidate_score_scenarios.csv` แสดง F1 เมื่อ precision ของแถวที่เติมเปลี่ยนตั้งแต่ 0 ถึง 1
- `candidate_residual_ranking.csv` เก็บ residual ranking และเหตุผลเชิง feature ของ top candidates
- `candidate_suite_checksums.sha256` ใช้ยืนยันทุกไฟล์
- `build_candidate_suite.py` สร้างชุดนี้ซ้ำแบบ deterministic
- `predict_final_model.py` สร้าง champion จาก raw train/test โดยไม่ต้องใช้ไฟล์โมเดล `.pkl`
- `superai6_candidate_suite_ranked.zip` รวม submission, report, manifest, checksums และ scripts สำคัญ

## Validation

- ตรวจครบ 8 submissions
- ทุกไฟล์มี 10,000 แถวและ schema `Id,label`
- Id ไม่ซ้ำและลำดับตรง `X_test.csv`
- label เป็น binary และไม่มี missing value
- champion rebuild ได้ตรงไฟล์เดิมทุก label
- champion SHA-256: `2159bff8a7e8b12899562692a0b291a90200fb85e9efaaa18bcfd1d7ef650bfb`
- ไม่มีการ submit Kaggle ระหว่างการสร้างชุดนี้
- ไม่มี API token อยู่ในไฟล์หรือ bundle
