from __future__ import annotations

"""Dashboard layout, inspector, and responsive shell styles."""

WORKSTATION_RENDER_SHELL_LAYOUT = """
    .dashboard-frame {
      display: grid;
      gap: 16px;
    }
    .dashboard-workbench {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr) 340px;
      gap: 16px;
      align-items: stretch;
    }
    .dashboard-rail,
    .dashboard-inspector {
      padding: 16px;
      position: sticky;
      top: 18px;
      align-self: start;
      min-height: calc(100vh - 36px);
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.01)),
        var(--wk-panel-strong);
    }
    .dashboard-rail::before,
    .dashboard-inspector::before {
      content: "";
      display: block;
      width: 44px;
      height: 3px;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent), transparent);
      margin-bottom: 14px;
    }
    .dashboard-rail .tab-button,
    .dashboard-rail .copy-button {
      width: 100%;
      justify-content: flex-start;
      text-align: left;
    }
    .dashboard-rail .wk-chip-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }
    .dashboard-rail-group + .dashboard-rail-group,
    .dashboard-inspector-group + .dashboard-inspector-group {
      margin-top: 14px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
    }
    .dashboard-rail-label,
    .dashboard-inspector-label {
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    .dashboard-home-board {
      margin-bottom: 16px;
    }
    .dashboard-home-board .section-title {
      margin-bottom: 12px;
    }
    .dashboard-stage {
      padding: 18px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.01)),
        rgba(9, 15, 28, 0.96);
      display: grid;
      gap: 18px;
    }
    .dashboard-stage-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--line);
    }
    .dashboard-stage-head h2 {
      margin: 0;
      font-size: 30px;
      letter-spacing: -0.04em;
      line-height: 1.05;
    }
    .dashboard-stage-copy {
      margin: 8px 0 0;
      max-width: 72ch;
      color: var(--muted);
      line-height: 1.6;
      font-size: 14px;
    }
    .dashboard-stage-proof {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }
    .dashboard-stage-proof .wk-proof-chip {
      white-space: nowrap;
    }
    .dashboard-overview-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.14fr) minmax(320px, 0.86fr);
      gap: 16px;
      align-items: start;
    }
    .dashboard-overview-primary,
    .dashboard-overview-secondary {
      display: grid;
      gap: 16px;
      align-content: start;
    }
    .dashboard-home-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .dashboard-home-card {
      border: 1px solid var(--line);
      border-radius: 16px;
      background:
        linear-gradient(180deg, rgba(97, 218, 251, 0.08), rgba(255, 255, 255, 0.02)),
        rgba(255, 255, 255, 0.03);
      padding: 16px;
      display: grid;
      gap: 8px;
      min-height: 148px;
    }
    .dashboard-home-card strong {
      display: block;
      font-size: 24px;
      line-height: 1.1;
    }
    .dashboard-home-card span {
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }
    .dashboard-home-card p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .dashboard-tab-row {
      display: flex;
      flex-wrap: nowrap;
      gap: 8px;
      margin: 0;
      padding: 10px 12px;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: thin;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.03);
    }
    .dashboard-inspector-title {
      margin: 0 0 10px;
      font-size: 20px;
      letter-spacing: -0.03em;
    }
    .dashboard-inspector-body {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }
    .dashboard-inspector-meta {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .dashboard-inspector-truth-note {
      margin-top: 12px;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: rgba(97, 218, 251, 0.06);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }
    .dashboard-inspector-row {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.03);
      overflow-wrap: anywhere;
      font-size: 12px;
      line-height: 1.5;
    }
    .inspector-view-toggle {
      display: flex;
      gap: 4px;
      margin: 8px 0 4px;
    }
    .inspector-view-btn {
      border: 1px solid var(--line);
      background: transparent;
      color: var(--muted);
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .inspector-view-btn.active {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    .dashboard-inspector-raw {
      display: none;
      margin-top: 12px;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(0, 0, 0, 0.26);
      font-family: var(--wk-font-mono);
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow: auto;
      max-height: 48vh;
      color: var(--wk-text);
    }
    .dashboard-inspector[data-inspector-mode="raw"] .dashboard-inspector-raw {
      display: block;
    }
    .dashboard-inspector[data-inspector-mode="raw"] .dashboard-inspector-human,
    .dashboard-inspector[data-inspector-mode="raw"] .dashboard-inspector-agent {
      display: none;
    }
    .dashboard-inspector[data-inspector-mode="agent"] .dashboard-inspector-human[data-human-optional="1"] {
      display: none;
    }
    .dashboard-inspector[data-inspector-mode="human"] .dashboard-inspector-agent[data-agent-optional="1"] {
      display: none;
    }
    .dashboard-drawer {
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.03);
      overflow: hidden;
    }
    .dashboard-drawer summary {
      list-style: none;
      cursor: pointer;
      padding: 12px 14px;
      color: var(--ink);
      font-size: 12px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      background: rgba(255, 255, 255, 0.02);
    }
    .dashboard-drawer summary::-webkit-details-marker {
      display: none;
    }
    .dashboard-drawer-body {
      padding: 14px;
      border-top: 1px solid var(--line);
    }
    .inspect-button {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.03);
      color: var(--ink);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 11px;
      cursor: pointer;
    }
    .inspect-button:hover,
    .inspect-button:focus-visible {
      border-color: var(--accent);
      color: var(--accent);
      outline: none;
    }
    @media (max-width: 1120px) {
      .hero, .cols-2, .dashboard-home-grid, .dashboard-overview-grid {
        grid-template-columns: 1fr;
      }
      .stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      .dashboard-workbench {
        grid-template-columns: 1fr;
      }
      .dashboard-rail,
      .dashboard-inspector {
        position: static;
        min-height: auto;
      }
      .dashboard-tab-row {
        position: relative;
      }
      .dashboard-tab-row::after {
        content: "";
        position: absolute;
        right: 0;
        top: 0;
        bottom: 0;
        width: 32px;
        background: linear-gradient(90deg, transparent, var(--bg, #0a0f1a));
        pointer-events: none;
        border-radius: 0 999px 999px 0;
      }
    }
    @media (max-width: 640px) {
      .shell { padding: 16px 12px 28px; }
      .mini-grid { grid-template-columns: 1fr; }
      .learning-program-grid { grid-template-columns: 1fr; }
      .learning-program-head { flex-direction: column; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      h1 { font-size: 34px; }
    }
    #initialLoadingOverlay {
      position: fixed;
      inset: 0;
      z-index: 9999;
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      background: var(--bg, #0a0f1a);
      color: var(--wk-text, #e0e6ed);
      font-family: var(--wk-font-sans, system-ui, sans-serif);
    }
    #initialLoadingOverlay .loading-ring {
      width: 40px;
      height: 40px;
      border: 3px solid rgba(97, 218, 251, 0.2);
      border-top-color: var(--accent, #61dafb);
      border-radius: 50%;
      animation: spin-ring 0.9s linear infinite;
    }
    @keyframes spin-ring {
      to { transform: rotate(360deg); }
    }
    .live-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: var(--muted);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .live-badge::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #4cda80;
      animation: pulse-dot 1.6s ease-in-out infinite;
    }
    summary { list-style: none; }
    summary::-webkit-details-marker { display: none; }
"""
