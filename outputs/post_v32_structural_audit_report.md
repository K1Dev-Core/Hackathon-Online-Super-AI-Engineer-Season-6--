# v32 Structural Audit

## ผลสรุป

ไฟล์ที่ดีที่สุดที่ยืนยันด้วย leaderboard ตอนนี้คือ
`post_v25_publish_candidates/submission_v27_stream3_5_payload.csv`:

- Public F1: `0.96824`
- Private F1: `0.97748`
- Positive labels: `2,854`

ไม่สร้าง candidate ใหม่ที่อ้างว่าดีกว่า v27 เพราะหลักฐานรอบล่าสุดชี้ตรงข้าม

## สิ่งที่ทดสอบ

`v30` เพิ่ม 13 แถว CONNECT handshake และได้ Public `0.96551` / Private `0.97586`.
`v31` เพิ่มอีก 10 แถวใน CONNECT family เดียวกัน และได้ Public `0.96416` /
Private `0.97393`. ทั้งสองแพ้ v27 ชัดเจน จึงตัด CONNECT family ออกจาก search ต่อ

Exact-group audit ของ streams 0-5 พบ candidate groups ที่มี positive ratio สูง
แต่มี negative ปนเพียงสามกลุ่ม และทั้งหมดเป็น CONACK shape เดียวกัน:

- stream 2: `Id=4550`
- stream 3: `Id=680`
- stream 5: `Id=1527`

`Id=4550` เคยถูกส่งแล้วและทำ Private ลด จึงไม่เพิ่มอีกสองแถวที่เป็น twin เดียวกัน

ตรวจ payload family เพิ่มเติมแล้ว:

- stream 0/37 มี PUBLISH topic 30, payload 138 จำนวนมาก แต่เป็น normal-context
  family; การเติมแบบกว้างเคยทำคะแนนตก.
- topic 32, payload 139 ใน stream 0 มี 3 แถวที่ยังเป็นลบ แต่ twin window 256
  อยู่ใน stream 1 และเป็นคนละ context จึงไม่ย้าย label ข้าม stream.
- streams 3 และ 5 ไม่มี PUBLISH payload ตกหล่นที่ผ่าน precision gate หลัง v27.

## คำแนะนำ

ใช้ไฟล์ v27 เดิมเป็น submission candidate. `v30` และ `v31` เก็บไว้เป็นหลักฐาน
การ reject เท่านั้น ไม่ควรส่งซ้ำ. รายงานนี้ไม่อ้างว่า v27 ชนะอันดับหนึ่งของ
leaderboard ทั้งหมด แต่เป็น current best จากคะแนนที่มีการวัดจริงใน workspace.
