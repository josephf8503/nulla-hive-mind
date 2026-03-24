from __future__ import annotations

"""NullaBook fabric timeline styles for workstation dashboard."""

WORKSTATION_RENDER_NULLABOOK_FABRIC_TIMELINE_STYLES = """
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
"""
