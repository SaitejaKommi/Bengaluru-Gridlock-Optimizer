/**
 * landing.js — Landing Page Controller (v2 Redesign)
 * Premium split-screen hero + connected animated pipeline timeline.
 */
import { router } from '../app.js';

// ═══════════════════════════════════════════════════════
// SVG TRAFFIC SCENE — Shared base elements
// Represents a real traffic camera frame perspective
// ═══════════════════════════════════════════════════════
const SCENE_BASE = `
  <defs>
    <linearGradient id="skyG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#C5D8E8"/>
      <stop offset="100%" stop-color="#D9EAF4"/>
    </linearGradient>
    <linearGradient id="roadG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#607D8B"/>
      <stop offset="100%" stop-color="#4A5568"/>
    </linearGradient>
  </defs>

  <!-- Sky -->
  <rect width="340" height="190" fill="url(#skyG)"/>

  <!-- Background buildings — left cluster -->
  <rect x="0"  y="74" width="56" height="60" fill="#8FA8B8" opacity="0.6"/>
  <rect x="5"  y="82" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="20" y="82" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="35" y="82" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="5"  y="95" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="20" y="95" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>

  <!-- Background buildings — right cluster -->
  <rect x="283" y="58" width="57" height="76" fill="#8FA8B8" opacity="0.6"/>
  <rect x="290" y="68" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="306" y="68" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="322" y="68" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="290" y="82" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>
  <rect x="306" y="82" width="10" height="8"  fill="#90CAF9" opacity="0.45"/>

  <!-- Tree silhouette -->
  <rect x="74" y="116" width="4" height="18" fill="#6D4C41"/>
  <circle cx="76" cy="111" r="13" fill="#66BB6A" opacity="0.72"/>

  <!-- Footpath -->
  <rect y="132" width="340" height="10" fill="#D7CCC8"/>

  <!-- Road surface -->
  <rect y="142" width="340" height="48" fill="url(#roadG)"/>

  <!-- Lane markings — centre dashes -->
  <rect x="0"   y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="38"  y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="76"  y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="114" y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="152" y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="190" y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="228" y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="266" y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>
  <rect x="304" y="164" width="22" height="3" fill="#FDD835" opacity="0.75"/>

  <!-- ====== CAR (white sedan — no violation) ====== -->
  <rect x="50"  y="138" width="100" height="40" rx="3" fill="#ECEFF1"/>
  <rect x="66"  y="120" width="68"  height="22" rx="5" fill="#CFD8DC"/>
  <rect x="70"  y="123" width="28"  height="16" rx="2" fill="#90CAF9" opacity="0.62"/>
  <rect x="104" y="123" width="24"  height="16" rx="2" fill="#90CAF9" opacity="0.62"/>
  <circle cx="68"  cy="177" r="9" fill="#1C2833"/>
  <circle cx="68"  cy="177" r="4" fill="#566573"/>
  <circle cx="138" cy="177" r="9" fill="#1C2833"/>
  <circle cx="138" cy="177" r="4" fill="#566573"/>
  <rect x="50"  y="150" width="5" height="14" rx="2" fill="#FFF9C4"/>
  <rect x="148" y="150" width="5" height="14" rx="2" fill="#EF9A9A"/>

  <!-- ====== MOTORCYCLE + 2 RIDERS (violation scene) ====== -->
  <rect x="212" y="154" width="52" height="12" rx="2" fill="#B71C1C"/>
  <rect x="222" y="148" width="28" height="14" rx="2" fill="#C62828"/>
  <rect x="249" y="146" width="20" height="4"  rx="1" fill="#424242"/>
  <circle cx="218" cy="168" r="9" fill="#1C2833"/>
  <circle cx="218" cy="168" r="4" fill="#566573"/>
  <circle cx="258" cy="168" r="9" fill="#1C2833"/>
  <circle cx="258" cy="168" r="4" fill="#566573"/>
  <!-- Rider 1 body (front) -->
  <rect x="229" y="132" width="20" height="26" rx="3" fill="#37474F"/>
  <!-- Rider 1 — bare head (no helmet) -->
  <circle cx="239" cy="126" r="9" fill="#D4A574"/>
  <!-- Rider 2 body (pillion) -->
  <rect x="213" y="137" width="18" height="20" rx="3" fill="#455A64"/>
  <!-- Rider 2 — bare head (no helmet) -->
  <circle cx="222" cy="132" r="8" fill="#D4A574"/>

  <!-- Traffic signal -->
  <rect x="3"  y="104" width="5"  height="32" fill="#37474F"/>
  <rect x="0"  y="92"  width="20" height="28" rx="3" fill="#212121"/>
  <circle cx="10" cy="99"  r="5" fill="#EF5350"/>
  <circle cx="10" cy="109" r="5" fill="#FFF176" opacity="0.22"/>
  <circle cx="10" cy="119" r="5" fill="#66BB6A"  opacity="0.18"/>

  <!-- CCTV overlay — timestamp + REC -->
  <rect x="2"   y="2" width="52" height="14" rx="2" fill="#000000" opacity="0.55"/>
  <circle cx="9" cy="9" r="3" fill="#F44336"/>
  <text x="15" y="13" font-size="7" font-family="monospace" fill="#FFFFFF">REC</text>
  <rect x="272" y="2" width="66" height="14" rx="2" fill="#000000" opacity="0.55"/>
  <text x="276" y="12" font-size="7" font-family="monospace" fill="#FFFFFF">14:23:07</text>
`;

