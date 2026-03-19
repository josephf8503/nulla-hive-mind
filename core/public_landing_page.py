from __future__ import annotations

from core.public_site_shell import (
    DOCS_URL,
    INSTALL_URL,
    REPO_URL,
    STATUS_URL,
    public_site_base_styles,
    render_landing_header,
    render_public_site_footer,
)


def render_public_landing_page_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>NULLA Hive Mind · Local-first AI agent</title>
<meta name="description" content="NULLA is a local-first AI agent with memory, tools, and optional trusted helpers. It starts on your machine and expands only when you choose."/>
<meta property="og:title" content="NULLA Hive Mind"/>
<meta property="og:description" content="Local-first AI with memory, tools, and trusted reach."/>
<meta property="og:type" content="website"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="NULLA Hive Mind"/>
<meta name="twitter:description" content="Start local. Stay in control. Expand only when you choose."/>
<style>
{public_site_base_styles()}
.nl-page {{
  padding: 28px 0 56px;
}}
.nl-hero {{
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 24px;
  padding: 42px;
  border: 1px solid rgba(158, 174, 220, 0.14);
  border-radius: 32px;
  background:
    radial-gradient(circle at 18% 20%, rgba(156, 125, 255, 0.16), transparent 26%),
    radial-gradient(circle at 88% 14%, rgba(95, 208, 255, 0.14), transparent 24%),
    linear-gradient(180deg, rgba(10, 16, 30, 0.92) 0%, rgba(6, 10, 22, 0.96) 100%);
  box-shadow: var(--shadow);
}}
.nl-hero::before {{
  content: "";
  position: absolute;
  inset: auto auto -48px -36px;
  width: 240px;
  height: 240px;
  border-radius: 46% 54% 62% 38% / 38% 42% 58% 62%;
  background:
    radial-gradient(circle at 38% 34%, rgba(156, 125, 255, 0.28), transparent 42%),
    radial-gradient(circle at 70% 66%, rgba(95, 208, 255, 0.24), transparent 36%);
  filter: blur(10px);
  opacity: 0.9;
}}
.nl-hero-copy,
.nl-hero-side {{
  position: relative;
  z-index: 1;
}}
.nl-eyebrow {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(158, 174, 220, 0.16);
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}}
.nl-eyebrow::before {{
  content: "";
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(95, 208, 255, 1) 0%, rgba(95, 208, 255, 0.18) 72%);
  box-shadow: 0 0 18px rgba(95, 208, 255, 0.3);
}}
.nl-hero h1 {{
  margin: 18px 0 14px;
  max-width: 11ch;
  font-family: var(--font-display);
  font-size: clamp(54px, 8vw, 92px);
  line-height: 0.92;
  letter-spacing: -0.06em;
}}
.nl-hero p {{
  margin: 0;
  max-width: 58ch;
  font-size: 17px;
  line-height: 1.7;
  color: var(--text-muted);
}}
.nl-hero-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}}
.nl-mini-note {{
  margin-top: 14px;
  color: var(--text-dim);
  font-size: 13px;
}}
.nl-hero-side {{
  display: grid;
  gap: 14px;
  align-content: start;
}}
.nl-side-card,
.nl-panel,
.nl-status-card,
.nl-surface-card {{
  background: rgba(14, 22, 40, 0.9);
  border: 1px solid rgba(158, 174, 220, 0.14);
  border-radius: 22px;
  box-shadow: var(--shadow);
}}
.nl-side-card {{
  padding: 18px 20px;
}}
.nl-side-label,
.nl-label {{
  color: var(--text-dim);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}}
