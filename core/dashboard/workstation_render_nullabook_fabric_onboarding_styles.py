from __future__ import annotations

"""NullaBook fabric onboarding and community styles for workstation dashboard."""

WORKSTATION_RENDER_NULLABOOK_FABRIC_ONBOARDING_STYLES = """
    .nb-onboard {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;
      margin-bottom: 48px;
    }
    .nb-onboard-step {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 20px;
      position: relative;
    }
    .nb-onboard-num {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: linear-gradient(135deg, #61dafb, #a78bfa);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 13px;
      color: #0a0f1a;
      margin-bottom: 10px;
    }
    .nb-onboard-title {
      font-weight: 700;
      font-size: 15px;
      color: var(--ink);
      margin-bottom: 6px;
    }
    .nb-onboard-desc {
      font-size: 13px;
      color: var(--muted);
      line-height: 1.5;
    }
    .nb-onboard-link {
      display: inline-block;
      margin-top: 10px;
      font-size: 12px;
      color: var(--accent);
      text-decoration: none;
    }
    .nb-onboard-link:hover { text-decoration: underline; }
    .nb-community-badge {
      display: inline-block;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 2px 7px;
      border-radius: 999px;
      margin-right: 6px;
    }
    .nb-community-badge--solved { background: rgba(52, 211, 153, 0.15); color: #34d399; }
    .nb-community-badge--open { background: rgba(97, 218, 251, 0.15); color: #61dafb; }
    .nb-community-badge--researching { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
    .nb-community-meta-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 6px;
      font-size: 11px;
      color: var(--muted);
    }
    @media (max-width: 640px) {
      .nb-hero-title { font-size: 28px; }
      .nb-communities { grid-template-columns: 1fr; }
      .nb-agent-grid { grid-template-columns: 1fr; }
      .nb-vitals { grid-template-columns: repeat(2, 1fr); }
      .nb-fabric-cards { grid-template-columns: 1fr; }
      .nb-onboard { grid-template-columns: 1fr; }
    }
"""
