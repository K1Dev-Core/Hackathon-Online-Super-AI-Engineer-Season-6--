# Submission Source Bundle

Source code สำหรับสร้างไฟล์ selected:

`submission_offline_02_hedge_payload132.csv`

## เข้าโฟลเดอร์หลัก

`submission_source/offline02/`

ในโฟลเดอร์มี:

- `predict.py`: สร้าง prediction จาก `X_train.csv` และ `X_test.csv`
- `validate.py`: ตรวจ schema, จำนวนแถว, Id order และ label domain
- `requirements.txt`: dependency ของ Python
- `README.md`: วิธีรันและคำอธิบาย algorithm

## รันจาก repository root

```bash
python submission_source/offline02/predict.py \
  --train data/X_train.csv \
  --test data/X_test.csv \
  --output outputs/submission_offline_02_reproduced.csv
```

## ตรวจไฟล์

```bash
python submission_source/offline02/validate.py \
  --test data/X_test.csv \
  --submission outputs/submission_offline_02_reproduced.csv
```

ผลที่ตรวจแล้ว:

- Rows: `10,000`
- Positive labels: `2,811`
- SHA-256: `2fe54d9dd8fc524d605fb0115941e896c86d09a6be5485d1ab626f66375c03a4`

Source นี้ไม่รวม dataset, API token หรือ credential ใด ๆ