// Original frame (no overlays)
const ORIGINAL_SVG = `<svg viewBox="0 0 340 190" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">${SCENE_BASE}</svg>`;

// Annotated frame (detection bounding boxes + labels)
const ANNOTATED_SVG = `<svg viewBox="0 0 340 190" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">${SCENE_BASE}

  <!-- ======== AI DETECTION OVERLAYS ======== -->

  <!-- Car detection box (blue) -->
  <rect x="45" y="116" width="114" height="68" rx="1"
        fill="rgba(59,130,246,0.05)" stroke="#3B82F6" stroke-width="2"/>
  <rect x="45" y="105" width="72" height="13" rx="2" fill="#3B82F6"/>
  <text x="49" y="115" font-size="8.5" font-family="monospace" fill="#FFFFFF" font-weight="bold">car  0.91</text>

  <!-- Motorcycle + triple riding (red) -->
  <rect x="206" y="122" width="68" height="55" rx="1"
        fill="rgba(220,38,38,0.06)" stroke="#DC2626" stroke-width="2.5"/>
  <rect x="206" y="110" width="124" height="14" rx="2" fill="#DC2626"/>
  <text x="210" y="121" font-size="8.5" font-family="monospace" fill="#FFFFFF" font-weight="bold">triple_riding 0.88</text>

  <!-- No-helmet circle — rider 1 -->
  <circle cx="239" cy="126" r="13" fill="none" stroke="#F97316" stroke-width="2.5" stroke-dasharray="4,2"/>
  <rect x="232" y="109" width="85" height="12" rx="2" fill="#F97316"/>
  <text x="236" y="119" font-size="7.5" font-family="monospace" fill="#FFFFFF" font-weight="bold">no_helmet 0.94</text>

  <!-- License plate region (amber dashed) -->
  <rect x="210" y="160" width="54" height="14" rx="1"
        fill="rgba(245,158,11,0.10)" stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="4,2"/>
  <rect x="210" y="150" width="38" height="12" rx="1" fill="#F59E0B"/>
  <text x="214" y="160" font-size="7.5" font-family="monospace" fill="#FFFFFF" font-weight="bold">plate</text>

  <!-- CCTV re-render on top of overlays -->
  <rect x="2"   y="2" width="52" height="14" rx="2" fill="#000000" opacity="0.55"/>
  <circle cx="9" cy="9" r="3" fill="#F44336"/>
  <text x="15" y="13" font-size="7" font-family="monospace" fill="#FFFFFF">REC</text>
  <rect x="272" y="2" width="66" height="14" rx="2" fill="#000000" opacity="0.55"/>
  <text x="276" y="12" font-size="7" font-family="monospace" fill="#FFFFFF">14:23:07</text>
</svg>`;

// ═══════════════════════════════════════════════════════
// PIPELINE STEPS CONFIG
// ═══════════════════════════════════════════════════════
const PIPELINE_STEPS = [
  { num: '01', icon: '📸', label: 'Input Image',            tech: 'Camera Frame'       },
  { num: '02', icon: '🚗', label: 'Vehicle Detection',      tech: 'YOLOv8 Detector'   },
  { num: '03', icon: '⚠️', label: 'Violation Analysis',     tech: 'Rule-Based Engine'  },
  { num: '04', icon: '🔢', label: 'Plate Detection',        tech: 'YOLOv8 Localizer'  },
  { num: '05', icon: '📝', label: 'OCR Extraction',         tech: 'EasyOCR Engine'     },
  { num: '06', icon: '🖼️', label: 'Evidence Generation',   tech: 'OpenCV Annotation'  },
  { num: '07', icon: '📋', label: 'Final Report',           tech: 'Structured Output'  },
];

