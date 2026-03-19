from __future__ import annotations

from html import escape

REPO_URL = "https://github.com/Parad0x-Labs/nulla-hive-mind"
DOCS_URL = f"{REPO_URL}/blob/main/docs/README.md"
STATUS_URL = f"{REPO_URL}/blob/main/docs/STATUS.md"
INSTALL_URL = f"{REPO_URL}/blob/main/docs/INSTALL.md"


def public_site_base_styles() -> str:
    return """
:root {
  --bg: #050816;
  --bg-alt: #0a1122;
  --surface: rgba(10, 16, 30, 0.84);
  --surface2: rgba(14, 22, 40, 0.92);
  --surface3: rgba(19, 30, 54, 0.96);
  --border: rgba(158, 174, 220, 0.16);
  --border-hover: rgba(169, 128, 255, 0.42);
  --text: #eef2ff;
  --text-muted: #a8b4d2;
  --text-dim: #7784a8;
  --accent: #9c7dff;
  --accent2: #5fd0ff;
  --green: #64e0a7;
  --orange: #f2ae62;
  --blue: #6cbcff;
  --purple: #b392ff;
  --red: #ff7b92;
  --pink: #ff83d4;
  --radius: 18px;
  --radius-sm: 12px;
  --shadow: 0 28px 84px rgba(0, 0, 0, 0.36);
  --font-ui: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
  --font-display: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
}
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-height: 100vh;
  font-family: var(--font-ui);
  color: var(--text);
  background:
    radial-gradient(circle at 14% 18%, rgba(156, 125, 255, 0.18), transparent 24%),
    radial-gradient(circle at 86% 12%, rgba(95, 208, 255, 0.16), transparent 22%),
    radial-gradient(circle at 50% 100%, rgba(255, 131, 212, 0.08), transparent 20%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-alt) 100%);
  -webkit-font-smoothing: antialiased;
  position: relative;
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(255,255,255,0.028) 1px, transparent 1px),
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 26px 26px;
  opacity: 0.28;
}
body::after {
  content: "";
  position: fixed;
  inset: auto auto 4% -40px;
  width: 260px;
  height: 260px;
  pointer-events: none;
  border-radius: 46% 54% 58% 42% / 46% 40% 60% 54%;
  background:
    radial-gradient(circle at 40% 38%, rgba(156, 125, 255, 0.22), transparent 42%),
    radial-gradient(circle at 72% 62%, rgba(95, 208, 255, 0.18), transparent 38%);
  filter: blur(12px);
  opacity: 0.82;
}
a {
  color: var(--blue);
  text-decoration: none;
}
a:hover { color: var(--accent2); }
.ns-shell {
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
}
.ns-header {
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(16px) saturate(1.25);
  -webkit-backdrop-filter: blur(16px) saturate(1.25);
  background: rgba(5, 8, 22, 0.72);
  border-bottom: 1px solid rgba(158, 174, 220, 0.12);
}
.ns-header-inner {
  min-height: 72px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
}
.ns-brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: var(--text);
}
.ns-brand:hover { color: var(--text); }
.ns-brand-mark {
  width: 38px;
  height: 38px;
  position: relative;
  border-radius: 14px;
  border: 1px solid rgba(156, 125, 255, 0.28);
  background: linear-gradient(135deg, rgba(156, 125, 255, 0.18), rgba(95, 208, 255, 0.08));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
}
.ns-brand-mark::before,
.ns-brand-mark::after {
  content: "";
  position: absolute;
  top: 8px;
  width: 13px;
  height: 18px;
  border-radius: 58% 42% 60% 40% / 54% 46% 52% 48%;
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.88), rgba(156, 125, 255, 0.78));
  box-shadow: 0 0 18px rgba(156, 125, 255, 0.24);
}
.ns-brand-mark::before {
  left: 7px;
  transform: rotate(-22deg);
}
.ns-brand-mark::after {
  right: 7px;
  transform: rotate(22deg);
}
.ns-brand-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ns-brand-title {
  font-family: var(--font-display);
  font-size: 26px;
  line-height: 1;
  letter-spacing: -0.04em;
}
.ns-brand-subtitle {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--text-dim);
}
.ns-nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
.ns-nav a {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  color: var(--text-muted);
  border: 1px solid transparent;
  transition: border-color 0.18s ease, background 0.18s ease, color 0.18s ease, transform 0.18s ease;
}
.ns-nav a:hover,
.ns-nav a:focus-visible {
  color: var(--text);
  border-color: rgba(156, 125, 255, 0.24);
  background: rgba(255,255,255,0.04);
  outline: none;
  transform: translateY(-1px);
}
.ns-nav a.is-active {
  color: var(--text);
  border-color: rgba(156, 125, 255, 0.28);
  background: rgba(156, 125, 255, 0.12);
}
.ns-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
}
.ns-ghost-link {
  color: var(--text-dim);
  font-size: 13px;
}
.ns-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 700;
  color: #04101c;
  background: linear-gradient(135deg, var(--accent2), #9cf1ff);
  box-shadow: 0 14px 38px rgba(95, 208, 255, 0.18);
}
.ns-button:hover { color: #04101c; transform: translateY(-1px); }
.ns-button--secondary {
  color: var(--text);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(158, 174, 220, 0.18);
  box-shadow: none;
}
.ns-button--secondary:hover { color: var(--text); }
.ns-footer {
  margin: 44px auto 28px;
  padding: 20px 0 0;
  border-top: 1px solid rgba(158, 174, 220, 0.12);
}
.ns-footer-inner {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  justify-content: space-between;
}
.ns-footer-copy {
  color: var(--text-dim);
  font-size: 13px;
}
.ns-footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.ns-footer-links a {
  color: var(--text-muted);
  font-size: 13px;
}
@media (max-width: 980px) {
  .ns-header-inner {
    grid-template-columns: 1fr;
    padding: 14px 0;
  }
  .ns-nav,
  .ns-header-actions {
    justify-content: flex-start;
  }
}
"""


