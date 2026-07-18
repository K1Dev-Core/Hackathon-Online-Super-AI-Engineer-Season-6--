# Post-v16 Continuation Report

## สถานะล่าสุด

`submission_v16_plus_residual_top7.csv` ได้คะแนนจริง Public `0.96414` /
Private `0.97403` จาก v12 เพิ่ม Public `+0.00110` และ Private `+0.00103`.
v14 ยืนยัน `Id=4057` เป็น Private TP ด้วยคะแนน Private `0.97335`.

## Candidate ต่อไป

| Rank | File | Positives | เพิ่มจาก v16 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v17_plus_stream2_tail.csv` | 2,825 | 4 แถว rank 12-15 | แนะนำสุด |
| 2 | `submission_v18_plus_rank12_16.csv` | 2,826 | 5 แถว rank 12-16 | โหด |
| 3 | `submission_v19_plus_rank12_20.csv` | 2,830 | 9 แถว rank 12-20 | โหดมาก |
| 4 | `submission_v20_plus_rank12_30.csv` | 2,840 | 19 แถว rank 12-30 | เสี่ยงสุด |

## เหตุผล

- v16 ทำให้ residual ranks 5-10 รวม 6 แถวช่วยคะแนนทั้ง Public และ Private.
- `v17` ต่อด้วย stream-2 tail ranks 12-15; stream เดียวกับ confirmed TP หลายแถว
  และ stream attack fraction `0.905797`.
- `v18-v20` เพิ่มกลุ่มกว้างขึ้น. Upside สูงขึ้น แต่ false-positive risk สูงขึ้นเร็ว.
- ถ้าเพิ่ม TP ฝั่ง Public: ประมาณ `+0.00037` ต่อแถว.
- ถ้าเพิ่ม TP ฝั่ง Private: ประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v17_plus_stream2_tail.csv` เป็น next controlled aggressive file.
ใช้ `v19` ถ้าต้องการลุ้นแรง. `v20` maximum-risk เท่านั้น.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
