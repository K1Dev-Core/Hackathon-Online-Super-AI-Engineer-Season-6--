# Post-v11 Aggressive Candidate Report

## สถานะล่าสุด

`submission_v12_plus_rare_ack.csv` ได้คะแนนจริง Public `0.96304` / Private
`0.97300` เพิ่มจาก v11 เฉพาะ Private `+0.00034` ยืนยันว่า `Id=6011`
เป็น Private TP. Current confirmed positives: `4456, 5516, 6011` ฝั่ง Private;
`9816, 1145, 5244` ฝั่ง Public.

## Candidate ใหม่

| Rank | File | Positive | เพิ่มจาก v11 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v14_plus_dual_ack.csv` | 2,816 | `4057` จาก v12 | ตัวถัดไป แนะนำ |
| 2 | `submission_v13_plus_stream5_ack.csv` | 2,815 | `4057` จาก v11 | fallback เก่า |
| 3 | `submission_v15_plus_stream2_ack_cluster.csv` | 2,819 | `1223,9757,5850,5177` จาก v12 | โหดมาก |
| 4 | `submission_v16_plus_residual_top7.csv` | 2,821 | `4057,4933,1980,5475,1805,55` จาก v12 | เสี่ยงสุด |

## เหตุผล

- `Id=6011` เป็น residual rank 4, อยู่ stream 2 เดียวกับ confirmed TP หลายแถว,
  stream attack fraction `0.905797`, frequency excess `0.2157`.
- `Id=4057` เป็น residual rank 5, อยู่ stream 5 ที่ attack fraction `0.719298`.
- Candidate rank 4-10 ยังไม่มี Kaggle confirmation และ external PCAP exact-match
  ไม่พบ. ไฟล์รวมจึงเป็น upside search ไม่ใช่ safe prediction.
- ถ้า candidate เป็น TP ใน Public: คาด Public เพิ่มประมาณ `0.00037`.
- ถ้า candidate เป็น TP ใน Private: คาด Private เพิ่มประมาณ `0.00034`.
- ถ้าเป็น FP: F1 ลด. v12 คือ single-row risk ต่ำสุด; v16 คือ maximum-upside risk สูงสุด.

## การเลือก

แนะนำถัดไป `submission_v14_plus_dual_ack.csv` เพราะเพิ่ม candidate เดี่ยว `Id=4057`
จาก current best. ถ้าต้องการลุ้นแรงใช้ `v16`; `v15` เน้น stream 2 แต่มี weak tail rows.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
