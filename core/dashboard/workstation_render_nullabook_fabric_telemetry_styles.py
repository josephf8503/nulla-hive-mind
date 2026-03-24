from __future__ import annotations

"""NullaBook fabric telemetry styles for workstation dashboard."""

WORKSTATION_RENDER_NULLABOOK_FABRIC_TELEMETRY_STYLES = """
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
"""
