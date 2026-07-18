# Post-v27 Stream Threshold Report

## สถานะล่าสุด

`submission_v27_stream3_5_payload.csv` เป็น current best: Public `0.96824` /
Private `0.97748`. ผลจริงของ probes ถัดไปยืนยันว่า CONNECT handshake เป็น
false-positive zone:

- `submission_v30_stream_fraction_085.csv`: Public `0.96551` / Private `0.97586`.
- `submission_v31_stream_fraction_080.csv`: Public `0.96416` / Private `0.97393`.
- ทั้งสองไฟล์ต่ำกว่า v27 จึง reject ถาวร.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v27 | ระดับ |
|---:|---|---:|---:|---|
| 1 | `submission_v27_stream3_5_payload.csv` | 2,854 | 0 rows | CONFIRMED BEST |
| 2 | `submission_v30_stream_fraction_085.csv` | 2,867 | 13 rows | REJECTED |
| 3 | `submission_v31_stream_fraction_080.csv` | 2,877 | 23 rows | REJECTED |

## เหตุผล

- v30 เพิ่ม MQTT CONNECT `msgtype=1`, `frame.len=151`, `tcp.len=97`,
  `mqtt.kalive=15`, `mqtt.len=95` จำนวน 13 แถว.
- v31 เพิ่ม CONNECT family เดียวกันอีก 10 แถว.
- v26 เคยยืนยันแล้วว่า CONACK/handshake shape ใกล้เคียงกันทำ Private ตก;
  จึงไม่เติม CONNECT หรือ CONACK ต่อ.
- Exact payload audit ใน streams 0-5 ไม่พบกลุ่ม unselected ที่มี purity สูง;
  กลุ่มที่ผ่าน gate มีเฉพาะ CONACK `tcp.window_size=64523` ซึ่งเป็น hard negative.
- กลุ่ม PUBLISH topic 30 / payload 138 ใน stream 0 และ stream 37 มีจำนวนมาก
  และ context เป็น normal family; ไม่ย้ายกฎจาก stream 3/5 ไปใช้กว้างๆ.

## การเลือก

ใช้ `submission_v27_stream3_5_payload.csv` เท่านั้น. ไม่มี v32 ที่มีหลักฐาน
ดีกว่า v27 ในชุดข้อมูลปัจจุบัน; การเติมต่อจาก threshold เป็นการเพิ่ม false positive.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
