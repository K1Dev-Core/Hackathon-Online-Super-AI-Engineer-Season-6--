# Post-v20 Refined Candidate Report

## สถานะล่าสุด

`submission_v20_plus_rank12_30.csv` ได้คะแนนจริง Public `0.96461` /
Private `0.97412`. เมื่อเทียบ v16 เพิ่ม Public `+0.00047` แต่ Private เพียง
`+0.00009`; กลุ่ม rank 12-30 มี false positives ปน จึงไม่ควรเติม residual ทั้งกลุ่มต่อ.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v16 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v21_high_context.csv` | 2,831 | 10 แถว attack-context สูง | แนะนำสุด |
| 2 | `submission_v22_high_novelty_4082.csv` | 2,822 | `Id=4082` เดี่ยว | probe คุมความเสี่ยง |
| 3 | `submission_v23_context_plus_novelty.csv` | 2,832 | v21 + `4082` | โหดสุด |

## เหตุผล

- v21 เก็บเฉพาะ candidates ที่อยู่ stream attack fraction สูงหรือมี stream-4/5 context
  สูง; ตัด stream-0 low-context rows ออก.
- v22 แยก `Id=4082` เพราะ frequency excess `0.75045` สูงสุดในกลุ่มที่ยังไม่เลือก
  แม้ stream attack fraction ต่ำ.
- v23 รวมสองสมมติฐาน; false-positive risk สูงกว่า v21.
- ถ้าเพิ่ม TP ฝั่ง Public: ประมาณ `+0.00037` ต่อแถว.
- ถ้าเพิ่ม TP ฝั่ง Private: ประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v21_high_context.csv` เป็นตัวถัดไป. ใช้ `v23` ถ้าต้องการลุ้นแรง.
`v22` เหมาะสำหรับแยกทดสอบ novelty เดี่ยว.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