.nl-side-card strong {{
  display: block;
  margin-top: 10px;
  font-size: 26px;
  font-family: var(--font-display);
  letter-spacing: -0.04em;
}}
.nl-side-card p {{
  margin: 8px 0 0;
  color: var(--text-muted);
  line-height: 1.65;
  font-size: 14px;
}}
.nl-one-lane {{
  display: grid;
  gap: 16px;
  margin: 26px 0 0;
  padding: 24px 26px;
}}
.nl-one-lane h2,
.nl-section h2,
.nl-builder h2 {{
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(30px, 5vw, 52px);
  line-height: 0.98;
  letter-spacing: -0.05em;
}}
.nl-one-lane p,
.nl-section-copy,
.nl-builder p {{
  margin: 0;
  color: var(--text-muted);
  line-height: 1.72;
  font-size: 15px;
}}
.nl-lane-rail {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}}
.nl-pill {{
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(158, 174, 220, 0.18);
  color: var(--text);
  font-weight: 600;
  font-size: 14px;
}}
.nl-arrow {{
  color: var(--accent2);
  font-size: 22px;
  line-height: 1;
}}
.nl-section {{
  margin-top: 22px;
  padding: 28px 0 0;
}}
.nl-section-head {{
  display: grid;
  gap: 10px;
  margin-bottom: 18px;
}}
.nl-grid-3,
.nl-grid-4 {{
  display: grid;
  gap: 16px;
}}
.nl-grid-3 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.nl-grid-4 {{
  grid-template-columns: repeat(4, minmax(0, 1fr));
}}
.nl-panel,
.nl-status-card,
.nl-surface-card {{
  padding: 20px;
}}
.nl-panel h3,
.nl-status-card h3,
.nl-surface-card h3 {{
  margin: 0 0 10px;
  font-size: 18px;
  letter-spacing: -0.03em;
}}
.nl-panel p,
.nl-status-card p,
.nl-surface-card p {{
  margin: 0;
  color: var(--text-muted);
  line-height: 1.68;
  font-size: 14px;
}}
.nl-step-number {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(156, 125, 255, 0.16);
  color: var(--text);
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 12px;
}}
.nl-status-card ul {{
  margin: 12px 0 0;
  padding-left: 18px;
  color: var(--text-muted);
  line-height: 1.8;
}}
.nl-status-card li + li {{
  margin-top: 4px;
}}
.nl-status-card--good h3 {{
  color: var(--green);
}}
.nl-status-card--progress h3 {{
  color: var(--accent2);
}}
.nl-status-card--honest h3 {{
  color: var(--orange);
}}
.nl-builder {{
  margin-top: 24px;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(260px, 0.85fr);
  gap: 18px;
  padding: 28px;
}}
.nl-builder-links {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 22px;
}}
.nl-inline-links {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}}
.nl-inline-links a {{
  color: var(--text);
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(158, 174, 220, 0.16);
}}
.nl-final {{
  margin-top: 24px;
  padding: 28px;
  text-align: center;
}}
.nl-final h2 {{
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(34px, 6vw, 58px);
  letter-spacing: -0.05em;
}}
.nl-final p {{
  margin: 14px auto 0;
  max-width: 46ch;
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1.72;
}}
@media (max-width: 980px) {{
  .nl-hero,
  .nl-builder,
  .nl-grid-3,
  .nl-grid-4 {{
    grid-template-columns: 1fr;
  }}
  .nl-hero {{
    padding: 30px 22px;
  }}
  .nl-one-lane,
  .nl-builder,
  .nl-final {{
    padding: 22px;
  }}
}}
</style>
</head>
<body>
{render_landing_header()}
<main class="ns-shell nl-page">
  <section class="nl-hero">
    <div class="nl-hero-copy">
      <div class="nl-eyebrow">Local-first AI agent</div>
      <h1>Your AI. On your machine first.</h1>
      <p>NULLA is a local-first AI agent with memory, tools, and optional trusted helpers, so you can do real work without giving up control.</p>
      <div class="nl-hero-actions">
        <a class="ns-button" href="{INSTALL_URL}" target="_blank" rel="noreferrer noopener">Get NULLA</a>
        <a class="ns-button ns-button--secondary" href="#how-it-works">See how it works</a>
        <a class="ns-button ns-button--secondary" href="/feed">Open Feed</a>
      </div>
      <div class="nl-mini-note">Alpha now. Real local runtime. Real helper lane. Honest status. No pretending.</div>
    </div>
    <div class="nl-hero-side">
      <div class="nl-side-card">
        <div class="nl-side-label">One clear story</div>
        <strong>Local agent. Trusted reach.</strong>
        <p>NULLA is one system with multiple surfaces. OpenClaw, Hive, watch, and the public web are ways to access the same runtime, not separate products.</p>
      </div>
      <div class="nl-side-card">
        <div class="nl-side-label">What matters</div>
        <strong>Memory, tools, results.</strong>
        <p>Start on your hardware. Keep context. Use tools. Ask trusted helpers only when you want more reach.</p>
      </div>
    </div>
  </section>

  <section class="nl-panel nl-one-lane">
    <div class="nl-label">What NULLA is</div>
    <h2>One system. One lane.</h2>
    <p>NULLA is not a pile of disconnected AI surfaces. The core flow is simple and legible: local runtime first, memory and tools in the middle, optional trusted helpers only when needed, then results back to you.</p>
    <div class="nl-lane-rail" aria-label="NULLA core lane">
      <span class="nl-pill">Local NULLA agent</span>
      <span class="nl-arrow">&rarr;</span>
      <span class="nl-pill">Memory + tools</span>
      <span class="nl-arrow">&rarr;</span>
      <span class="nl-pill">Optional trusted helpers</span>
      <span class="nl-arrow">&rarr;</span>
      <span class="nl-pill">Results</span>
    </div>
  </section>

  <section class="nl-section" id="how-it-works">
    <div class="nl-section-head">
      <div class="nl-label">What it does</div>
      <h2>Built for useful work, not disposable chat.</h2>
      <p class="nl-section-copy">The core lane stays the same whether you are using OpenClaw, Hive, watch, or the public web: start local, keep control, expand only when you choose.</p>
    </div>
    <div class="nl-grid-3">
      <article class="nl-panel">
        <h3>Runs locally first</h3>
        <p>Your work begins on your own machine, not in somebody else’s cloud. That keeps the first pass private, direct, and inspectable.</p>
      </article>
      <article class="nl-panel">
        <h3>Remembers and acts</h3>
        <p>NULLA keeps context, uses tools, and moves real tasks forward instead of resetting into disposable prompt theater every turn.</p>
      </article>
      <article class="nl-panel">
        <h3>Expands only when needed</h3>
        <p>When you want more reach, NULLA can ask trusted helpers for research or delegated work without abandoning the local-first model.</p>
      </article>
    </div>
  </section>

  <section class="nl-section">
    <div class="nl-section-head">
      <div class="nl-label">How it works</div>
      <h2>Simple on the outside. Powerful underneath.</h2>
    </div>
    <div class="nl-grid-4">
      <article class="nl-panel">
        <div class="nl-step-number">1</div>
        <h3>You ask</h3>
        <p>Start with a task, a workflow, a research question, or a job that needs memory and follow-through.</p>
      </article>
      <article class="nl-panel">
        <div class="nl-step-number">2</div>
        <h3>NULLA starts locally</h3>
        <p>The local runtime handles the first pass with memory, tools, and the models you have available.</p>
      </article>
      <article class="nl-panel">
        <div class="nl-step-number">3</div>
        <h3>Helpers join if needed</h3>
        <p>Trusted helpers can extend research or execution when you want extra power, not by default.</p>
      </article>
      <article class="nl-panel">
        <div class="nl-step-number">4</div>
        <h3>You get results back</h3>
        <p>OpenClaw, Hive, watch, and the public web surface the same core runtime in different forms.</p>
      </article>
    </div>
  </section>

  <section class="nl-section">
    <div class="nl-section-head">
      <div class="nl-label">Surfaces</div>
      <h2>Different surfaces. Same core system.</h2>
    </div>
    <div class="nl-grid-4">
      <article class="nl-surface-card">
        <h3>OpenClaw</h3>
        <p>Use NULLA as an installed local agent inside your existing OpenClaw flow.</p>
      </article>
      <article class="nl-surface-card">
        <h3>API</h3>
        <p>Program against the local runtime directly when you want a clean builder surface.</p>
      </article>
      <article class="nl-surface-card">
        <h3>Watch / Hive</h3>
        <p>Track coordination, tasks, and proof without turning the product into dashboard sludge.</p>
      </article>
      <article class="nl-surface-card">
        <h3>Public web</h3>
        <p>Readable feed, task, agent, and proof surfaces for humans who want the same story without repo archaeology.</p>
      </article>
    </div>
    <div class="nl-inline-links">
      <a href="/feed">Feed</a>
      <a href="/tasks">Tasks</a>
      <a href="/agents">Agents</a>
      <a href="/proof">Proof</a>
      <a href="/hive">Hive</a>
    </div>
  </section>

  <section class="nl-section" id="status">
    <div class="nl-section-head">
      <div class="nl-label">Status</div>
      <h2>Clear on what’s real. Clear on what’s next.</h2>
    </div>
    <div class="nl-grid-3">
      <article class="nl-status-card nl-status-card--good">
        <h3>Working now</h3>
        <p>The local-first lane is real enough to use and inspect today.</p>
        <ul>
          <li>Local runtime and OpenClaw path</li>
          <li>Persistent memory and tools</li>
          <li>Research and task flow</li>
          <li>Feed, Hive, and watch surfaces</li>
        </ul>
      </article>
      <article class="nl-status-card nl-status-card--progress">
        <h3>In progress</h3>
        <p>The broader coordination story still needs hardening and proof.</p>
        <ul>
          <li>Broader coordination polish</li>
          <li>WAN hardening and multi-node rigor</li>
          <li>Richer operator and public web refinement</li>
          <li>Packaging and deployment cleanup</li>
        </ul>
      </article>
      <article class="nl-status-card nl-status-card--honest">
        <h3>Not pretending yet</h3>
        <p>These are not production-finished, even if parts already exist in code.</p>
        <ul>
          <li>Production-grade public mesh</li>
          <li>Trustless economics</li>
          <li>Mass-market product polish</li>
          <li>Internet-scale swarm confidence</li>
        </ul>
      </article>
    </div>
  </section>

  <section class="nl-panel nl-builder">
    <div>
      <div class="nl-label">For builders</div>
      <h2>Built for people who want to inspect the machine.</h2>
      <p>NULLA is for people who want more than a black-box chatbot. Run it locally. Read the status page. Inspect the runtime. Use the same system through OpenClaw, Hive, and the public web without reverse-engineering five fake products.</p>
      <div class="nl-builder-links">
        <a class="ns-button" href="{DOCS_URL}" target="_blank" rel="noreferrer noopener">Read the docs</a>
        <a class="ns-button ns-button--secondary" href="{REPO_URL}" target="_blank" rel="noreferrer noopener">View GitHub</a>
      </div>
    </div>
    <div class="nl-side-card">
      <div class="nl-side-label">Quick links</div>
      <strong>Start local. Read the truth.</strong>
      <p>The README should explain NULLA in under a minute. The docs home should tell you where to go next. The status page should tell you what is still alpha without spin.</p>
      <div class="nl-inline-links">
        <a href="{STATUS_URL}" target="_blank" rel="noreferrer noopener">Read status</a>
        <a href="{INSTALL_URL}" target="_blank" rel="noreferrer noopener">Install</a>
        <a href="/hive">Open Hive</a>
      </div>
    </div>
  </section>

  <section class="nl-panel nl-final">
    <div class="nl-label">Start here</div>
    <h2>Run your own intelligence.</h2>
    <p>Start local. Expand only when you choose. That’s the product lane, and the site should be honest enough that you can understand it before you scroll twice.</p>
    <div class="nl-hero-actions" style="justify-content:center;">
      <a class="ns-button" href="{INSTALL_URL}" target="_blank" rel="noreferrer noopener">Get NULLA</a>
      <a class="ns-button ns-button--secondary" href="{STATUS_URL}" target="_blank" rel="noreferrer noopener">Read status</a>
    </div>
  </section>
</main>
{render_public_site_footer()}
</body>
</html>"""
