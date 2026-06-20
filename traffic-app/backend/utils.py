"""
utils.py — Shared image utilities for the traffic violation detection pipeline.
Handles image annotation, crop extraction, and base64 encoding.
"""

import cv2
import numpy as np
import base64
from typing import List, Dict, Tuple


# ─── Colour palette ──────────────────────────────────────────────────────────
COLORS = {
    "car":         (0,   200,  50),   # green
    "motorcycle":  (255, 140,   0),   # orange
    "bus":         (0,   180, 255),   # sky blue
    "truck":       (100, 100, 255),   # purple-blue
    "person":      (200, 200,   0),   # yellow
    "violation":   (0,     0, 220),   # red (BGR)
    "compliant":   (0,   200,  50),   # green
    "plate":       (0,   220, 220),   # cyan
    "default":     (180, 180, 180),   # grey
}


def decode_image(raw_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into a BGR numpy array."""
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image. Unsupported format or corrupted file.")
    return img


def encode_image_base64(img: np.ndarray) -> str:
    """Encode a BGR numpy array as base64 PNG string."""
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("Failed to encode annotated image to PNG.")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def safe_crop(img: np.ndarray, x1: int, y1: int, x2: int, y2: int, pad: int = 0) -> np.ndarray:
    """Crop image with optional padding, clamped to image bounds."""
    h, w = img.shape[:2]
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)
    return img[y1:y2, x1:x2].copy()


def draw_label(
    img: np.ndarray,
    text: str,
    x1: int, y1: int,
    color: Tuple[int, int, int],
    font_scale: float = 0.55,
    thickness: int = 2,
) -> None:
    """Draw a filled label box above a bounding box."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    label_y = max(y1, th + 8)
    # Background rectangle
    cv2.rectangle(img, (x1, label_y - th - 6), (x1 + tw + 4, label_y + baseline), color, -1)
    # Text
    cv2.putText(img, text, (x1 + 2, label_y - 2), font, font_scale, (255, 255, 255), thickness)


def annotate_image(
    img: np.ndarray,
    vehicles: List[Dict],
    helmets: List[Dict],
    seatbelts: List[Dict],
    plates: List[Dict],
    violations: List[Dict],
) -> np.ndarray:
    """
    Draw all detection results on the image.
    Returns an annotated copy.
    """
    out = img.copy()

    # Build violation lookup by vehicle_id for fast access
    violated_ids = {v["vehicle_id"] for v in violations}

    # ── Vehicle bounding boxes ─────────────────────────────────────────────
    for v in vehicles:
        x1, y1, x2, y2 = [int(c) for c in v["bbox"]]
        vtype = v.get("type", "vehicle")
        conf = v.get("confidence", 0.0)
        vid = v.get("id", 0)

        color = COLORS.get(vtype, COLORS["default"])
        if vid in violated_ids:
            color = COLORS["violation"]

        cv2.rectangle(out, (x1, y1), (x2, y2), color, 3)
        label = f"ID{vid} {vtype} {conf:.0%}"
        draw_label(out, label, x1, y1, color)

    # ── Helmet boxes ──────────────────────────────────────────────────────
    for h in helmets:
        if "bbox" not in h or not h["bbox"]:
            continue
        x1, y1, x2, y2 = [int(c) for c in h["bbox"]]
        status = h.get("status", "unknown")
        conf = h.get("confidence", 0.0)
        color = COLORS["violation"] if "without" in status.lower() else COLORS["compliant"]
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        draw_label(out, f"{status} {conf:.0%}", x1, y1, color, font_scale=0.45)

    # ── Seatbelt boxes ───────────────────────────────────────────────────
    for s in seatbelts:
        if "bbox" not in s or not s["bbox"]:
            continue
        x1, y1, x2, y2 = [int(c) for c in s["bbox"]]
        status = s.get("status", "unknown")
        conf = s.get("confidence", 0.0)
        color = COLORS["violation"] if "no_" in status.lower() else COLORS["compliant"]
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        draw_label(out, f"{status} {conf:.0%}", x1, y1, color, font_scale=0.45)

    # ── Plate boxes ──────────────────────────────────────────────────────
    for p in plates:
        if "bbox" not in p or not p["bbox"]:
            continue
        x1, y1, x2, y2 = [int(c) for c in p["bbox"]]
        text = p.get("text", "?")
        cv2.rectangle(out, (x1, y1), (x2, y2), COLORS["plate"], 2)
        draw_label(out, f"Plate: {text}", x1, y2, COLORS["plate"], font_scale=0.45)

    return out


def center_of_box(box: List[float]) -> Tuple[float, float]:
    """Return the center (cx, cy) of a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def boxes_overlap(
    box_a: List[float], box_b: List[float], threshold: float = 0.3
) -> bool:
    """
    Check if two bounding boxes overlap by IoU >= threshold.
    Useful for associating detections across crops and original image coords.
    """
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return False

    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union_area = area_a + area_b - inter_area

    return (inter_area / (union_area + 1e-6)) >= threshold
