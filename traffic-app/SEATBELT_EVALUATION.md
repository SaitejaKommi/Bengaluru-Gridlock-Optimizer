# Seatbelt Model Evaluation Report

This report evaluates the performance characteristics, class outputs, and architectural assumptions of the **`seatbelt_best.pt`** model.

---

## 1. Class Output Verification
Running visual check scripts confirmed that `seatbelt_best.pt` outputs three target classes:
- **`0: mobile`** (representing a driver/occupant holding a cell phone or calling)
- **`1: seatbelt`** (representing a seatbelt strap localized on the chest)
- **`2: windshield`** (representing the windshield glass bounding region)

---

## 2. Backend Assumption Discrepancy

### The Discrepancy
- **Backend Assumption**: The service script (`seatbelt_service.py`) was written assuming the model outputted classes representing both `"seatbelt"` and `"no_seatbelt"` (as labeled in typical interior seatbelt datasets).
- **Actual Model Output**: The model only localizes **`seatbelt` presence**, and does not have an explicit class for `"no_seatbelt"`. 

### Can the model reliably determine Seatbelt compliance?
**No, not directly**. Since there is no `"no_seatbelt"` class, the model can only identify when a seatbelt is *present*. 
- To declare a `"no_seatbelt"` violation, the backend must use an *absence-based heuristic* (i.e. *"If windshield is detected but seatbelt is not localized, flag a violation"*).
- The original code implemented this by automatically returning `"no_seatbelt"` with `0.5` confidence whenever the model returned zero boxes or had an unavailable state.
- Because this heuristic leads to false alerts on dark car cabins or glare, we have removed it, which means seatbelt compliance checks will return `"unavailable"` (unknown) on zero detections until a model trained with an explicit negative class (e.g. occupant chest without a strap) is supplied.

---

## 3. Cell Phone Detection Potential

### Key Discovery
The model contains class **`0: mobile`**! 
- This means mobile phone usage detection **is already supported** by the current custom model weights (`seatbelt_best.pt`).
- However, the backend code in `seatbelt_service.py` currently discards class `0` because it only filters for labels matching `SEATBELT_CLASSES` or `NO_SEATBELT_CLASSES`.

### Recommendation to Enable Mobile Usage Detection
To implement mobile phone usage detection without adding a new model file, the backend can be updated to parse class `0` from the model's predictions. If a `"mobile"` box is localized with high confidence, the system can append a `"Mobile Phone Usage"` violation directly.
