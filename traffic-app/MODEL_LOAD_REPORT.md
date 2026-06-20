# Model Load Verification Report

This report documents the verification audit for all four ML models in the VioDetect backend system, confirming their paths, successful loading states, active fallback behaviors, and target class outputs.

---

## Model Verification Summary Table

| Model | Configured Path | Loaded? | Classes | Fallback Active? | Fallback Model |
|---|---|---|---|---|---|
| **YOLO Vehicle Detector** | `backend/models/vehicle_best.pt` | **No** (Weights missing) | `car`, `motorcycle`, `bus`, `truck`, `auto`, `bicycle` | **Yes** | `yolov8s.pt` |
| **YOLO Helmet Detector** | `backend/models/helmet_best.pt` | **Yes** | `0: helmet`, `1: no_helmet` | **No** | None |
| **YOLO Seatbelt Detector** | `backend/models/seatbelt_best.pt` | **Yes** | `0: mobile`, `1: seatbelt`, `2: windshield` | **No** | None |
| **YOLO License Plate Detector** | `backend/models/plate_best.pt` | **No** (Weights missing) | Standard COCO classes | **Yes** | `yolov8n.pt` |

---

## Detailed Model Audits

### 1. YOLO Vehicle Detector
- **File Responsible**: [vehicle_service.py](file:///c:/Users/kommi/Downloads/Bengaluru-Gridlock-Optimizer/traffic-app/backend/services/vehicle_service.py)
- **Path Configured**: `backend/models/vehicle_best.pt`
- **Audit Findings**: The custom weights file does not exist in `backend/models/`. The script triggers its fallback routine, loading the COCO pretrained `yolov8s.pt` from the root directory.
- **Class Mappings**: Standard COCO classes are active. The service maps vehicle classes using:
  ```python
  VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "auto", "bicycle"}
  ```
  Since COCO does not contain `"auto"`, it relies on the other vehicle classes for vehicle localization.

### 2. YOLO Helmet Detector
- **File Responsible**: [helmet_service.py](file:///c:/Users/kommi/Downloads/Bengaluru-Gridlock-Optimizer/traffic-app/backend/services/helmet_service.py)
- **Path Configured**: `backend/models/helmet_best.pt`
- **Audit Findings**: Custom weights loaded successfully from `backend/models/helmet_best.pt`. The fallback code is bypassed.
- **Class Mappings**: 
  - `0`: `helmet`
  - `1`: `no_helmet`
  - In `helmet_service.py`, index mappings are used (`0` maps to `"with_helmet"` status, `1` maps to `"without_helmet"` status).

### 3. YOLO Seatbelt Detector
- **File Responsible**: [seatbelt_service.py](file:///c:/Users/kommi/Downloads/Bengaluru-Gridlock-Optimizer/traffic-app/backend/services/seatbelt_service.py)
- **Path Configured**: `backend/models/seatbelt_best.pt`
- **Audit Findings**: Custom weights loaded successfully from `backend/models/seatbelt_best.pt`. The fallback code is bypassed.
- **Class Mappings**:
  - `0`: `mobile`
  - `1`: `seatbelt`
  - `2`: `windshield`
  - **Conflict Note**: The backend script expected labels like `"seatbelt"` and `"no_seatbelt"`. The actual model outputs `"mobile"`, `"seatbelt"`, and `"windshield"` (with no `"no_seatbelt"` class). This is discussed in `SEATBELT_EVALUATION.md`.

### 4. YOLO License Plate Detector
- **File Responsible**: [plate_service.py](file:///c:/Users/kommi/Downloads/Bengaluru-Gridlock-Optimizer/traffic-app/backend/services/plate_service.py)
- **Path Configured**: `backend/models/plate_best.pt`
- **Audit Findings**: Custom weights file does not exist in `backend/models/`. The script triggers its fallback routine, loading the COCO pretrained `yolov8n.pt` from the root directory.
- **Class Mappings**: Standard COCO classes are loaded. Because these classes do not contain `"plate"` or `"license"`, the detector logs that it does not support plate classes and skips localization.
