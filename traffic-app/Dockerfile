# ─── Stage 1: Build image ─────────────────────────────────────────────────────
FROM python:3.10-slim

# System dependencies for OpenCV headless + EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (Hugging Face Spaces requirement)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download YOLO base weights so they're baked into the image
# (avoids downloading at inference time in HF Spaces)
RUN python -c "\
from ultralytics import YOLO; \
print('Downloading yolov8n...'); YOLO('yolov8n.pt'); \
print('Downloading yolov8s...'); YOLO('yolov8s.pt'); \
print('Base weights ready.')"

# Copy application code
COPY --chown=appuser:appuser . .

# Create models directory (users can mount fine-tuned weights here)
RUN mkdir -p /app/backend/models

# Switch to non-root user
USER appuser

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

# Start the application
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
