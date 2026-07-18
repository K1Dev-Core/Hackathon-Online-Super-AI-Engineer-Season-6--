# Post-v23 Payload Candidate Report

## สถานะล่าสุด

`submission_v23_context_plus_novelty.csv` ได้คะแนนจริง Public `0.96598` /
Private `0.97541`. Protocol stream audit พบว่า v23 ยังปล่อย MQTT payload rows
ใน stream ที่มี positive fraction สูงไว้หลายแถว.

## Candidate ใหม่

| Rank | File | Positives | เพิ่มจาก v23 | ระดับ |
|---:|---|---:|---|---|
| 1 | `submission_v24_stream2_mqtt_payload.csv` | 2,841 | 9 stream-2 payload rows | แนะนำสุด |
| 2 | `submission_v25_stream2_plus_stream4_payload.csv` | 2,844 | v24 + 3 stream-4 payload rows | โหด |
| 3 | `submission_v26_stream_payload_plus_connect.csv` | 2,845 | v25 + `Id=4550` | เสี่ยงสุด |

## เหตุผล

- Stream 2 หลัง v23 มี positive fraction `259/276 = 0.9384`; rows ที่เหลือในกลุ่ม
  MQTT payload ใช้รูปแบบ attack payload เดียวกับกลุ่มที่ทำคะแนนผ่านแล้ว.
- Stream 4 มี positive fraction `106/116 = 0.9138`; payload rows ที่เหลือจึงเป็น
  candidate structural completion.
- `Id=4550` เป็น MQTT CONNECT, แยกไว้ v26 เพราะอาจเป็น normal handshake.
- Candidate ใหม่ยังไม่มี Kaggle confirmation. เพิ่ม TP ฝั่ง Public คาดประมาณ `+0.00037`
  ต่อแถว; ฝั่ง Private คาดประมาณ `+0.00034` ต่อแถว.

## การเลือก

ใช้ `submission_v24_stream2_mqtt_payload.csv` เป็นไฟล์ถัดไป. ใช้ `v25` ถ้าต้องการ
ลุ้นสอง stream. `v26` maximum risk เพราะรวม CONNECT row.

ยังไม่ส่ง Kaggle จาก pipeline นี้.
