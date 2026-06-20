"""
pipeline.py — Orchestrates all 4 detection services.

Execution order:
  1. Vehicle Detection (always runs)
  2. Helmet Detection  (only for motorcycles)
  3. Seatbelt Detection (only for cars/buses/trucks)
  4. Number Plate Detection (all vehicles)
  5. Rule engine — maps violations
  6. Annotate image + encode base64

Each service is wrapped in try/except so one failure never kills the pipeline.
"""

import logging
from typing import Dict, Any

import numpy as np

from backend.services.vehicle_service  import detect_vehicles
from backend.services.helmet_service   import detect_helmet
from backend.services.seatbelt_service import detect_seatbelt
from backend.services.plate_service    import detect_numberplate
from backend.utils import annotate_image, encode_image_base64

logger = logging.getLogger(__name__)

# Vehicle types that trigger each sub-module
MOTORCYCLE_TYPES = {"motorcycle"}
CAR_TYPES        = {"car", "bus", "truck", "auto"}


def run_pipeline(image: np.ndarray) -> Dict[str, Any]:
    """
    Full inference pipeline on a BGR numpy image.

    Returns the consolidated JSON result dict.
    """
    logger.info("─── Pipeline started ───────────────────────────────────────")

    # ── STEP 1: Vehicle Detection ──────────────────────────────────────────
    logger.info("Running vehicle detection...")
    try:
        vehicles = detect_vehicles(image)
    except Exception as exc:
        logger.error(f"Vehicle detection crashed: {exc}")
        vehicles = []

    logger.info(f"Vehicles found: {len(vehicles)}")

    helmets   = []
    seatbelts = []
    plates    = []

    for v in vehicles:
        vtype = v.get("type", "")
        vid   = v["id"]
        bbox  = v["bbox"]

        # ── STEP 2: Helmet Detection (motorcycles only) ──────────────────
        if vtype in MOTORCYCLE_TYPES:
            logger.info(f"Running helmet detection for motorcycle ID {vid}...")
            try:
                h = detect_helmet(image, bbox, vid)
                helmets.append(h)
            except Exception as exc:
                logger.error(f"Helmet detection crashed for vehicle {vid}: {exc}")
                helmets.append({
                    "vehicle_id": vid,
                    "status": "unavailable",
                    "confidence": 0.0,
                    "bbox": [],
                })

        # ── STEP 3: Seatbelt Detection (cars/buses/trucks) ───────────────
        elif vtype in CAR_TYPES:
            logger.info(f"Running seatbelt detection for {vtype} ID {vid}...")
            try:
                s = detect_seatbelt(image, bbox, vid)
                seatbelts.append(s)
            except Exception as exc:
                logger.error(f"Seatbelt detection crashed for vehicle {vid}: {exc}")
                seatbelts.append({
                    "vehicle_id": vid,
                    "status": "unavailable",
                    "confidence": 0.0,
                    "bbox": [],
                })

        # ── STEP 4: Number Plate Detection (all vehicles) ────────────────
        logger.info(f"Running plate detection for vehicle ID {vid}...")
        try:
            p = detect_numberplate(image, vehicle_bbox=bbox, vehicle_id=vid)
            if p["text"] or p["confidence"] > 0:
                plates.append(p)
        except Exception as exc:
            logger.error(f"Plate detection crashed for vehicle {vid}: {exc}")

    # ── STEP 5: Rule Engine — compile violations ───────────────────────────
    logger.info("Running rule engine...")
    violations = _build_violations(vehicles, helmets, seatbelts)

    # ── STEP 6: Annotate image ─────────────────────────────────────────────
    logger.info("Annotating image...")
    try:
        annotated = annotate_image(image, vehicles, helmets, seatbelts, plates, violations)
        annotated_b64 = encode_image_base64(annotated)
    except Exception as exc:
        logger.error(f"Image annotation failed: {exc}")
        annotated_b64 = ""

    # ── Summary ────────────────────────────────────────────────────────────
    summary = {
        "total_vehicles":  len(vehicles),
        "motorcycles":     sum(1 for v in vehicles if v["type"] in MOTORCYCLE_TYPES),
        "cars":            sum(1 for v in vehicles if v["type"] in CAR_TYPES),
        "violations_count": len(violations),
        "helmet_violations": sum(1 for h in helmets if h.get("status") == "without_helmet"),
        "seatbelt_violations": sum(1 for s in seatbelts if s.get("status") == "no_seatbelt"),
        "plates_read": sum(1 for p in plates if p.get("text")),
    }

    logger.info(f"Pipeline complete. Vehicles={len(vehicles)}, Violations={len(violations)}")
    logger.info("─── Pipeline complete ──────────────────────────────────────")

    return {
        "status":          "success",
        "vehicles":        vehicles,
        "helmets":         helmets,
        "seatbelts":       seatbelts,
        "numberplates":    plates,
        "violations":      violations,
        "summary":         summary,
        "annotated_image": annotated_b64,
    }


# ── Rule engine ───────────────────────────────────────────────────────────────

def _build_violations(
    vehicles: list,
    helmets:  list,
    seatbelts: list,
) -> list:
    """Convert service outputs into canonical violation records."""
    violations = []

    # Helmet violations
    for h in helmets:
        if h.get("status") == "without_helmet":
            violations.append({
                "vehicle_id": h["vehicle_id"],
                "type":       "No Helmet",
                "confidence": h.get("confidence", 0.0),
                "description": "Motorcycle rider detected without helmet",
            })

    # Seatbelt violations
    for s in seatbelts:
        if s.get("status") == "no_seatbelt":
            violations.append({
                "vehicle_id": s["vehicle_id"],
                "type":       "No Seatbelt",
                "confidence": s.get("confidence", 0.0),
                "description": "Vehicle occupant detected without seatbelt",
            })

    # Triple riding
    for v in vehicles:
        if v.get("triple_riding"):
            violations.append({
                "vehicle_id": v["id"],
                "type":       "Triple Riding",
                "confidence": v.get("confidence", 0.0),
                "description": "Motorcycle carrying 3 or more riders (illegal)",
            })

    return violations
