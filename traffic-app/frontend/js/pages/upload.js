/**
 * upload.js — Image Upload & Active Analysis view controller.
 */
import { AppState, router } from '../app.js';

export function renderUpload() {
  const container = document.createElement('div');
  container.className = 'page';

  container.innerHTML = `
    <!-- Upload Card -->
    <section class="upload-section" id="upload-card-wrapper" style="display: ${AppState.isAnalyzing ? 'none' : 'block'};">
      <div class="upload-card">
        <div class="upload-card-title">Upload Traffic Image</div>
        <div class="upload-card-sub">Supports JPG, PNG, WEBP — Max 20 MB</div>

        <!-- Drop zone -->
        <div id="drop-zone">
          <input type="file" id="file-input" accept="image/*" />
          <div id="drop-hint">
            <div class="dz-icon">📸</div>
            <div class="dz-title"><strong>Click to upload</strong> or drag &amp; drop</div>
            <div class="dz-sub">High-resolution images give better results</div>
          </div>
          <div id="preview-area">
            <img id="preview-img" alt="Image preview" />
            <div class="preview-meta">
              <span id="preview-name"></span>
              <button id="change-btn">↩ Change</button>
            </div>
          </div>
        </div>

        <div id="error-box"></div>

        <button id="analyze-btn" disabled>
          🔍 &nbsp;Analyze Image
        </button>
      </div>
    </section>

    <!-- Processing Loader State -->
    <section id="analysis-state-wrapper" style="display: ${AppState.isAnalyzing ? 'block' : 'none'};">
      <div id="analysis-state">
        <div class="analysis-anim">
          <div class="analysis-ring"></div>
          <div class="analysis-ring-2"></div>
          <div class="analysis-core">🤖</div>
        </div>
        <div class="analysis-title">Analyzing Image…</div>
        <p style="font-size:0.875rem;color:var(--ink-60);margin-bottom:8px;">
          Running AI pipeline on your image
        </p>
        <div class="analysis-steps">
          <div class="a-step" id="step-vehicle">
            <span class="a-step-icon">🚗</span> Vehicle Detection
          </div>
          <div class="a-step" id="step-helmet">
            <span class="a-step-icon">🪖</span> Helmet &amp; Rider Check
          </div>
          <div class="a-step" id="step-seatbelt">
            <span class="a-step-icon">🔒</span> Seatbelt Detection
          </div>
          <div class="a-step" id="step-plate">
            <span class="a-step-icon">🔢</span> Number Plate OCR
          </div>
          <div class="a-step" id="step-report">
            <span class="a-step-icon">📋</span> Generating Report
          </div>
        </div>
      </div>
    </section>
  `;

  // Grab DOM references relative to container
  const uploadWrapper = container.querySelector('#upload-card-wrapper');
  const loaderWrapper = container.querySelector('#analysis-state-wrapper');
  const dropZone       = container.querySelector('#drop-zone');
  const fileInput      = container.querySelector('#file-input');
  const dropHint       = container.querySelector('#drop-hint');
  const previewArea    = container.querySelector('#preview-area');
  const previewImg     = container.querySelector('#preview-img');
  const previewName    = container.querySelector('#preview-name');
  const changeBtn      = container.querySelector('#change-btn');
  const analyzeBtn     = container.querySelector('#analyze-btn');
  const errorBox       = container.querySelector('#error-box');

  const steps = ['step-vehicle', 'step-helmet', 'step-seatbelt', 'step-plate', 'step-report'];

  // Restore file state if previously selected and not currently loading
  if (AppState.selectedFile && !AppState.isAnalyzing) {
    displayPreview(AppState.selectedFile, AppState.previewUrl);
  }

  // Bind Event Listeners
  dropZone.addEventListener('click', () => {
    if (!AppState.selectedFile) fileInput.click();
  });

  fileInput.addEventListener('change', e => {
    if (e.target.files.length) handleFileSelect(e.target.files[0]);
  });

  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length) handleFileSelect(e.dataTransfer.files[0]);
  });

  changeBtn.addEventListener('click', e => {
    e.stopPropagation();
    resetUploadState();
    fileInput.click();
  });

  analyzeBtn.addEventListener('click', () => {
    executeAnalysis();
  });

  function handleFileSelect(file) {
    if (!file || !file.type.startsWith('image/')) {
      showError('Please select a valid image file (JPG, PNG, WEBP).');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      showError('File too large. Maximum size is 20 MB.');
      return;
    }

    AppState.selectedFile = file;
    AppState.previewUrl = URL.createObjectURL(file);
    displayPreview(file, AppState.previewUrl);
    hideError();
  }

  function displayPreview(file, url) {
    previewImg.src = url;
    previewName.textContent = file.name;
    dropHint.style.display = 'none';
    previewArea.style.display = 'flex';
    analyzeBtn.disabled = false;
  }

  function resetUploadState() {
    AppState.selectedFile = null;
    AppState.previewUrl = null;
    fileInput.value = '';
    previewImg.src = '';
    previewArea.style.display = 'none';
    dropHint.style.display = '';
    analyzeBtn.disabled = true;
  }

  function showError(msg) {
    errorBox.textContent = '⚠️  ' + msg;
    errorBox.style.display = 'block';
  }

  function hideError() {
    errorBox.style.display = 'none';
  }

  async function executeAnalysis() {
    if (!AppState.selectedFile) return;

    AppState.isAnalyzing = true;
    AppState.error = null;
    AppState.analysisResult = null;

    // Transition view layout
    uploadWrapper.style.display = 'none';
    loaderWrapper.style.display = 'block';

    // Start progress loader ticks
    animateProcessingSteps();

    const form = new FormData();
    form.append('file', AppState.selectedFile);

    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        body: form
      });

      if (!response.ok) {
        const errPayload = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errPayload.detail || `Server error ${response.status}`);
      }

      const data = await response.json();

      // Graceful animation delay
      await new Promise(r => setTimeout(r, 600));

      AppState.analysisResult = data;
      AppState.isAnalyzing = false;

      // Navigate to Results page
      router.navigate('/results');
    } catch (err) {
      console.error('Analysis execution failed:', err);
      AppState.isAnalyzing = false;
      AppState.error = err.message;

      // Reset view to upload with errors
      loaderWrapper.style.display = 'none';
      uploadWrapper.style.display = 'block';
      showError(`Analysis failed: ${err.message}`);
    }
  }

  function animateProcessingSteps() {
    steps.forEach(id => {
      const stepEl = container.querySelector(`#${id}`);
      if (stepEl) stepEl.className = 'a-step';
    });

    let index = 0;
    const interval = setInterval(() => {
      if (!AppState.isAnalyzing) {
        clearInterval(interval);
        return;
      }

      if (index > 0) {
        const prevEl = container.querySelector(`#${steps[index - 1]}`);
        if (prevEl) prevEl.classList.replace('active', 'done');
      }

      if (index < steps.length) {
        const activeEl = container.querySelector(`#${steps[index]}`);
        if (activeEl) activeEl.classList.add('active');
        index++;
      } else {
        clearInterval(interval);
      }
    }, 600);
  }

  return container;
}
