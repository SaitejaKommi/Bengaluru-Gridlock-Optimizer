"""
plate_service.py

Reused from: Flipkart_Grid_Number_Plate_Detection.ipynb (cells 9–17)

Full pipeline:
  1. YOLO detects license plate bounding box
  2. Crop + 8× upscale + denoise + sharpen  (from notebook cells 14–16)
  3. EasyOCR reads the text  (from notebook cell 17)
  4. Clean and return

Uses EasyOCR with allowlist A-Z 0-9 (Indian plates).
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple

import cv2
import numpy as np
import easyocr
from ultralytics import YOLO

from backend.utils import safe_crop

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "plate_best.pt")
FALLBACK_WEIGHTS = "yolov8n.pt"
CONF_THRESHOLD = 0.25

_model: Optional[YOLO] = None
_ocr: Optional[easyocr.Reader] = None


def load_model() -> YOLO:
    global _model
    if _model is not None:
        return _model

    if os.path.isfile(WEIGHTS_PATH):
        logger.info(f"Loading custom plate weights from {WEIGHTS_PATH}")
        _model = YOLO(WEIGHTS_PATH)
    else:
        logger.info(f"Custom plate weights not found — using {FALLBACK_WEIGHTS} (may not detect plates)")
        _model = YOLO(FALLBACK_WEIGHTS)

    logger.info("Plate detection model loaded.")
    return _model


def load_ocr() -> easyocr.Reader:
    global _ocr
    if _ocr is not None:
        return _ocr
    logger.info("Initialising EasyOCR (downloading models on first run)...")
    _ocr = easyocr.Reader(["en"], gpu=False, verbose=False)
    logger.info("EasyOCR ready.")
    return _ocr


# ── Image enhancement pipeline (from notebook cells 14–16) ──────────────────
def _enhance_plate_crop(crop: np.ndarray) -> np.ndarray:
    """Upscale, denoise, and sharpen a plate crop for better OCR."""
    if crop.size == 0:
        return crop

    h, w = crop.shape[:2]
    # Limit maximum upscaled dimensions to prevent extremely slow denoising on CPU
    max_w = 600
    max_h = 200
    
    fx = min(8.0, max_w / w)
    fy = min(8.0, max_h / h)
    fx = max(1.0, fx)
    fy = max(1.0, fy)

    # Upscale
    big = cv2.resize(crop, None, fx=fx, fy=fy, interpolation=cv2.INTER_CUBIC)

    # Denoise (notebook cell 16)
    big = cv2.fastNlMeansDenoisingColored(big, None, 10, 10, 7, 21)

    # Sharpen (notebook cell 16)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    big = cv2.filter2D(big, -1, kernel)

    return big


def _clean_plate_text(raw: str) -> str:
    """Strip non-alphanumeric and normalise to uppercase (Indian plates)."""
    cleaned = re.sub(r"[^A-Z0-9]", "", raw.upper())
    return cleaned


def detect_numberplate(
    full_image: np.ndarray,
    vehicle_bbox: Optional[List[int]] = None,
    vehicle_id: int = 0,
) -> Dict:
    """
    Detect license plate in an image (optionally cropped to a vehicle).

    Args:
        full_image:   Full BGR image array.
        vehicle_bbox: Optional [x1,y1,x2,y2] to restrict search to a vehicle crop.
        vehicle_id:   ID of the parent vehicle (for output tagging).

    Returns dict:
    {
        "vehicle_id": int,
        "text":       str,        # cleaned plate text, "" if not found
        "confidence": float,      # detection confidence
        "ocr_confidence": float,  # OCR confidence
        "bbox":       [x1,y1,x2,y2] in original image coords, or []
    }
    """
    model = load_model()
    ocr   = load_ocr()

    # If the loaded model does not contain a license plate class (e.g. COCO fallback),
    # then skip plate detection to avoid false positive detections on COCO classes.
    has_plate_class = any("plate" in name.lower() or "license" in name.lower() for name in model.names.values())
    if not has_plate_class:
        logger.info(f"Model {model.ckpt_path} does not support license plate classes. Skipping plate detection.")
        return _empty_result(vehicle_id)

    # Optionally restrict search region
    if vehicle_bbox:
        x1v, y1v, x2v, y2v = vehicle_bbox
        search_img    = safe_crop(full_image, x1v, y1v, x2v, y2v, pad=10)
        offset_x      = max(0, x1v - 10)
        offset_y      = max(0, y1v - 10)
    else:
        search_img    = full_image
        offset_x      = 0
        offset_y      = 0

    if search_img.size == 0:
        return _empty_result(vehicle_id)

    try:
        results = model(search_img, conf=CONF_THRESHOLD, verbose=False)[0]
    except Exception as exc:
        logger.error(f"Plate detection failed for vehicle {vehicle_id}: {exc}")
        return _empty_result(vehicle_id)

    if len(results.boxes) == 0:
        return _empty_result(vehicle_id)

    # Take the highest-confidence plate box
    best_idx   = int(results.boxes.conf.argmax())
    det_conf   = float(results.boxes.conf[best_idx])
    xyxy       = results.boxes.xyxy[best_idx].cpu().numpy().tolist()
    px1, py1, px2, py2 = [int(c) for c in xyxy]

    # Crop with padding (notebook cell 15: pad=20)
    plate_crop = safe_crop(search_img, px1, py1, px2, py2, pad=20)


    if plate_crop.size == 0:
        return _empty_result(vehicle_id)

    # Enhance (notebook cells 14–16)
    enhanced = _enhance_plate_crop(plate_crop)

    # OCR (notebook cell 17)
    try:
        ocr_results = ocr.readtext(
            enhanced,
            detail=1,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        )
    except Exception as exc:
        logger.error(f"EasyOCR failed for vehicle {vehicle_id}: {exc}")
        return _empty_result(vehicle_id)

    if not ocr_results:
        return _empty_result(vehicle_id)

    # Combine all OCR text and pick best confidence
    plate_text = " ".join(_clean_plate_text(r[1]) for r in ocr_results if r[1].strip())
    ocr_conf   = max(float(r[2]) for r in ocr_results)

    # Convert back to original image coordinates
    orig_bbox = [
        offset_x + px1,
        offset_y + py1,
        offset_x + px2,
        offset_y + py2,
    ]

    logger.info(f"Plate detected for vehicle {vehicle_id}: '{plate_text}' (det={det_conf:.2f}, ocr={ocr_conf:.2f})")
    return {
        "vehicle_id":    vehicle_id,
        "text":          plate_text,
        "confidence":    round(det_conf, 3),
        "ocr_confidence": round(ocr_conf, 3),
        "bbox":          orig_bbox,
    }


def _empty_result(vehicle_id: int) -> Dict:
    return {
        "vehicle_id":    vehicle_id,
        "text":          "",
        "confidence":    0.0,
        "ocr_confidence": 0.0,
        "bbox":          [],
    }
