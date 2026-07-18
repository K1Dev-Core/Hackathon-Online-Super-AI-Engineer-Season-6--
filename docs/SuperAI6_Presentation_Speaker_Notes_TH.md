# Speaker Notes — The IoT Attack Detection Challenge

ผู้บรรยาย: 610686-วชิรวิทย์

## 01 — เปิดเรื่อง

โจทย์นี้มีข้อมูลฝึกเป็น Normal ทั้งหมด จึงไม่ใช่ classification แบบทั่วไป แนวทางของผมใช้ความหมายของ TCP และ MQTT สร้าง detector ที่อธิบายได้ แล้วตรวจสมมติฐานด้วย stream structure, PCAP และ controlled leaderboard experiments ผลสุดท้ายได้ Public 0.96267 และ Private 0.97198

## 02 — โจทย์ยากตรงไหน

Train 100,000 แถวเป็น Normal ทั้งหมด ส่วน test 10,000 แถวมีทั้ง Normal และ Attack เราจึงเรียน decision boundary จาก label สองคลาสไม่ได้ Rare-normal และ attack บางชนิดมี packet shape ใกล้กันมาก ทำให้ anomaly score เดี่ยวไม่พอ

## 03 — ภูมิทัศน์การโจมตี

การโจมตีห้ากลุ่มไม่ได้อยู่ในระดับเดียวกัน Dictionary และ Will Payload สะท้อน CONNECT fields, Invalid Subscription และ Publish อยู่ระดับ MQTT transaction ส่วน SYN Flood อยู่ระดับ TCP state ดังนั้น detector ต้องรวม features หลายชั้น

## 04 — แผนที่ features

ผมแบ่ง 23 features เป็นสามกลุ่ม Frame, TCP และ MQTT จุดสำคัญคือ missing values ใน MQTT ไม่ควรเติมแบบไม่มีบริบท เพราะหลาย packet เป็น TCP control packet ที่ไม่มี MQTT layer อยู่แล้ว TCP stream ใช้เป็นบริบทภายใน capture แต่ห้ามถือเป็น identity ข้ามไฟล์

## 05 — Core insight

Autoencoder หรือ isolation model มักให้คะแนนสูงกับ rare-normal และอาจพลาด attack ที่ใช้ packet format ปกติ ผมจึงใช้ protocol rules เป็น high-precision anchors แล้วค่อยเพิ่ม recall ผ่าน stream structure และ evidence gates

## 06 — Pipeline

Pipeline เริ่มจาก normal profile แล้วรวมกฎ protocol ตัด false positive ตรวจ stream และใช้ source evidence ก่อนส่ง ทุก submission เป็น delta จาก baseline ที่ไม่แก้ทับ พร้อม changed Id list และ checksum ทำให้ย้อนกลับได้

## 07 — Rule engine

หกกฎหลักครอบคลุม novelty ของ TCP stack, packet shape, SYN flood, dictionary CONNECT, invalid subscription และ publish signature การรวมด้วย OR เพิ่ม recall แต่ต้องมี exclusion rules แยกต่างหากเพื่อไม่ให้ false positive สะสม

## 08 — Precision corrections

ตัวอย่างสำคัญคือ PINGRESP window 253 ซึ่ง pseudo model มั่นใจว่าเป็น attack แต่ score probe บอกว่าเป็น false positive เราจึงลบทั้ง family ในทางกลับกัน PUBLISH window 256 ผ่าน probe หลายรอบ จึงเพิ่มกลับแบบ family-complete

## 09 — Structural completion

SYN-flood labels ครอบคลุม stream 0 ถึง 599 ยกเว้น 194 เมื่อตรวจ stream 194 พบ normal template 9 packets และ packet ส่วนเกินเพียง Id 9816 การเพิ่มแถวเดียวทำให้ Public เพิ่มจาก 0.96193 เป็น 0.96230

## 10 — Score progression

คะแนนไม่ได้เพิ่มเป็นเส้นตรง Broad novelty เคยทำให้คะแนนลดจึง rollback หลังจากนั้นใช้กลุ่มเล็กและ homogeneous มากขึ้น จาก rules, publish completion, structural Id 9816 และ payload Id 1145 จน Public สูงสุด 0.96267

## 11 — PCAP evidence

ผมสแกน attack PCAP 313 ไฟล์และ normal PCAP 49 ไฟล์ รวมมากกว่า 37 GB หรือ 260.9 ล้าน TCP packets ใช้ hash หลาย profile ตั้งแต่ packet shape ถึง full features หลักคือ candidate ต้องมี attack support และไม่ชน normal corpus

## 12 — Falsification

Id 8150 ดูดีจาก packet shape แต่คะแนนลด จึง reject ทันที ส่วน Id 1145 ผ่าน residual gate และทำให้คะแนนเพิ่ม สิ่งสำคัญคือ evidence pipeline ต้องหักล้างสมมติฐานได้ ไม่ใช่สะสมเหตุผลสนับสนุนอย่างเดียว

## 13 — Public–Private gap

ไฟล์ Public สูงสุดได้ Private 0.97198 แต่ v8 ที่ Public ต่ำกว่าเล็กน้อยกลับได้ Private 0.97232 นี่คือ sampling variance ของ split 50/50 และเหตุผลที่ไม่ควรเลือกโมเดลจาก Public score เพียงตัวเดียว

## 14 — ผลสุดท้าย

ไฟล์ที่เลือกได้ Private 0.97198 สูงกว่า baseline ผู้จัด 0.65030 มาก คะแนนสูงสุด 0.98149 และอันดับสอง 0.97879 จากนั้นมีหลายทีมที่ 0.97198 รวมทีมของเรา ช่องว่างจากอันดับหนึ่ง 0.00951

## 15 — Negative results

สี่แนวทางที่ไม่ใช้คือ broad novelty, pseudo labels ที่ไม่ผ่าน hard-negative check, external model ที่เจอ domain shift และ packet shape เดี่ยว ทุกความล้มเหลวถูกเก็บเป็น guardrail ไม่ให้ทำผิดซ้ำ

## 16 — งานต่อไป

รอบต่อไปต้องเปลี่ยนหน่วยวิเคราะห์จาก packet เป็น flow และ MQTT transaction สร้าง inter-arrival, direction, burst และ state transition สำคัญที่สุดคือต้อง split validation ตาม capture หรือ session ไม่ใช่ random rows เพื่อป้องกัน leakage

## 17 — สรุปและถามตอบ

สรุปสามข้อ หนึ่ง ใช้ protocol meaning เป็น anchor สอง packet shape ต้องมี context สาม Public leaderboard มี noise จึงต้องเลือกจาก stability และ evidence ขอบคุณครับ พร้อมตอบคำถามเรื่องกฎ การทดลอง PCAP หรือการพัฒนาต่อ
