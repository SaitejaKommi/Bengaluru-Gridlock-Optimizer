# Hallucination Audit Report

This report documents the audit of code paths within the VioDetect backend where traffic violations were programmatically generated on empty detection outputs. It also describes the corrective patches applied to eliminate these false violations.

---

## Audited Hallucination Locations

### 1. Helmet Service Fallback (Motorcycles)
- **File**: [helmet_service.py](file:///c:/Users/kommi/Downloads/Bengaluru-Gridlock-Optimizer/traffic-app/backend/services/helmet_service.py)
- **Target Code**: Lines 110–117
- **Logic**: If the custom helmet model was loaded but returned **zero** bounding box detections on a motorcycle crop, the code assumed that the rider was violating the helmet law. It returned:
  ```python
  "status": "without_helmet",
  "confidence": 0.5
  ```
- **Risk**: Programmatic false positives. Any motorcycle crop with poor contrast, low resolution, or occlusion resulted in an automatic "No Helmet" violation, even if the rider was wearing a helmet.
- **Correction Applied**: Changed the fallback to return `status: "unavailable"` and `confidence: 0.0` when zero boxes are detected. Detections are only marked as violations if the model explicitly localizes a non-helmet occupant.

### 2. Seatbelt Service Crop Fallback (Cars)
- **File**: [seatbelt_service.py](file:///c:/Users/kommi/Downloads/Bengaluru-Gridlock-Optimizer/traffic-app/backend/services/seatbelt_service.py)
- **Target Code**: Lines 110–117
- **Logic**: If the custom seatbelt model was loaded but returned **zero** bounding box detections on a car crop, the system assumed that the occupants were violating the seatbelt law, returning:
  ```python
  "status": "no_seatbelt",
  "confidence": 0.5
  ```
- **Risk**: High rate of false positives on dark interiors, tinted windows, or windshield glares where occupant chests could not be localized.
- **Correction Applied**: Patched the branch to return `status: "unavailable"` and `confidence: 0.0`.

### 3. Seatbelt Service Status Fallback
- **File**: [seatbelt_service.py](file:///c:/Users/kommi/Downloads/Bengaluru-Gridlock-Optimizer/traffic-app/backend/services/seatbelt_service.py)
- **Target Code**: Lines 143–146
- **Logic**: In cases where the seatbelt model returned detections, but they were ignored (e.g. only detecting `windshield` or `mobile` but not `seatbelt`), `best_status` remained `"unavailable"`. The fallback block then forced:
  ```python
  if best_status == "unavailable":
      best_status = "no_seatbelt"
      best_conf   = 0.5
  ```
- **Risk**: If the model localized only a windshield or a cell phone, the code hallucinated a seatbelt violation.
- **Correction Applied**: Removed the fallback statement entirely. An `"unavailable"` status now correctly bubbles up as `"unavailable"` (unknown), preventing hallucinated seatbelt citations.
