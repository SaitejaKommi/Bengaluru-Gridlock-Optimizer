import os
import sys
import time
import requests
import cv2
import numpy as np
import subprocess

# ─── Configuration ────────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:7860"
TEST_DIR = "test_images"
os.makedirs(TEST_DIR, exist_ok=True)

# Public URLs for testing real traffic/violation cases
# These are reliable open-source stock images for testing
TEST_IMAGE_URLS = {
    "mixed_traffic": "https://raw.githubusercontent.com/ultralytics/yolov5/master/data/images/bus.jpg",
    "bike_helmet": "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/basketball2.png", # small demo placeholder
}

def generate_test_images():
    """Generate synthetic test cases for edge cases (blurry, large, empty, noise, etc.)."""
    print("Generating synthetic test images...")

    # 1. Empty/Black image
    img_empty = np.zeros((640, 640, 3), dtype=np.uint8)
    cv2.imwrite(os.path.join(TEST_DIR, "empty_road.jpg"), img_empty)

    # 2. Large image
    img_large = np.zeros((3000, 2000, 3), dtype=np.uint8)
    cv2.rectangle(img_large, (500, 500), (1500, 1500), (100, 255, 100), -1) # fake green block
    cv2.imwrite(os.path.join(TEST_DIR, "large_image.jpg"), img_large)

    # 3. Small image
    img_small = np.zeros((50, 50, 3), dtype=np.uint8)
    cv2.imwrite(os.path.join(TEST_DIR, "small_image.jpg"), img_small)

    # 4. Blurry image
    img_blurry = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    img_blurry = cv2.GaussianBlur(img_blurry, (25, 25), 0)
    cv2.imwrite(os.path.join(TEST_DIR, "blurry_image.jpg"), img_blurry)

    # 5. Random noise image
    img_noise = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    cv2.imwrite(os.path.join(TEST_DIR, "noise_image.jpg"), img_noise)

    # Download real image helpers
    for name, url in TEST_IMAGE_URLS.items():
        try:
            print(f"Downloading {name} image from {url}...")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                with open(os.path.join(TEST_DIR, f"{name}.jpg"), "wb") as f:
                    f.write(resp.content)
            else:
                print(f"Failed to download {name} (status {resp.status_code})")
        except Exception as exc:
            print(f"Error downloading {name}: {exc}")

def run_tests():
    """Run tests against the FastAPI application."""
    print("\n" + "="*50)
    print("  RUNNING PIPELINE INTEGRATION TESTS")
    print("="*50)

    # Check health endpoint
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Health check status: {r.status_code}")
        print(f"Health response: {r.json()}\n")
    except Exception as exc:
        print(f"Server is not running or health check failed: {exc}")
        sys.exit(1)

    test_files = [f for f in os.listdir(TEST_DIR) if f.endswith(".jpg")]
    failed_tests = []

    for idx, filename in enumerate(test_files, 1):
        filepath = os.path.join(TEST_DIR, filename)
        print(f"Test {idx}/{len(test_files)}: '{filename}'")

        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f, "image/jpeg")}
                start_t = time.time()
                r = requests.post(f"{API_URL}/analyze", files=files, timeout=30)
                duration = time.time() - start_t

            print(f"  Response Code : {r.status_code} ({duration:.2f}s)")
            if r.status_code == 200:
                res = r.json()
                print(f"  Status        : {res.get('status')}")
                summary = res.get('summary', {})
                print(f"  Summary       : {summary}")
                print(f"  Vehicles      : {len(res.get('vehicles', []))}")
                print(f"  Violations    : {len(res.get('violations', []))}")
                print(f"  Plates        : {len(res.get('numberplates', []))}")
                if res.get("annotated_image"):
                    print("  Annotated Img : Yes (Base64 string present)")
                else:
                    print("  Annotated Img : No (Empty/None)")
            else:
                print(f"  Error Detail  : {r.text}")
                failed_tests.append(filename)
        except Exception as exc:
            print(f"  Crashed       : {exc}")
            failed_tests.append(filename)
        print("-" * 50)

    print("\n" + "="*50)
    if failed_tests:
        print(f"❌ TESTS FAILED: {len(failed_tests)} failures: {failed_tests}")
        sys.exit(1)
    else:
        print("✅ ALL TEST SCENARIOS PASSED SUCCESSFULLY!")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run-only":
        run_tests()
    else:
        generate_test_images()
        run_tests()
