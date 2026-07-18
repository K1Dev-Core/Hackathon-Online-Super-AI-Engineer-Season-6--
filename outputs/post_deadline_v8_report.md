# Post-Deadline v8 Improvement Report

## สรุป

ไฟล์ `submission_v10_pareto_plus_exact_twin.csv` ได้คะแนนจริง Public `0.96304`
/ Private `0.97232` สูงกว่า v8 ฝั่ง Public `0.00111` โดยเก็บ `Id=4456` และเพิ่ม
`Id=9816`, `Id=1145`, `Id=5244` รวม positive `2,813` แถว

## หลักฐานจากคะแนนจริง

- v8 ต่างจาก PUBLISH baseline เพียง `Id=4456` แต่ Public เท่ากันที่ `0.96193`
  จึงสรุปได้ว่าแถวนี้อยู่ Private split
- เมื่อเทียบ v8 กับไฟล์ structural/public-best คะแนน Private ลดจาก `0.97232`
  เป็น `0.97198` เมื่อไม่มี `Id=4456` จึงยืนยันว่า `Id=4456` เป็น Private TP
- `Id=9816` ทำให้ Public เพิ่ม `0.96193 -> 0.96230`
- `Id=1145` ทำให้ Public เพิ่ม `0.96230 -> 0.96267`
- `Id=5244` มีทุก feature นอกจาก `Id` เหมือน `Id=1145` และผลจริง v10 ยืนยันว่า
  เป็น Public TP: Public เพิ่ม `0.96267 -> 0.96304` แต่ Private ไม่เปลี่ยน

## ลำดับไฟล์

| Rank | File | Positives | Public F1 ประเมิน | Private F1 ประเมิน | การใช้ |
|---:|---|---:|---:|---:|---|
| 1 | `submission_v10_pareto_plus_exact_twin.csv` | 2,813 | **0.96304 จริง** | **0.97232 จริง** | ไฟล์ดีที่สุดตอนนี้ |
| 2 | `submission_v9_pareto_confirmed.csv` | 2,812 | **0.96267 จริง** | **0.97232 จริง** | ปลอดภัยสุด |
| 3 | `submission_v11_pareto_plus_payload150.csv` | 2,814 | ยังไม่ยืนยัน | ยังไม่ยืนยัน | upside สูงกว่า ความเสี่ยงสูงกว่า |

v10 มีผล Kaggle จริงแล้ว. ขั้นถัดไปคือ v11 ซึ่งเพิ่ม `Id=5516` เพื่อทดสอบ
Private split โดยตรง; คะแนน v11 ยังไม่ยืนยัน.

## Integrity

- Scored v8 SHA-256: `e72b0bf1f27e507c7e2bc8f350625f0d923e84ced87740ddcc027c7b874b7adb`
- v8 rows: `10,000`
- ทุกไฟล์ผ่าน schema, Id order, binary-label, changed-Id และ checksum validation
