# ชุดเอกสารภาษาไทยสำหรับนำเสนอ

## ไฟล์หลัก

| ไฟล์ | ใช้เมื่อ | รายละเอียด |
|---|---|---|
| `SuperAI6_IoT_Attack_Detection_Design_Report_TH.docx` | ส่งรายงาน/แก้ไขใน Word | สร้างจาก retained Design Report template, 10 หน้า |
| `SuperAI6_IoT_Attack_Detection_Design_Report_TH.pdf` | อ่านหรือส่งกรรมการ | Design Report ที่ render ภาษาไทยแล้ว |
| `SuperAI6_IoT_Attack_Detection_Report_TH.pdf` | อ่านเชิงเทคนิครายละเอียด | รายงานเต็ม 22 หน้า พร้อมกฎ การทดลอง และ reproducibility |
| `SuperAI6_IoT_Attack_Detection_Report_TH.md` | แก้เนื้อหาต้นฉบับ | canonical technical content |
| `../presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pptx` | พรีเซนต์ | 17 slides, 16:9, speaker notes ฝังในไฟล์ |
| `../presentation/SuperAI6_IoT_Attack_Detection_Presentation_TH.pdf` | เปิดสำรอง | PDF ที่ตรวจ Thai glyph และ layout แล้ว |
| `SuperAI6_Presentation_Speaker_Notes_TH.md` | ซ้อมพูด | script แยกตาม slide |

## ลำดับนำเสนอ 10 นาที

ใช้ครบ 17 slides เวลาประมาณ 30–40 วินาทีต่อหน้า:

1. ปัญหา Normal-only และเป้าหมาย F1
2. Attack landscape และ feature layers
3. Core insight กับ pipeline
4. Rule engine และ precision corrections
5. Structural completion และ score progression
6. PCAP evidence กับ falsification cases
7. Public–Private gap และผลสุดท้าย
8. Negative results, next work และ Q&A

## ลำดับนำเสนอ 5 นาที

เลือก slides `1, 2, 5, 6, 7, 9, 10, 11, 13, 14, 17` รวม 11 หน้า เน้นประโยคหลัก:

- Train มี Normal เท่านั้น จึงต้องใช้ one-class anomaly detection
- Protocol rules เป็น high-precision anchors
- Stream structure เพิ่ม `Id=9816` และทำคะแนนดีขึ้น
- PCAP support ต้องมี normal falsifier และ context
- Public-best ไม่ใช่ Private-best เสมอ
- ผลสุดท้าย Public `0.96267`, Private `0.97198`

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
- `outputs/submission_current_best_96267.csv` สำหรับ exact scored artifact

## หมายเหตุการแก้ไข

PPTX ใช้ข้อความเป็น transparent PNG layers เพื่อรับประกัน Thai rendering ข้าม LibreOffice/PowerPoint ส่วน speaker notes ยังเป็นข้อความจริง แก้เนื้อหาใน `tools/generate_slides.js` แล้วรัน generator ใหม่

