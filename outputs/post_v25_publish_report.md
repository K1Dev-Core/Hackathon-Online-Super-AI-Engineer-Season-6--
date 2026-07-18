# Post-v25 Publish Candidate Report

## สถานะล่าสุด

`submission_v25_stream2_plus_stream4_payload.csv` ได้ Public `0.96749` /
Private `0.97611`. `v26` เพิ่ม CONNECT `Id=4550` แล้ว Private ลดเป็น `0.97578`;
ตัด CONNECT ทั้งหมดออกจากชุดใหม่.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v25 | ระดับ |
|---:|---|---:|---:|---|
| 1 | `submission_v27_stream3_5_payload.csv` | 2,854 | 10 payload rows | แนะนำสุด |
| 2 | `submission_v28_publish_payload_cluster.csv` | 2,871 | 27 payload rows | โหด |
| 3 | `submission_v29_all_high_fraction_payload.csv` | 2,881 | 37 payload rows | สุดโหด |

## เหตุผล

- v25 ยืนยันว่าการเติม MQTT payload ใน high-positive streams ทำคะแนนจริงทั้งสองฝั่ง.
- v27 ใช้ streams 3 และ 5 ที่มี positive fraction `0.7606` และ `0.8070`.
- v28 เพิ่ม publish rows จาก streams positive fraction `0.75+`.
- v29 รวม payload ทั้งหมด แต่ไม่รวม MQTT CONNECT ซึ่ง v26 พิสูจน์แล้วว่าเสี่ยง.
- Candidate ใหม่ยังไม่มี Kaggle confirmation. เพิ่ม TP Public คาดประมาณ `+0.00037`
  ต่อแถว; TP Private คาดประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v27_stream3_5_payload.csv` เป็น next controlled aggressive file.
ใช้ `v29` ถ้าต้องการ maximum upside โดยยอมรับความเสี่ยง.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
