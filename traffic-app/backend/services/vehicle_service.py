"""
vehicle_service.py

Reused from: Vehical_Detection.ipynb (cells 14–23)

Loads a fine-tuned YOLO model for vehicle + rider detection.
Falls back to yolov8s.pt (COCO pretrained) if custom weights not found.

Classes expected from fine-tuned model (IDD dataset):
  car, motorcycle, bus, truck, auto, rider, person, bicycle

Also detects triple-riding violations (≥3 riders on one motorcycle).
"""

import os
import logging
from typing import List, Dict

import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "vehicle_best.pt")
FALLBACK_WEIGHTS = "yolov8s.pt"
CONF_THRESHOLD = 0.25

# Vehicle classes (covers both COCO and IDD fine-tuned model)
VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "auto", "bicycle"}
RIDER_CLASSES   = {"person", "rider"}

_model: YOLO = None  # singleton


def load_model() -> YOLO:
    """Load model once. Prefers custom weights, falls back to pretrained."""
    global _model
    if _model is not None:
        return _model

    if os.path.isfile(WEIGHTS_PATH):
        logger.info(f"Loading custom vehicle weights from {WEIGHTS_PATH}")
        _model = YOLO(WEIGHTS_PATH)
    else:
        logger.info(f"Custom vehicle weights not found — using {FALLBACK_WEIGHTS}")
        _model = YOLO(FALLBACK_WEIGHTS)

    logger.info("Vehicle model loaded.")
    return _model


def detect_vehicles(image: np.ndarray) -> List[Dict]:
    """
    Run vehicle detection on a BGR numpy array.

    Returns a list of dicts:
    {
        "id":         int,
        "type":       str,          # "car" | "motorcycle" | "bus" | ...
        "confidence": float,
        "bbox":       [x1,y1,x2,y2] (ints, original image coords)
    }

    Also detects triple-riding: adds "triple_riding": True to motorcycle entries
    when ≥ 3 riders are spatially associated with that bike.
    """
    model = load_model()

    try:
        results = model(image, conf=CONF_THRESHOLD, verbose=False)[0]
    except Exception as exc:
        logger.error(f"Vehicle detection inference failed: {exc}")
        return []

    boxes  = results.boxes
    names  = model.names

    vehicles: List[Dict] = []
    riders:   List[List[float]] = []
    vid = 0

    for i in range(len(boxes)):
        cls_id = int(boxes.cls[i])
        label  = names[cls_id].lower()
        conf   = float(boxes.conf[i])
        xyxy   = boxes.xyxy[i].cpu().numpy().tolist()
        x1, y1, x2, y2 = [int(c) for c in xyxy]

        if label in VEHICLE_CLASSES:
            vid += 1
            vehicles.append({
                "id":           vid,
                "type":         label,
                "confidence":   round(conf, 3),
                "bbox":         [x1, y1, x2, y2],
                "triple_riding": False,
            })
        elif label in RIDER_CLASSES:
            riders.append([x1, y1, x2, y2])

    # ── Triple-riding detection (from notebook cell 23) ────────────────────
    for v in vehicles:
        if v["type"] != "motorcycle":
            continue

        bx1, by1, bx2, by2 = v["bbox"]
        bcx = (bx1 + bx2) / 2.0
        bike_width = bx2 - bx1
        rider_count = 0

        for rider_box in riders:
            rx1, ry1, rx2, ry2 = rider_box
            rcx = (rx1 + rx2) / 2.0
            rcy = (ry1 + ry2) / 2.0

            # Horizontal proximity (within ~1.2× bike width)
            if abs(rcx - bcx) < max(80, bike_width * 1.2):
                # Rider center must be above or around the bike bottom
                if rcy <= by2 + 50:
                    rider_count += 1

        if rider_count >= 3:
            v["triple_riding"] = True
            logger.info(f"Triple riding detected on vehicle ID {v['id']} ({rider_count} riders)")

    logger.info(f"Detected {len(vehicles)} vehicles ({sum(1 for v in vehicles if v['type']=='motorcycle')} motorcycles, {sum(1 for v in vehicles if v['type'] in {'car','bus','truck'})} cars/buses/trucks)")
    return vehicles
