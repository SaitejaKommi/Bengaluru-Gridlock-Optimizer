# Helmet Model Evaluation Report

This report evaluates the performance characteristics, class outputs, and processing logic of the fine-tuned **`helmet_best.pt`** model.

---

## 1. Model Verification

### Class Names & Indices
The loaded custom model outputs two distinct classes:
- **`0: helmet`** (representing a driver or passenger wearing a helmet)
- **`1: no_helmet`** (representing a driver or passenger riding without a helmet)

### Output Format
The model outputs standard YOLO coordinates in the format `[cx1, cy1, cx2, cy2, confidence, class_id]`. These coordinates are defined relative to the cropped motorcycle bounding box, and the service maps them back to the original full-frame coordinate space:
```python
crop_offset_x = max(0, x1 - 10)
crop_offset_y = max(0, y1 - pad - 10)
orig_bbox = [
    crop_offset_x + cx1,
    crop_offset_y + cy1,
    crop_offset_x + cx2,
    crop_offset_y + cy2,
]
```

### Rider Association Logic
- The system associates helmets with vehicles by cropping the motorcycle detection box first.
- To ensure the rider's head is captured (which sits above the bike frame), a padding equal to $50\%$ of the motorcycle's height is added to the top of the crop boundary:
  ```python
  pad = int((y2 - y1) * 0.5)
  crop = safe_crop(full_image, x1, y1 - pad, x2, y2, pad=10)
  ```
- The crop is passed to `helmet_best.pt`.
- The highest-confidence detection box is selected as the primary status identifier.

---

## 2. Evaluation Scenarios

### Expected Working Cases
- **Single Rider, High Contrast**: Clear daylight captures of a single rider where the helmet stands out against the sky or building silhouettes.
- **Proper Bounding Box Alignments**: Standard lookdown camera angles where the vehicle detector accurately locates the motorcycle, ensuring the $50\%$ top-pad covers the rider's head.

### Expected Failure Cases
- **Pillion Rider Occlusion**: If a passenger is sitting directly behind the driver, their head may be hidden in the driver's shadow or outline. The model will only detect the driver's helmet, missing a passenger's non-compliance violation.
- **Low-contrast / Night Environments**: Dark helmets matching the color of asphalt or the motorcycle frame can fail to register, resulting in false negatives.
- **Turbans and Religious Headwear**: Headwear such as turbans can be misclassified as helmets or no-helmets, leading to false alerts.

---

## 3. Parameter Recommendations

- **Current Configured Threshold**: `0.25`
- **Recommended Threshold**:
  - **For Automated Citation (No Review)**: `0.55` (prevents false positives from background clutter or headwear).
  - **For Semi-Automated Audited Flow (Human-in-the-loop)**: `0.35` (captures borderline detections, allowing a reviewer to reject false alerts).
