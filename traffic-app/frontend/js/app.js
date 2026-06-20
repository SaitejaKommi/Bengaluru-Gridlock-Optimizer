/**
 * app.js — Main frontend coordinator and global state store.
 */
import { Router } from './router.js';
import { renderLanding } from './pages/landing.js';
import { renderUpload } from './pages/upload.js';
import { renderResults } from './pages/results.js';

// Central Global Application State
export const AppState = {
  selectedFile: null,      // Image File object
  previewUrl: null,        // Object URL of local image preview
  isAnalyzing: false,      // Analysis request loading state
  analysisResult: null,    // JSON payload from /analyze
  error: null,             // Analysis error message
};

// Router configurations
const routes = {
  '/': renderLanding,
  '/upload': renderUpload,
  '/results': renderResults,
};

export let router;

// Bootstrap application on load
document.addEventListener('DOMContentLoaded', () => {
  router = new Router(routes, 'view-outlet');
  router.init();

  // Logo navigation home
  const logo = document.querySelector('.nav-logo');
  if (logo) {
    logo.style.cursor = 'pointer';
    logo.addEventListener('click', () => {
      router.navigate('/');
    });
  }

  // Navbar CTA button navigation
  const navStartBtn = document.getElementById('nav-start-btn');
  if (navStartBtn) {
    navStartBtn.addEventListener('click', () => {
      router.navigate('/upload');
    });
  }
});
