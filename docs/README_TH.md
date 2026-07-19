# ชุดเอกสารภาษาไทยสำหรับนำเสนอ

## ไฟล์หลัก

| ไฟล์ | ใช้เมื่อ | รายละเอียด |
|---|---|---|
| `SuperAI6_IoT_Attack_Detection_Design_Report_TH.docx` | ส่งรายงาน/แก้ไขใน Word | สร้างจาก retained Design Report template, 10 หน้า |
| `SuperAI6_IoT_Attack_Detection_Design_Report_TH.pdf` | อ่านหรือส่งกรรมการ | Design Report ที่ render ภาษาไทยแล้ว |
| `SuperAI6_IoT_Attack_Detection_Report_TH.pdf` | อ่านเชิงเทคนิครายละเอียด | รายงานเต็ม 22 หน้า พร้อมกฎ การทดลอง และ reproducibility |
| `SuperAI6_IoT_Attack_Detection_Report_TH.md` | แก้เนื้อหาต้นฉบับ | canonical technical content |
| `SuperAI6_IoT_Attack_Detection_Report_TH.html` | เปิดผ่าน browser | รายงาน HTML ที่อธิบาย selected offline_02 artifact โดยตรง |
| `SuperAI6_IoT_Attack_Detection_Technical_DeepDive_TH.md` | แชร์ความรู้ | technical deep dive: data, features, rules, models, tuning และ validation |
| `SuperAI6_IoT_Attack_Detection_Technical_DeepDive_TH.html` | เปิดผ่าน browser | technical deep dive พร้อม code, tables และ references |
| `../presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pptx` | พรีเซนต์ | 17 slides, 16:9, speaker notes ฝังในไฟล์ |
| `../presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pdf` | เปิดสำรอง | PDF ที่ตรวจ Thai glyph และ layout แล้ว |
| `../presentation/SuperAI6_IoT_Attack_Detection_Offline02_Presentation_TH.pptx` | พรีเซนต์ไฟล์ที่เลือก | 11 slides จาก Black and Gray Gradient template, อธิบาย offline_02, เทคนิค และคะแนน Private/Public |
| `../presentation/SuperAI6_IoT_Attack_Detection_Offline02_Presentation_TH.pdf` | เปิดสำรอง | PDF ที่ render จาก PPTX และตรวจ layout แล้ว |
| `SuperAI6_IoT_Attack_Detection_Offline02_Speaker_Notes_TH.md` | ซ้อมพูด | คำพูดภาษาไทยแบบเป็นธรรมชาติ พร้อมข้อมูลไฟล์ เทคนิค code และข้อควรระวังเรื่อง score |
| `SuperAI6_IoT_Attack_Detection_Offline02_Slide_Image_Guide_TH.md` | เตรียมภาพ | อธิบายครบ 11 สไลด์ว่าควรแคปภาพอะไร วางตรงไหน ใช้ caption ใด และควรหลีกเลี่ยงอะไร |
| `SuperAI6_IoT_Attack_Detection_Offline02_Slide_Content_Expanded_TH.md` | เติมเนื้อหาสไลด์ | เนื้อหาขยายครบ 11 หน้า แยกข้อความบนสไลด์ คำอธิบาย เทคนิค โค้ด ตัวอย่างพูด และเวอร์ชันสั้น |
| `../presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.html` | พรีเซนต์ผ่าน browser | ไฟล์เดียวจบ 12 slides มี notes, keyboard, fullscreen, touch และ print/PDF |
| `SuperAI6_Presentation_Speaker_Notes_TH.md` | ซ้อมพูด | script แยกตาม slide |
| `SuperAI6_Slide_Handoff_TH.md` | ส่งให้ AI ทำสไลด์ต่อ | brief ครบ 12 slides, code จริง, score, references และ checklist |

## ลำดับนำเสนอ 10 นาที

ใช้ HTML deck ครบ 12 slides เวลาประมาณ 30–40 วินาทีต่อหน้า:

1. ปัญหา Normal-only และเป้าหมาย F1
2. Feature layers และสมมติฐาน
3. Pipeline และ rule engine
4. โค้ดจริงและ hard negatives
5. Case studies และ score evidence
6. Reproducibility, limitations, references และ Q&A

## ลำดับนำเสนอ 5 นาที

เลือก slides `1, 2, 4, 5, 7, 8, 9, 10, 11, 12` รวม 10 หน้า เน้นประโยคหลัก:

- Train มี Normal เท่านั้น จึงต้องใช้ one-class anomaly detection
- Protocol rules เป็น high-precision anchors
- Stream structure เพิ่ม `Id=9816` และทำคะแนนดีขึ้น
- PCAP support ต้องมี normal falsifier และ context
- Public-best ไม่ใช่ Private-best เสมอ
- ไฟล์ที่เลือก upload: `submission_offline_02_hedge_payload132.csv`, Public `0.96267`, Private `0.97198`

## Demo สำหรับ Q&A

```bash
python outputs/predict_final_model.py \
  --train data/X_train.csv \
  --test data/X_test.csv \
  --output outputs/submission_reproduced.csv
```

จุดที่ควรเปิดอธิบาย:

- `outputs/predict_final_model.py` สำหรับ protocol rules
- `outputs/offline_benchmark_report.md` สำหรับ Monte Carlo/stress test
- `outputs/pcap_attack_shape_support.csv` และ `outputs/pcap_normal_shape_support.csv` สำหรับ evidence gate
- `outputs/offline_benchmark_candidates/submission_offline_02_hedge_payload132.csv` สำหรับไฟล์ที่เลือก upload

## หมายเหตุการแก้ไข

PPTX ใช้ข้อความเป็น transparent PNG layers เพื่อรับประกัน Thai rendering ข้าม LibreOffice/PowerPoint ส่วน speaker notes ยังเป็นข้อความจริง แก้เนื้อหาใน `tools/generate_slides.js` แล้วรัน generator ใหม่
