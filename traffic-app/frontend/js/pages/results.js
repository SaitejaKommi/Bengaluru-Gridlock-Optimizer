/**
 * results.js — Results Page View Controller.
 */
import { AppState, router } from '../app.js';

export function renderResults() {
  // Security Redirect: If direct visit without upload data, route back to upload
  if (!AppState.analysisResult) {
    setTimeout(() => {
      router.navigate('/upload');
    }, 0);
    const fallback = document.createElement('div');
    fallback.style.padding = '40px';
    fallback.innerHTML = '<p style="text-align:center;color:var(--ink-60);">No analysis context loaded. Redirecting...</p>';
    return fallback;
  }

  const data = AppState.analysisResult;
  const s = data.summary || {};
  const violations = data.violations || [];
  const plates = data.numberplates || [];
  const vehicles = data.vehicles || [];

  const container = document.createElement('div');
  container.className = 'page results-container';

  // 1. Compile pills data
  const pills = [
    { val: s.total_vehicles   ?? 0, label: 'Vehicles', cls: 'blue'   },
    { val: s.motorcycles      ?? 0, label: 'Motorcycles', cls: '' },
    { val: s.cars             ?? 0, label: 'Cars / Buses', cls: '' },
    { val: s.violations_count ?? 0, label: 'Violations', cls: (s.violations_count > 0) ? 'danger' : 'safe' },
    { val: s.plates_read      ?? 0, label: 'Plates Read', cls: '' },
  ];

  const summaryStripHtml = pills.map(p => `
    <div class="sum-pill ${p.cls}">
      <div class="sum-pill-val">${p.val}</div>
      <div class="sum-pill-label">${p.label}</div>
    </div>
  `).join('');

  // 2. Original / Annotated images
  const originalSrc = AppState.previewUrl || '';
  const annotatedSrc = data.annotated_image 
    ? 'data:image/png;base64,' + data.annotated_image 
    : originalSrc;

  // 3. Violations
  let violationsHtml = '';
  if (!violations.length) {
    violationsHtml = `
      <div class="no-violations">
        <div class="no-v-icon">✅</div>
        <div>
          <div class="no-v-title">No Violations Detected</div>
          <div class="no-v-sub">All detected vehicles appear to be compliant in this image.</div>
        </div>
      </div>`;
  } else {
    const icons = {
      'No Helmet':    { icon: '🪖', desc: 'Motorcycle rider detected without helmet' },
      'No Seatbelt':  { icon: '🔒', desc: 'Vehicle occupant detected without seatbelt' },
      'Triple Riding':{ icon: '🏍️', desc: 'Motorcycle carrying 3 or more riders' },
      'Mobile Usage': { icon: '📱', desc: 'Driver detected using mobile phone while driving' },
    };

    violationsHtml = '<div class="violations-grid">';
    violations.forEach(v => {
      const info = icons[v.type] || { icon: '⚠️', desc: v.description || '' };
      const conf = v.confidence ? Math.round(v.confidence * 100) : null;
      const confLabel = conf && conf > 75 ? 'high' : conf && conf > 50 ? 'medium' : 'high';
      const confText  = conf && conf > 75 ? 'High Confidence' : conf && conf > 50 ? 'Medium' : 'Detected';

      // Cross reference vehicle types
      const veh = vehicles.find(vv => vv.id === v.vehicle_id);
      const vtype = veh ? capitalize(veh.type) : 'Vehicle #' + v.vehicle_id;

      violationsHtml += `
        <div class="violation-card">
          <div class="vc-top">
            <div class="vc-icon">${info.icon}</div>
            <div class="vc-badge ${confLabel}">${confText}</div>
          </div>
          <div class="vc-type">${escHtml(v.type)}</div>
          <div class="vc-desc">${escHtml(info.desc)}</div>
          <div class="vc-meta">
            <div class="vc-vehicle">🚗 ${escHtml(vtype)}</div>
            ${conf ? `<div class="vc-conf">Confidence: <span>${conf}%</span></div>` : ''}
          </div>
        </div>`;
    });
    violationsHtml += '</div>';
  }

  // 4. Plates
  let platesSectHtml = '';
  const validPlates = plates.filter(p => p.text && p.text.trim());
  if (validPlates.length > 0) {
    const platesCardsHtml = validPlates.map(p => `
      <div class="plate-card">
        <div class="plate-card-label">🔢 Number Plate — Vehicle #${p.vehicle_id}</div>
        <div class="plate-number">${escHtml(p.text)}</div>
        <div class="plate-meta">
          <div class="plate-meta-item">Detection: <strong>${Math.round(p.confidence * 100)}%</strong></div>
          <div class="plate-meta-item">OCR: <strong>${Math.round(p.ocr_confidence * 100)}%</strong></div>
        </div>
      </div>
    `).join('');

    platesSectHtml = `
      <div class="sec-label">
        <span class="sec-label-text">Number Plates</span>
        <div class="sec-divider"></div>
      </div>
      <div class="plates-row">${platesCardsHtml}</div>
    `;
  }

  // 5. Evidence report
  const hasViolations = violations.length > 0;
  const ts = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: true });
  
  const primaryPlate = plates.find(p => p.text) || null;
  const plateText = primaryPlate ? primaryPlate.text : 'Not Detected';
  const uniqueVtypes = [...new Set(vehicles.map(v => capitalize(v.type)))];
  const vtypeStr = uniqueVtypes.length ? uniqueVtypes.join(', ') : 'None';

  const vioRows = violations.length
    ? violations.map(v => `
        <div class="ev-vrow">
          <span>⚠️</span>
          <span>${escHtml(v.type)} — Vehicle #${v.vehicle_id}</span>
          ${v.confidence ? `<span style="margin-left:auto;font-size:0.75rem;opacity:0.8;">${Math.round(v.confidence*100)}%</span>` : ''}
        </div>`).join('')
    : `<div class="ev-vrow ok"><span>✅</span><span>No violations detected</span></div>`;

  const evidenceReportHtml = `
    <div class="evidence-card">
      <div class="evidence-header">
        <div class="evidence-header-left">
          <div class="evidence-logo">🏛️</div>
          <div>
            <div class="evidence-header-title">Traffic Violation Evidence Report</div>
            <div class="evidence-header-sub">AI-Generated · ${ts}</div>
          </div>
        </div>
        <div class="evidence-status-badge ${hasViolations ? 'violation' : 'clear'}">
          ${hasViolations ? '⚠️ Violation Found' : '✅ Clear'}
        </div>
      </div>
      <div class="evidence-body">
        <div class="evidence-grid">
          <div>
            <div class="ev-field-label">Vehicle Types</div>
            <div class="ev-field-val">${escHtml(vtypeStr)}</div>
          </div>
          <div>
            <div class="ev-field-label">Total Vehicles</div>
            <div class="ev-field-val">${s.total_vehicles ?? 0}</div>
          </div>
          <div>
            <div class="ev-field-label">Number Plate</div>
            <div class="ev-field-val">${escHtml(plateText)}</div>
          </div>
          <div>
            <div class="ev-field-label">Total Violations</div>
            <div class="ev-field-val" style="color:${hasViolations ? 'var(--red)' : 'var(--green)'}">
              ${violations.length}
            </div>
          </div>
          <div>
            <div class="ev-field-label">Timestamp</div>
            <div class="ev-field-val" style="font-size:0.82rem;">${ts}</div>
          </div>
          <div>
            <div class="ev-field-label">Evidence Status</div>
            <div class="ev-field-val" style="color:${hasViolations ? 'var(--red)' : 'var(--green)'}">
              ${hasViolations ? 'Violation Record' : 'Compliant'}
            </div>
          </div>
        </div>
        <div class="evidence-violations-list">
          ${vioRows}
        </div>
      </div>
    </div>
  `;

  // Combine into final document structure
  container.innerHTML = `
    <!-- Summary strip -->
    <div class="summary-strip">${summaryStripHtml}</div>

    <!-- Image comparison -->
    <div class="sec-label">
      <span class="sec-label-text">Evidence Images</span>
      <div class="sec-divider"></div>
    </div>
    <div class="img-compare">
      <div class="img-panel">
        <div class="img-panel-head">
          <div class="h-dot" style="background:#60a5fa;"></div>
          Original Upload
        </div>
        <img src="${originalSrc}" alt="Original image" />
      </div>
      <div class="img-panel">
        <div class="img-panel-head">
          <div class="h-dot" style="background:#f97316;"></div>
          Annotated Evidence
        </div>
        <img src="${annotatedSrc}" alt="Annotated image" />
      </div>
    </div>

    <!-- Violations List -->
    <div class="sec-label">
      <span class="sec-label-text">Violations Detected</span>
      <div class="sec-divider"></div>
    </div>
    <div id="violations-container">${violationsHtml}</div>

    <!-- Plates List -->
    <div id="plates-container">${platesSectHtml}</div>

    <!-- Evidence Report Block -->
    <div class="sec-label">
      <span class="sec-label-text">Evidence Report</span>
      <div class="sec-divider"></div>
    </div>
    <div id="evidence-container">${evidenceReportHtml}</div>

    <!-- Action Bar -->
    <div class="results-actions">
      <button class="download-report-btn" id="print-report-btn">
        📄 Download PDF Report
      </button>
      <button class="new-analysis-btn" id="new-analysis-btn">
        📸 Analyze Another Image
      </button>
    </div>
  `;

  // Bind actions
  setTimeout(() => {
    const printBtn = container.querySelector('#print-report-btn');
    if (printBtn) {
      printBtn.addEventListener('click', () => {
        window.print();
      });
    }

    const nextBtn = container.querySelector('#new-analysis-btn');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        router.navigate('/upload');
      });
    }
  }, 0);

  return container;
}

// Format Helpers
function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : str;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
