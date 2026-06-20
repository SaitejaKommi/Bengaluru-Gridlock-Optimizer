---
title: Traffic Violation Detection
emoji: 🚦
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---

# 🚦 AI Traffic Violation Detection System

Automated traffic violation detection powered by YOLO + EasyOCR. Upload a traffic image and the system automatically detects:

- 🚗 **Vehicles** — Cars, motorcycles, buses, trucks
- 🪖 **Helmet violations** — Motorcycle riders without helmets
- 🔒 **Seatbelt violations** — Car drivers without seatbelts
- 🏍️ **Triple riding** — 3+ riders on a single motorcycle
- 🔢 **Number plates** — License plate text via OCR

## Architecture

```
User Upload
    ↓
Vehicle Detection (YOLO)
    ↓
Helmet Detection (motorcycles)    Seatbelt Detection (cars)
    ↓                                      ↓
Number Plate Detection + EasyOCR
    ↓
Unified JSON Report + Annotated Image
```

## Quick Start (Local)

```bash
# Clone
git clone <repo-url>
cd traffic-app

# Install
pip install -r requirements.txt

# Run
uvicorn backend.app:app --host 0.0.0.0 --port 7860 --reload
# Open http://localhost:7860
```

## Docker

```bash
docker build -t traffic-violation-detector .
docker run -p 7860:7860 traffic-violation-detector
```

## Using Fine-tuned Weights

Place your trained `best.pt` files in `backend/models/`:

```
backend/models/
├── vehicle_best.pt     # Fine-tuned on IDD dataset
├── helmet_best.pt      # Fine-tuned binary: with_helmet / without_helmet
├── seatbelt_best.pt    # Fine-tuned: seatbelt / no_seatbelt
└── plate_best.pt       # Fine-tuned on Indian number plate dataset
```

The app auto-detects them. If not found, falls back to `yolov8n.pt` / `yolov8s.pt`.

## API Reference

### `GET /health`
Returns service status.

```json
{"status": "ok", "models_loaded": true}
```

### `POST /analyze`
Analyze an uploaded image.

**Request:** `multipart/form-data` with field `file` (image)

**Response:**
```json
{
  "status": "success",
  "vehicles": [
    {"id": 1, "type": "motorcycle", "confidence": 0.91, "bbox": [x1,y1,x2,y2], "triple_riding": false}
  ],
  "helmets": [
    {"vehicle_id": 1, "status": "without_helmet", "confidence": 0.87, "bbox": [...]}
  ],
  "seatbelts": [
    {"vehicle_id": 2, "status": "no_seatbelt", "confidence": 0.78, "bbox": [...]}
  ],
  "numberplates": [
    {"vehicle_id": 1, "text": "KA01AB1234", "confidence": 0.82, "ocr_confidence": 0.91, "bbox": [...]}
  ],
  "violations": [
    {"vehicle_id": 1, "type": "No Helmet", "confidence": 0.87, "description": "..."}
  ],
  "summary": {
    "total_vehicles": 3,
    "motorcycles": 1,
    "cars": 2,
    "violations_count": 2,
    "helmet_violations": 1,
    "seatbelt_violations": 1,
    "plates_read": 2
  },
  "annotated_image": "<base64 PNG>"
}
```

## Folder Structure

```
traffic-app/
├── backend/
│   ├── app.py               # FastAPI application
│   ├── pipeline.py          # Orchestration logic
│   ├── utils.py             # Image utils, annotation
│   ├── models/              # Drop best.pt files here
│   └── services/
│       ├── vehicle_service.py
│       ├── helmet_service.py
│       ├── seatbelt_service.py
│       └── plate_service.py
├── frontend/
│   └── index.html           # Single-page UI
├── Dockerfile
├── requirements.txt
└── README.md
```

## Troubleshooting

| Problem | Solution |
|---|---|
| `libGL.so.1 not found` | Install `libgl1-mesa-glx` (Ubuntu) or use Docker |
| OCR downloads on first run | Expected — EasyOCR downloads ~80MB model once |
| Low detection accuracy | Upload fine-tuned `best.pt` weights to `backend/models/` |
| Port already in use | Change port: `uvicorn backend.app:app --port 8080` |

## Source Notebooks

This application was built from 4 Google Colab notebooks:
- `Vehical_Detection.ipynb` — YOLO fine-tuned on IDD (Indian Driving Dataset)
- `Flipkart_Grid_Helmet_Detection.ipynb` — Binary helmet classifier
- `Flipkart_Grid_SeatBelt_Detection.ipynb` — Seatbelt detection (Roboflow dataset)
- `Flipkart_Grid_Number_Plate_Detection.ipynb` — Indian number plate + EasyOCR
