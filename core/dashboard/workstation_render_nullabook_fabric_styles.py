from __future__ import annotations

"""NullaBook telemetry, fabric, proof, and onboarding styles for the workstation dashboard."""

WORKSTATION_RENDER_NULLABOOK_FABRIC_STYLES = """
    /* Telemetry, timeline, proof, and onboarding */
    .nb-vitals {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 12px;
      margin-top: 20px;
    }
    .nb-vital {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px 14px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }
    .nb-vital-value {
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -1px;
      color: var(--ink);
    }
    .nb-vital-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--muted);
      margin-top: 4px;
    }
    .nb-vital-fresh {
      font-size: 10px;
      color: var(--accent);
      margin-top: 4px;
    }
    .nb-vital--live .nb-vital-value { color: var(--ok); }
    .nb-vital--live::before {
      content: '';
      position: absolute;
      top: 8px;
      right: 10px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--ok);
      animation: nb-pulse 2s ease-in-out infinite;
    }
    .nb-ticker-wrap {
      margin-top: 16px;
      overflow: hidden;
      border-radius: 8px;
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 10px 0;
    }
    .nb-ticker {
      display: flex;
      gap: 32px;
      animation: nb-scroll 30s linear infinite;
      white-space: nowrap;
      padding: 0 16px;
    }
    @keyframes nb-scroll {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }
    .nb-ticker-item {
      font-size: 13px;
      color: var(--muted);
      flex-shrink: 0;
    }
    .nb-ticker-dot {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      margin-right: 6px;
      vertical-align: middle;
    }
    .nb-ticker-dot--claim { background: #61dafb; }
    .nb-ticker-dot--post { background: #a78bfa; }
    .nb-ticker-dot--solve { background: #34d399; }
    .nb-ticker-dot--default { background: var(--muted); }
    .nb-timeline {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .nb-tl-topic {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px;
    }
    .nb-tl-topic-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    .nb-tl-topic-title {
      font-weight: 700;
      font-size: 15px;
      color: var(--ink);
    }
    .nb-tl-badge {
      display: inline-block;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 3px 8px;
      border-radius: 999px;
    }
    .nb-tl-badge--solved { background: rgba(52, 211, 153, 0.15); color: #34d399; }
    .nb-tl-badge--open { background: rgba(97, 218, 251, 0.15); color: #61dafb; }
    .nb-tl-badge--researching { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
    .nb-tl-badge--disputed { background: rgba(244, 114, 182, 0.15); color: #f472b6; }
    .nb-tl-events {
      display: flex;
      flex-direction: column;
      gap: 0;
      padding-left: 16px;
      border-left: 2px solid var(--line);
    }
    .nb-tl-ev {
      position: relative;
      padding: 6px 0 6px 16px;
      font-size: 13px;
      color: var(--muted);
    }
    .nb-tl-ev::before {
      content: '';
      position: absolute;
      left: -7px;
      top: 12px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 2px solid var(--line);
      background: var(--bg);
    }
    .nb-tl-ev--claim::before { border-color: #61dafb; background: rgba(97,218,251,0.2); }
    .nb-tl-ev--post::before { border-color: #a78bfa; background: rgba(167,139,250,0.2); }
    .nb-tl-ev--solve::before { border-color: #34d399; background: rgba(52,211,153,0.2); }
    .nb-tl-ev-agent { color: var(--accent); font-weight: 600; }
    .nb-tl-ev-time { color: var(--muted); font-size: 11px; margin-left: 8px; }
    .nb-fabric-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .nb-fabric-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px;
    }
    .nb-fabric-card-title {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .nb-fabric-card-value {
      font-size: 24px;
      font-weight: 800;
      color: var(--ink);
      letter-spacing: -0.5px;
    }
    .nb-fabric-card-detail {
      font-size: 12px;
      color: var(--muted);
      margin-top: 6px;
      line-height: 1.5;
    }
    .nb-proof-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 20px;
    }
    .nb-proof-card p {
      margin: 0 0 12px;
      font-size: 14px;
      line-height: 1.6;
      color: var(--muted);
    }
    .nb-proof-card p:last-child { margin-bottom: 0; }
    .nb-proof-factors {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .nb-proof-factor {
      background: rgba(97, 218, 251, 0.05);
      border: 1px solid rgba(97, 218, 251, 0.12);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 12px;
      color: var(--ink);
    }
    .nb-proof-factor-label { font-weight: 700; display: block; margin-bottom: 2px; }
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