def render_landing_header() -> str:
    return _render_header(
        nav_items=(
            ('/', 'Home', True, ''),
            ('#how-it-works', 'How it works', False, ''),
            ('#status', 'Status', False, ''),
            (DOCS_URL, 'Docs', False, ' target="_blank" rel="noreferrer noopener"'),
            (REPO_URL, 'GitHub', False, ' target="_blank" rel="noreferrer noopener"'),
        ),
        primary_cta_href=INSTALL_URL,
        primary_cta_label="Get NULLA",
    )


def render_surface_header(*, active: str) -> str:
    active_key = str(active or "").strip().lower()
    return _render_header(
        nav_items=(
            ('/', 'Home', active_key == 'home', ''),
            ('/feed', 'Feed', active_key == 'feed', ' data-tab="feed"'),
            ('/tasks', 'Tasks', active_key == 'tasks', ' data-tab="tasks"'),
            ('/agents', 'Agents', active_key == 'agents', ' data-tab="agents"'),
            ('/proof', 'Proof', active_key == 'proof', ' data-tab="proof"'),
            ('/hive', 'Hive', active_key == 'hive', ' data-tab="hive"'),
        ),
        primary_cta_href=INSTALL_URL,
        primary_cta_label="Get NULLA",
        ghost_href=DOCS_URL,
        ghost_label="Docs",
    )


def render_public_site_footer() -> str:
    return f"""
<footer class="ns-footer">
  <div class="ns-shell ns-footer-inner">
    <div class="ns-footer-copy">NULLA · local-first AI with memory, tools, and trusted reach.</div>
    <div class="ns-footer-links">
      <a href="{escape(STATUS_URL, quote=True)}" target="_blank" rel="noreferrer noopener">Status</a>
      <a href="{escape(DOCS_URL, quote=True)}" target="_blank" rel="noreferrer noopener">Docs</a>
      <a href="{escape(REPO_URL, quote=True)}" target="_blank" rel="noreferrer noopener">GitHub</a>
    </div>
  </div>
</footer>
"""


def _render_header(
    *,
    nav_items: tuple[tuple[str, str, bool, str], ...],
    primary_cta_href: str,
    primary_cta_label: str,
    ghost_href: str | None = None,
    ghost_label: str | None = None,
) -> str:
    nav_parts: list[str] = []
    for href, label, active, attrs in nav_items:
        active_attr = ' class="is-active"' if active else ""
        nav_parts.append(
            f'<a href="{escape(href, quote=True)}"{attrs}{active_attr}>{escape(label)}</a>'
        )
    nav_html = "".join(nav_parts)
    ghost_html = ""
    if ghost_href and ghost_label:
        ghost_html = (
            f'<a class="ns-ghost-link" href="{escape(ghost_href, quote=True)}" target="_blank" '
            f'rel="noreferrer noopener">{escape(ghost_label)}</a>'
        )
    return f"""
<header class="ns-header">
  <div class="ns-shell ns-header-inner">
    <a class="ns-brand" href="/">
      <span class="ns-brand-mark" aria-hidden="true"></span>
      <span class="ns-brand-copy">
        <span class="ns-brand-title">NULLA</span>
        <span class="ns-brand-subtitle">Local-first AI agent</span>
      </span>
    </a>
    <nav class="ns-nav" aria-label="Primary">
      {nav_html}
    </nav>
    <div class="ns-header-actions">
      {ghost_html}
      <a class="ns-button" href="{escape(primary_cta_href, quote=True)}" target="_blank" rel="noreferrer noopener">{escape(primary_cta_label)}</a>
    </div>
  </div>
</header>
"""
