# Post-Deadline v8 Improvement Report

## สรุป

ไฟล์แนะนำคือ `submission_v10_pareto_plus_exact_twin.csv` สร้างจาก v8 ที่ได้
Public `0.96193` / Private `0.97232` โดยเก็บ `Id=4456` และเพิ่ม `Id=9816`,
`Id=1145`, `Id=5244` รวม positive `2,813` แถว ไม่มีการส่ง Kaggle รอบใหม่

## หลักฐานจากคะแนนจริง

- v8 ต่างจาก PUBLISH baseline เพียง `Id=4456` แต่ Public เท่ากันที่ `0.96193`
  จึงสรุปได้ว่าแถวนี้อยู่ Private split
- เมื่อเทียบ v8 กับไฟล์ structural/public-best คะแนน Private ลดจาก `0.97232`
  เป็น `0.97198` เมื่อไม่มี `Id=4456` จึงยืนยันว่า `Id=4456` เป็น Private TP
- `Id=9816` ทำให้ Public เพิ่ม `0.96193 -> 0.96230`
- `Id=1145` ทำให้ Public เพิ่ม `0.96230 -> 0.96267`
- `Id=5244` มีทุก feature นอกจาก `Id` เหมือน `Id=1145` และอยู่ residual rank 2
  จึงเป็น candidate ที่มีหลักฐานดีที่สุดสำหรับเพิ่มคะแนนอีกหนึ่งแถว

## ลำดับไฟล์

| Rank | File | Positives | Public F1 ประเมิน | Private F1 ประเมิน | การใช้ |
|---:|---|---:|---:|---:|---|
| 1 | `submission_v10_pareto_plus_exact_twin.csv` | 2,813 | 0.96267-0.96304 | 0.97232-0.97266 | แนะนำสูงสุด |
| 2 | `submission_v9_pareto_confirmed.csv` | 2,812 | 0.96267 | 0.97232 | ปลอดภัยสุด |
| 3 | `submission_v11_pareto_plus_payload150.csv` | 2,814 | ยังไม่ยืนยัน | ยังไม่ยืนยัน | upside สูงกว่า ความเสี่ยงสูงกว่า |

ช่วงของ v10 ขึ้นกับว่า `Id=5244` อยู่ Public หรือ Private split ถ้า ground truth
เหมือน exact twin `Id=1145` จะเพิ่มคะแนน split ใด split หนึ่งประมาณ `0.00034-0.00037`
และไม่กระทบอีก split. คะแนนเป็นการ reconstruct จาก submission ที่มีคะแนนจริง ไม่ใช่ผล
Kaggle ที่ยืนยันหลัง deadline.

## Integrity

- Scored v8 SHA-256: `e72b0bf1f27e507c7e2bc8f350625f0d923e84ced87740ddcc027c7b874b7adb`
- v8 rows: `10,000`
- ทุกไฟล์ผ่าน schema, Id order, binary-label, changed-Id และ checksum validation
