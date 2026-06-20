"""
helmet_service.py

Reused from: Flipkart_Grid_Helmet_Detection.ipynb (cells 10–12)

Loads a fine-tuned YOLO binary classifier for helmet detection.
Falls back to yolov8n.pt if custom weights not found.

Fine-tuned class mapping (from notebook cell 7):
  0 → with_helmet    (driver/passenger_with_helmet)
  1 → without_helmet (driver/passenger_without_helmet)

For fallback COCO model: we cannot detect helmets directly,
so we return a "detection_unavailable" result with a note.
"""

import os
import logging
from typing import List, Dict, Optional

import numpy as np
from ultralytics import YOLO

from backend.utils import safe_crop

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "helmet_best.pt")
FALLBACK_WEIGHTS = "yolov8n.pt"
CONF_THRESHOLD = 0.25

# Expected class names after fine-tuning
HELMET_CLASS_MAP = {
    0: "with_helmet",
    1: "without_helmet",
}

_model: Optional[YOLO] = None
_using_custom: bool = False


def load_model() -> YOLO:
    global _model, _using_custom
    if _model is not None:
        return _model

    if os.path.isfile(WEIGHTS_PATH):
        logger.info(f"Loading custom helmet weights from {WEIGHTS_PATH}")
        _model = YOLO(WEIGHTS_PATH)
        _using_custom = True
    else:
        logger.info(f"Custom helmet weights not found — using {FALLBACK_WEIGHTS} (limited helmet detection)")
        _model = YOLO(FALLBACK_WEIGHTS)
        _using_custom = False

    logger.info("Helmet model loaded.")
    return _model


def detect_helmet(
    full_image: np.ndarray,
    bike_bbox: List[int],
    vehicle_id: int,
) -> Dict:
    """
    Run helmet detection on a motorcycle crop.

    Args:
        full_image:  Full BGR image array.
        bike_bbox:   [x1, y1, x2, y2] bounding box of the motorcycle.
        vehicle_id:  ID of the parent vehicle.

    Returns dict:
    {
        "vehicle_id":  int,
        "status":      "with_helmet" | "without_helmet" | "unavailable",
        "confidence":  float,
        "bbox":        [x1,y1,x2,y2] in original image coords, or []
    }
    """
    model = load_model()

    x1, y1, x2, y2 = bike_bbox
    # Use generous crop padding to capture riders above the bike
    pad = int((y2 - y1) * 0.5)
    crop = safe_crop(full_image, x1, y1 - pad, x2, y2, pad=10)

    if crop.size == 0:
        return {
            "vehicle_id": vehicle_id,
            "status": "unavailable",
            "confidence": 0.0,
            "bbox": [],
        }

    try:
        results = model(crop, conf=CONF_THRESHOLD, verbose=False)[0]
    except Exception as exc:
        logger.error(f"Helmet detection failed for vehicle {vehicle_id}: {exc}")
        return {
            "vehicle_id": vehicle_id,
            "status": "unavailable",
            "confidence": 0.0,
            "bbox": [],
        }

    if len(results.boxes) == 0:
        # No helmet class detected at all on crop
        if _using_custom:
            # The fine-tuned model should find something — treat as no helmet
            return {
                "vehicle_id": vehicle_id,
                "status": "without_helmet",
                "confidence": 0.5,
                "bbox": [],
            }
        else:
            return {
                "vehicle_id": vehicle_id,
                "status": "unavailable",
                "confidence": 0.0,
                "bbox": [],
            }

    # Pick the highest-confidence box
    best_idx = int(results.boxes.conf.argmax())
    cls_id   = int(results.boxes.cls[best_idx])
    conf     = float(results.boxes.conf[best_idx])
    xyxy     = results.boxes.xyxy[best_idx].cpu().numpy().tolist()
    cx1, cy1, cx2, cy2 = [int(c) for c in xyxy]

    # Map class ID to status
    if _using_custom:
        status = HELMET_CLASS_MAP.get(cls_id, "without_helmet")
    else:
        # Fallback: COCO has no helmet class — mark as unavailable
        return {
            "vehicle_id": vehicle_id,
            "status": "unavailable",
            "confidence": 0.0,
            "bbox": [],
        }

    # Convert crop coords back to original image coords
    crop_offset_x = max(0, x1 - 10)
    crop_offset_y = max(0, y1 - pad - 10)
    orig_bbox = [
        crop_offset_x + cx1,
        crop_offset_y + cy1,
        crop_offset_x + cx2,
        crop_offset_y + cy2,
    ]

    logger.info(f"Helmet detection for vehicle {vehicle_id}: {status} ({conf:.2f})")
    return {
        "vehicle_id": vehicle_id,
        "status":     status,
        "confidence": round(conf, 3),
        "bbox":       orig_bbox,
    }
