/**
 * router.js — History API client-side router.
 */
export class Router {
  constructor(routes, outletId = 'view-outlet') {
    this.routes = routes;
    this.outlet = document.getElementById(outletId);

    // Monitor back / forward history events
    window.addEventListener('popstate', () => this.handleRouting());

    // Intercept client-side link clicks
    document.addEventListener('click', (e) => {
      const link = e.target.closest('[data-link]');
      if (link) {
        e.preventDefault();
        const href = link.getAttribute('href');
        this.navigate(href);
      }
    });
  }

  /**
   * Run the router for the current pathname at bootstrap.
   */
  init() {
    this.handleRouting();
  }

  /**
   * Programmatically navigate to a URL path.
   */
  async navigate(path) {
    if (window.location.pathname === path && this.outlet.children.length > 0) return;
    window.history.pushState(null, '', path);
    await this.handleRouting();
  }

  /**
   * Resolves routes, updates output, and resets view details.
   */
  async handleRouting() {
    const path = window.location.pathname;
    const handler = this.routes[path] || this.routes['/'];

    // Clear main layout container
    this.outlet.innerHTML = '';

    // Create wrapper with smooth transition fade-in effect
    const pageWrapper = document.createElement('div');
    pageWrapper.className = 'fade-in';

    try {
      const result = await handler();
      if (result instanceof HTMLElement) {
        pageWrapper.appendChild(result);
      } else if (typeof result === 'string') {
        pageWrapper.innerHTML = result;
      }
      this.outlet.appendChild(pageWrapper);
      window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (err) {
      console.error('Routing execution failed:', err);
      pageWrapper.innerHTML = `
        <div class="page" style="padding-top: 60px;">
          <div style="background: var(--red-bg); border: 1px solid var(--red-border); color: var(--red); padding: 20px; border-radius: var(--r-md); font-weight: 500;">
            <h3>Routing Failure</h3>
            <p style="margin-top: 8px; font-size: 0.9rem;">Could not initialize view: ${err.message}</p>
          </div>
        </div>`;
      this.outlet.appendChild(pageWrapper);
    }
  }
}
