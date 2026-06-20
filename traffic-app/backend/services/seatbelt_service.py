"""
seatbelt_service.py

Reused from: Flipkart_Grid_SeatBelt_Detection.ipynb (cells 15–21)

Loads fine-tuned YOLO for seatbelt detection.
Falls back to yolov8n.pt if custom weights not found.

Expected classes from fine-tuned model:
  seatbelt, no_seatbelt  (Roboflow dataset: seat-belt-4k5qg-dnvkf)
"""

import os
import logging
from typing import List, Dict, Optional

import numpy as np
from ultralytics import YOLO

from backend.utils import safe_crop

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "seatbelt_best.pt")
FALLBACK_WEIGHTS = "yolov8n.pt"
CONF_THRESHOLD = 0.25

# Class names expected after fine-tuning
SEATBELT_CLASSES = {"seatbelt", "seatbelts"}
NO_SEATBELT_CLASSES = {"no_seatbelt", "no-seatbelt", "noseatbelt", "without_seatbelt"}

_model: Optional[YOLO] = None
_using_custom: bool = False


def load_model() -> YOLO:
    global _model, _using_custom
    if _model is not None:
        return _model

    if os.path.isfile(WEIGHTS_PATH):
        logger.info(f"Loading custom seatbelt weights from {WEIGHTS_PATH}")
        _model = YOLO(WEIGHTS_PATH)
        _using_custom = True
    else:
        logger.info(f"Custom seatbelt weights not found — using {FALLBACK_WEIGHTS} (limited seatbelt detection)")
        _model = YOLO(FALLBACK_WEIGHTS)
        _using_custom = False

    logger.info("Seatbelt model loaded.")
    return _model


def detect_seatbelt(
    full_image: np.ndarray,
    car_bbox: List[int],
    vehicle_id: int,
) -> Dict:
    """
    Run seatbelt detection on a car/bus/truck crop.

    Args:
        full_image:  Full BGR image array.
        car_bbox:    [x1, y1, x2, y2] bounding box of the vehicle.
        vehicle_id:  ID of the parent vehicle.

    Returns dict:
    {
        "vehicle_id":  int,
        "status":      "seatbelt" | "no_seatbelt" | "unavailable",
        "confidence":  float,
        "bbox":        [x1,y1,x2,y2] in original image coords, or []
    }
    """
    model = load_model()

    x1, y1, x2, y2 = car_bbox
    crop = safe_crop(full_image, x1, y1, x2, y2, pad=5)

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
        logger.error(f"Seatbelt detection failed for vehicle {vehicle_id}: {exc}")
        return {
            "vehicle_id": vehicle_id,
            "status": "unavailable",
            "confidence": 0.0,
            "bbox": [],
        }

    names = model.names

    if not _using_custom:
        return {
            "vehicle_id": vehicle_id,
            "status": "unavailable",
            "confidence": 0.0,
            "bbox": [],
        }

    if len(results.boxes) == 0:
        # Fine-tuned model found nothing — return unavailable (unknown)
        return {
            "vehicle_id": vehicle_id,
            "status": "unavailable",
            "confidence": 0.0,
            "bbox": [],
        }

    # Find the most relevant detection
    best_status = "unavailable"
    best_conf = 0.0
    best_bbox = []

    for i in range(len(results.boxes)):
        cls_id = int(results.boxes.cls[i])
        conf   = float(results.boxes.conf[i])
        label  = names[cls_id].lower()
        xyxy   = results.boxes.xyxy[i].cpu().numpy().tolist()
        cx1, cy1, cx2, cy2 = [int(c) for c in xyxy]

        if label in NO_SEATBELT_CLASSES:
            # No seatbelt is a strong finding — take highest conf
            if conf > best_conf or best_status == "unavailable":
                best_status = "no_seatbelt"
                best_conf   = conf
                best_bbox   = [x1 + cx1, y1 + cy1, x1 + cx2, y1 + cy2]
        elif label in SEATBELT_CLASSES and best_status not in ("no_seatbelt",):
            if conf > best_conf:
                best_status = "seatbelt"
                best_conf   = conf
                best_bbox   = [x1 + cx1, y1 + cy1, x1 + cx2, y1 + cy2]

    # Do not fallback to no_seatbelt if unavailable to prevent programmatic hallucinations

    logger.info(f"Seatbelt detection for vehicle {vehicle_id}: {best_status} ({best_conf:.2f})")
    return {
        "vehicle_id": vehicle_id,
        "status":     best_status,
        "confidence": round(best_conf, 3),
        "bbox":       best_bbox,
    }
