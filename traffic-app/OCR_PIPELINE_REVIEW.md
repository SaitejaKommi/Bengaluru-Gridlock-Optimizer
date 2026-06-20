# OCR Pipeline Review Report

This report presents a detailed audit of the license plate extraction and OCR pipeline in `plate_service.py`, explaining the current preprocessing, EasyOCR parameters, and character translation details.

---

## 1. Pipeline Component Audit

### Crop Padding
- **Implementation**: `plate_crop = safe_crop(search_img, px1, py1, px2, py2, pad=20)`
- **Audit Findings**: A static padding of `20px` is added to all sides of the crop. For small or distant license plates (e.g., 50px–100px wide), a 20px padding represents a massive boundary expansion. This crops in background artifacts like vehicle grilles, mounting screws, bumpers, or shadow lines, which EasyOCR attempts to read as characters.

### Image Preprocessing
- **Upscaling**: Resizes up to 8.0x using bicubic interpolation (`cv2.INTER_CUBIC`), capped at 600px width and 200px height.
- **Denoising**: `cv2.fastNlMeansDenoisingColored(..., 10, 10, 7, 21)` is executed with a strength of `10`.
- **Sharpening**: Filters using a high-pass Laplacian-like sharpening kernel:
  $$\begin{bmatrix} 0 & -1 & 0 \\ -1 & 5 & -1 \\ 0 & -1 & 0 \end{bmatrix}$$
- **Audit Findings**: While upscaling improves small text reading, the denoising filter strength of `10` is too aggressive on small crops. It smudges fine lines and intersections, blending characters. The subsequent sharpening filter hardens these smudged shapes, presenting distorted text boundaries to the OCR engine.

### EasyOCR Configuration
- **Implementation**:
  ```python
  ocr_results = ocr.readtext(
      enhanced,
      detail=1,
      allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
  )
  ```
- **Audit Findings**: The alphanumeric `allowlist` is correct for Indian plates. However, EasyOCR lacks layout structure awareness (priors) for license plates (e.g., expecting a sequence like `[State Code: 2 letters][District: 2 digits][Series: 1-2 letters][Plate: 4 digits]`). It processes the text as a generic scene text block, leading to letter-number substitutions (like `S` for `5` or `I` for `1`).

### OCR Post-Processing
- **Implementation**: Strips non-alphanumeric characters, converts to uppercase, and joins blocks with spaces.
- **Audit Findings**: It does not perform pattern verification or validation against standard Indian state registrations.

---

## 2. Character Translation Case Study: `KA53C1819` $\rightarrow$ `TSJC1819`

The following breakdown explains why character misread errors occur:

### 1. State Code Swap (`KA` $\rightarrow$ `TS`)
- **`K` $\rightarrow$ `T`**: The diagonal strokes of the letter `K` are thin. Aggressive denoising (`fastNlMeansDenoisingColored`) removes these low-contrast diagonal lines, leaving only the primary vertical stroke, which the model reads as a `T` or `I`.
- **`A` $\rightarrow$ `S`**: The central hollow hole of the letter `A` gets filled in during upscaling and denoising. The shape becomes a solid rounded blob. Sharpening outlines this blob, making it resemble the loops of an `S` or `8`.

### 2. District Code Swap (`53` $\rightarrow$ `S` / `J`)
- **`5` $\rightarrow$ `S`**: The sharp right-angled top of `5` is rounded off by the denoiser, blending it into an `S`.
- **`3` $\rightarrow$ `J`**: The left gaps in the number `3` are narrow. Denoising fills them, and sharpening outlines the outer curves, which EasyOCR reads as a `J` or `S`.

### 3. Extra Prefix / Suffix Hallucinations
- The mounting screws on the license plate frame appear as high-contrast dots. The sharpening filter enhances their edges, causing EasyOCR to read them as letters like `I`, `1`, or `T`, injecting false characters.

---

## 3. Recommended Pipeline Optimization

1. **Dynamic Crop Padding**: Replace the hardcoded `20px` pad with a dynamic percentage-based padding (e.g., `10%` of the localized bounding box width and height).
2. **Denoising Tuning**: Reduce the denoising strength from `10` to `5` (or bypass it entirely on high-resolution plates) to prevent character smudging.
3. **Layout Regex Correction**: Implement a post-processing validation function using regular expressions to correct common OCR substitutions based on Indian plate formats:
   ```python
   # Example substitution mapping
   if is_state_code_zone and char == '5': char = 'S'
   if is_digit_zone and char == 'S': char = '5'
   ```
