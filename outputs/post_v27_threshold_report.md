# Post-v27 Stream Threshold Report

## สถานะล่าสุด

`submission_v27_stream3_5_payload.csv` เป็น current best: Public `0.96824` /
Private `0.97748`. `v29` เพิ่ม 27 rows แล้วลดเป็น Public `0.96348` /
Private `0.97329`; กลุ่ม publish streams 6-32 มี false positives สูง.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v27 | ระดับ |
|---:|---|---:|---:|---|
| 1 | `submission_v30_stream_fraction_085.csv` | 2,867 | 13 rows | แนะนำสุด |
| 2 | `submission_v31_stream_fraction_080.csv` | 2,877 | 23 rows | โหด |

## เหตุผล

- v30 คัดเฉพาะ publish payload rows จาก streams ที่ current positive fraction >= 0.85.
- v31 ขยาย threshold เป็น >= 0.80.
- ทั้งสองตัด CONNECT และไม่ใช้ full v29 ซึ่งพิสูจน์แล้วว่าเสียคะแนน.
- Candidate ใหม่ยังไม่มี Kaggle confirmation. ต้องมองเป็น controlled probe.

## การเลือก

ใช้ `submission_v30_stream_fraction_085.csv` เป็น next file. ใช้ v31 ถ้าต้องการ
ลุ้นแรงและยอมรับ false-positive risk.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