export function renderLanding() {
  const container = document.createElement('div');

  const pipelineHTML = PIPELINE_STEPS.map(step => `
    <div class="pl-node">
      <div class="pl-num">${step.num}</div>
      <div class="pl-icon-wrap">${step.icon}</div>
      <div class="pl-label">${step.label}</div>
      <div class="pl-tech">${step.tech}</div>
    </div>
  `).join('');

  container.innerHTML = `

    <!-- ════════════════ HERO ════════════════ -->
    <section class="lp-hero-section">
      <div class="page">
        <div class="lp-hero-split">

          <!-- LEFT — copy + CTAs -->
          <div class="lp-hero-left">

            <div class="lp-eyebrow">
              <span>🏆</span>
              <span>Flipkart Gridlock Hackathon 2.0</span>
              <span class="lp-eyebrow-sep"></span>
              <span>Theme 3</span>
            </div>

            <h1 class="lp-headline">
              From CCTV Frame<br/>To Court-Ready<br/>
              <span class="lp-accent">Evidence</span>
            </h1>

            <p class="lp-subtext">
              One traffic camera frame in, a complete violation report out.
              Detect helmet violations, seatbelt violations, mobile phone usage, triple riding, and extract number plates in under 3 seconds with confidence scores that can be reviewed and audited by humans.
            </p>

            <div class="lp-metrics-row">
              <div class="lp-metric-item">
                <span class="lp-metric-icon">⚡</span>
                <span class="lp-metric-text">&lt; 3s Processing</span>
              </div>
              <div class="lp-metric-sep"></div>
              <div class="lp-metric-item">
                <span class="lp-metric-icon">🧠</span>
                <span class="lp-metric-text">YOLOv8 + EasyOCR</span>
              </div>
              <div class="lp-metric-sep"></div>
              <div class="lp-metric-item">
                <span class="lp-metric-icon">📋</span>
                <span class="lp-metric-text">Human-Auditable Reports</span>
              </div>
            </div>

            <div class="lp-cta-row">
              <button class="lp-btn-primary" id="lp-start-btn">
                <svg class="btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px; vertical-align: -2.5px;">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  <path d="M8 13v1 M11 10v4 M14 7v7"></path>
                </svg>Start Analysis
              </button>
              <button class="lp-btn-ghost"   id="lp-pipeline-btn">View Pipeline ↓</button>
            </div>

            <div class="lp-vtag-row">
              <span class="lp-vtag">🪖 Helmet Detection</span>
              <span class="lp-vtag">🔒 Seatbelt Analysis</span>
              <span class="lp-vtag">📱 Mobile Usage Detection</span>
              <span class="lp-vtag">🏍️ Triple Riding Detection</span>
              <span class="lp-vtag">🔢 Number Plate OCR</span>
            </div>

          </div>

          <!-- RIGHT — showcase card -->
          <div class="lp-hero-right">
            <div class="lp-showcase">

              <!-- Mac-style window chrome -->
              <div class="lp-showcase-chrome">
                <span class="lp-chrome-dot lp-chrome-red"></span>
                <span class="lp-chrome-dot lp-chrome-amber"></span>
                <span class="lp-chrome-dot lp-chrome-green"></span>
                <span class="lp-chrome-title">Detection Preview</span>
                <span class="lp-live-badge">● Live</span>
              </div>

              <!-- Step 01: Original frame -->
              <div class="lp-sc-step lp-sc-step-img">
                <div class="lp-sc-label">
                  <span class="lp-sc-num">01</span>
                  Original Traffic Frame
                </div>
                <div class="lp-sc-img-wrap">${ORIGINAL_SVG}</div>
              </div>

              <!-- Processing arrow -->
              <div class="lp-sc-divider">
                <div class="lp-sc-track"><div class="lp-sc-particle"></div></div>
                <span class="lp-sc-divider-label">AI Processing Pipeline</span>
              </div>

              <!-- Step 02: Annotated frame -->
              <div class="lp-sc-step lp-sc-step-img">
                <div class="lp-sc-label">
                  <span class="lp-sc-num">02</span>
                  AI Annotated Detection
                </div>
                <div class="lp-sc-img-wrap">${ANNOTATED_SVG}</div>
              </div>

              <!-- Step 03: Violations + OCR -->
              <div class="lp-sc-results">

                <div class="lp-sc-violation">
                  <span class="lp-sc-vicon">⚠️</span>
                  <div class="lp-sc-vbody">
                    <div class="lp-sc-vtype">Triple Riding · No Helmet</div>
                    <div class="lp-sc-vconf">2 violations detected · 88–94% confidence</div>
                  </div>
                  <span class="lp-sc-vbadge">HIGH</span>
                </div>

                <div class="lp-sc-plate">
                  <span class="lp-sc-plate-icon">🔢</span>
                  <div class="lp-sc-plate-body">
                    <div class="lp-sc-plate-label">Plate Extracted via OCR</div>
                    <div class="lp-sc-plate-num">KA ·· ·· ····</div>
                  </div>
                  <span class="lp-sc-plate-conf">91%</span>
                </div>

              </div>

            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- ════════════════ PIPELINE ════════════════ -->
    <section class="lp-pipeline-section" id="pipeline-section">
      <div class="page">

        <div class="lp-pl-header">
          <h2 class="lp-pl-title">How the AI Pipeline Works</h2>
          <p class="lp-pl-desc">
            Seven sequential stages transform a raw traffic image into a
            structured, downloadable evidence report — all in under 3 seconds.
          </p>
        </div>

        <div class="lp-pl-scroll">
          <div class="lp-pl-nodes">
            ${pipelineHTML}
          </div>
        </div>

      </div>
    </section>

  `;

  // Bind events after render
  setTimeout(() => {
    const startBtn = container.querySelector('#lp-start-btn');
    if (startBtn) startBtn.addEventListener('click', () => router.navigate('/upload'));

    const pipelineBtn = container.querySelector('#lp-pipeline-btn');
    if (pipelineBtn) {
      pipelineBtn.addEventListener('click', () => {
        const target = document.getElementById('pipeline-section');
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  }, 0);

  return container;
}
