# 🚦 Bengaluru Gridlock Optimizer

Automated AI Traffic Violation Detection System. This repository is containerized using Docker, making it easy to run locally, develop, and push contributions.

---

## 🚀 Quick Start (Local Setup)

Follow these steps to get the application running on your local machine.

### 📋 Prerequisites
Make sure you have the following installed:
- [Git](https://git-scm.com/)
- [Docker](https://docs.docker.com/get-docker/) (Recommended)
- [Python 3.10+](https://www.python.org/) (Optional, only required if running locally without Docker)

---

### 🏃‍♂️ Running with Docker (Recommended)

Since the application is fully Dockerized, this is the easiest way to run it without worrying about Python versions or system dependencies (like OpenCV or EasyOCR library dependencies).

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SaitejaKommi/Bengaluru-Gridlock-Optimizer.git
   cd Bengaluru-Gridlock-Optimizer
   ```

2. **Navigate to the application folder:**
   ```bash
   cd traffic-app
   ```

3. **Build the Docker image:**
   ```bash
   docker build -t traffic-violation-detector .
   ```

4. **Run the Docker container:**
   ```bash
   docker run -p 7860:7860 traffic-violation-detector
   ```

5. **Access the application:**
   Open your browser and navigate to:
   👉 **[http://localhost:7860](http://localhost:7860)**

> [!TIP]
> **Using Fine-Tuned Weights:**
> If you have fine-tuned model weights (e.g., `vehicle_best.pt`, `helmet_best.pt`, `seatbelt_best.pt`, `plate_best.pt`), place them in the `traffic-app/backend/models/` folder *before* building the Docker image. If not provided, the app will automatically fall back to standard `yolov8n.pt`/`yolov8s.pt` models.

---

### 🐍 Running with Local Python (Alternative)

If you prefer to run it without Docker directly in your host environment:

1. **Navigate to the application directory:**
   ```bash
   cd traffic-app
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Create venv
   python3 -m venv venv
   
   # Activate venv (Linux/macOS)
   source venv/bin/activate
   
   # Activate venv (Windows)
   # venv\Scripts\activate
   ```
   > [!NOTE]
   > The virtual environment folder (`venv/`) is already added to `.gitignore`, so it won't be tracked or pushed to the repository.

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI server:**
   ```bash
   uvicorn backend.app:app --host 0.0.0.0 --port 7860 --reload
   ```

5. **Access the app** at `http://localhost:7860`.

---

## 🛠️ Contributing & Pushing Changes

To contribute to the project and push your changes back to GitHub, follow this workflow:

1. **Stay updated:**
   Before making changes, pull the latest code:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create a new branch:**
   Create a branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make and verify your changes:**
   - Make your edits to the codebase.
   - Run the application locally (via Docker or Python) to verify everything works.

4. **Commit your changes:**
   ```bash
   # Check which files were modified/added
   git status

   # Stage the changes
   git add .

   # Commit with a clear message
   git commit -m "feat: described your additions/changes"
   ```

5. **Push to GitHub:**
   Push your local branch to the remote repository:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request (PR):**
   Go to the [GitHub repository page](https://github.com/SaitejaKommi/Bengaluru-Gridlock-Optimizer) and click **Compare & pull request** to submit your changes for review.

---

## 📁 Project Structure

```text
Bengaluru-Gridlock-Optimizer/
├── traffic-app/
│   ├── backend/             # FastAPI backend (services, pipeline, API)
│   │   ├── app.py
│   │   └── models/          # Drop fine-tuned weights here
│   ├── frontend/            # Single-page UI (HTML/JS/CSS)
│   ├── Dockerfile           # Docker configuration
│   ├── requirements.txt     # Python dependencies
│   └── README.md            # App details & API reference
└── README.md                # This setup guide
```
