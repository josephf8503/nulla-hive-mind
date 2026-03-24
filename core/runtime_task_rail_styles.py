RUNTIME_TASK_RAIL_STYLE_BLOCK = """
    :root {
      --bg: var(--wk-bg);
      --bg-2: var(--wk-bg-alt);
      --panel: var(--wk-panel);
      --panel-2: var(--wk-panel-strong);
      --line: var(--wk-line);
      --line-strong: var(--wk-line-strong);
      --text: var(--wk-text);
      --muted: var(--wk-muted);
      --accent: var(--wk-accent);
      --accent-2: var(--wk-warn);
      --good: var(--wk-good);
      --warn: var(--wk-warn);
      --bad: var(--wk-bad);
      --shadow: var(--wk-shadow);
      --radius: var(--wk-radius);
      --font-ui: var(--wk-font-ui);
      --font-mono: var(--wk-font-mono);
    }
    * { box-sizing: border-box; }
    body {
      font-family: var(--font-ui);
      color: var(--text);
    }
    .panel {
      background: linear-gradient(180deg, rgba(18, 29, 54, 0.96), rgba(9, 14, 27, 0.98));
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .panel-header {
      padding: 18px 20px 14px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255,255,255,0.03), transparent);
    }
    .eyebrow {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: var(--accent);
      margin-bottom: 8px;
    }
    .title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .title {
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.04em;
    }
    .status-pill {
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 12px;
      background: rgba(110, 231, 255, 0.12);
      color: var(--accent);
      border: 1px solid rgba(110, 231, 255, 0.2);
    }
    .subtitle {
      color: var(--muted);
      margin-top: 10px;
      line-height: 1.5;
    }
    .session-list {
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: calc(100vh - 180px);
      overflow: auto;
    }
    .session-card {
      border: 1px solid rgba(154, 171, 212, 0.12);
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.025);
      cursor: pointer;
      transition: transform 0.14s ease, border-color 0.14s ease, background 0.14s ease;
    }
    .session-card:hover,
    .session-card.active {
      transform: translateY(-1px);
      border-color: rgba(110, 231, 255, 0.42);
      background: rgba(110, 231, 255, 0.08);
    }
    .session-top {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
    }
    .session-id {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--muted);
      word-break: break-all;
    }
    .badge {
      padding: 5px 9px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      border: 1px solid transparent;
      white-space: nowrap;
    }
    .badge.running { color: var(--accent); background: rgba(110,231,255,0.12); border-color: rgba(110,231,255,0.2); }
    .badge.completed { color: var(--good); background: rgba(94,240,168,0.12); border-color: rgba(94,240,168,0.2); }
    .badge.request_done { color: var(--warn); background: rgba(255,209,102,0.12); border-color: rgba(255,209,102,0.2); }
    .badge.researching { color: var(--accent-2); background: rgba(255,148,102,0.12); border-color: rgba(255,148,102,0.22); }
    .badge.solved { color: var(--good); background: rgba(94,240,168,0.12); border-color: rgba(94,240,168,0.2); }
    .badge.failed { color: var(--bad); background: rgba(255,107,122,0.12); border-color: rgba(255,107,122,0.2); }
    .badge.pending_approval { color: var(--warn); background: rgba(255,209,102,0.12); border-color: rgba(255,209,102,0.2); }
    .badge.interrupted { color: #ffb15c; background: rgba(255,177,92,0.12); border-color: rgba(255,177,92,0.22); }
    .session-preview {
      font-size: 15px;
      line-height: 1.45;
      margin-bottom: 10px;
    }
    .session-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: var(--muted);
      font-size: 12px;
    }
    .trace-stage-head {
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      background: linear-gradient(180deg, rgba(255,255,255,0.03), transparent);
    }
    .trace-stage-head h2 {
      margin: 0;
      font-size: 28px;
      letter-spacing: -0.04em;
      line-height: 1.05;
    }
    .trace-stage-copy {
      margin: 8px 0 0;
      color: var(--muted);
      line-height: 1.55;
      max-width: 72ch;
      font-size: 14px;
    }
    .trace-stage-proof {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }
    .trace-stage-proof .wk-proof-chip {
      white-space: nowrap;
    }
    .rail-body {
      min-height: calc(100vh - 56px);
      display: grid;
      grid-template-rows: auto auto auto 1fr;
    }
    .detail-block {
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
    }
    .detail-main h2 {
      margin: 0 0 8px;
      font-size: 24px;
      letter-spacing: -0.03em;
    }
    .detail-main p {
      margin: 0;
      color: var(--muted);
      max-width: 900px;
      line-height: 1.55;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }
    .stat-card {
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.035);
      border: 1px solid var(--line);
    }
    .stat-card strong {
      display: block;
      font-size: 18px;
      line-height: 1.2;
      margin-bottom: 6px;
      overflow-wrap: anywhere;
    }
    .stat-card span {
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .stat-card code {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text);
    }
    .trace-strip {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .ops-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .ops-card {
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.035);
      border: 1px solid var(--line);
      min-height: 142px;
    }
    .ops-card.good {
      border-color: rgba(94, 240, 168, 0.26);
      background: rgba(94, 240, 168, 0.08);
    }
    .ops-card.warn {
      border-color: rgba(255, 209, 102, 0.28);
      background: rgba(255, 209, 102, 0.09);
    }
    .ops-card.bad {
      border-color: rgba(255, 107, 122, 0.3);
      background: rgba(255, 107, 122, 0.09);
    }
    .ops-card span {
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .ops-card strong {
      display: block;
      font-size: 20px;
      line-height: 1.2;
      margin-bottom: 8px;
      overflow-wrap: anywhere;
    }
    .ops-card p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .trace-stage {
      border-radius: 16px;
      border: 1px solid var(--line);
      padding: 14px;
      background: rgba(255,255,255,0.02);
      min-height: 112px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .trace-stage.active {
      border-color: rgba(110, 231, 255, 0.36);
      background: rgba(110, 231, 255, 0.08);
    }
    .trace-stage.done {
      border-color: rgba(94, 240, 168, 0.26);
      background: rgba(94, 240, 168, 0.08);
    }
    .trace-stage.failed {
      border-color: rgba(255, 107, 122, 0.3);
      background: rgba(255, 107, 122, 0.08);
    }
    .trace-stage .stage-label {
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .trace-stage .stage-value {
      font-size: 18px;
      font-weight: 700;
      line-height: 1.25;
    }
    .trace-stage .stage-detail {
      font-size: 13px;
      line-height: 1.45;
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    .meta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }
    .meta-chip {
      font-size: 12px;
      color: var(--muted);
      font-family: var(--font-mono);
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(154, 171, 212, 0.12);
    }
    .feed-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      min-height: 0;
    }
    .event-feed,
    .inspector {
      min-height: 0;
      overflow: auto;
    }
    .event-feed {
      padding: 18px 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .event-card {
      border: 1px solid rgba(154, 171, 212, 0.14);
      border-radius: 16px;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.03), transparent 55%),
        rgba(255,255,255,0.02);
      padding: 16px 18px;
      position: relative;
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.14s ease, border-color 0.14s ease, background 0.14s ease;
    }
    .event-card::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: var(--accent);
      opacity: 0.9;
    }
    .event-card.tool_failed::before,
    .event-card.task_failed::before { background: var(--bad); }
    .event-card.tool_preview::before,
    .event-card.task_pending_approval::before { background: var(--warn); }
    .event-card.task_interrupted::before { background: #ffb15c; }
    .event-card.task_completed::before,
    .event-card.tool_loop_completed::before { background: var(--good); }
    .event-card.tool_started::before { background: var(--accent-2); }
    .event-card:hover,
    .event-card.is-active {
      transform: translateY(-1px);
      border-color: rgba(110, 231, 255, 0.34);
      background:
        linear-gradient(135deg, rgba(97, 218, 251, 0.06), transparent 55%),
        rgba(255,255,255,0.03);
    }
    .event-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }
    .event-type {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--accent);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .event-time {
      font-size: 12px;
      color: var(--muted);
      font-family: var(--font-mono);
    }
    .event-message {
      font-size: 15px;
      line-height: 1.55;
      margin-bottom: 12px;
      white-space: pre-wrap;
    }
    .event-meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .inspector {
      border-left: 1px solid var(--line);
      padding: 18px 20px 24px;
      background: rgba(255,255,255,0.02);
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .inspector-card {
      border-radius: 16px;
      border: 1px solid var(--line-strong);
      background: rgba(255,255,255,0.03);
      padding: 14px;
    }
    .inspector-card h3 {
      margin: 0 0 10px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--accent);
    }
    .inspector-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .inspector-item {
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(154, 171, 212, 0.12);
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .inspector-item code {
      font-family: var(--font-mono);
      color: var(--text);
      font-size: 12px;
    }
    .empty-state {
      padding: 40px 24px;
      color: var(--muted);
      text-align: center;
      line-height: 1.6;
    }
    .link-line {
      margin-top: 12px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--muted);
    }
    .trace-workbench {
      display: grid;
      grid-template-columns: minmax(280px, 320px) minmax(0, 1.45fr) minmax(300px, 360px);
      gap: 16px;
      align-items: start;
    }
    .trace-rail-shell,
    .trace-summary-shell {
      position: sticky;
      top: 18px;
      align-self: start;
      min-height: calc(100vh - 36px);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.01)),
        var(--panel-2);
    }
    .trace-center-shell {
      background:
        linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.01)),
        rgba(9, 15, 28, 0.96);
    }
    .trace-rail-shell,
    .trace-summary-shell {
      padding: 16px;
    }
    .trace-rail-stack,
    .trace-summary-stack {
      display: grid;
      gap: 14px;
    }
    .trace-rail-section,
    .trace-summary-section {
      display: grid;
      gap: 10px;
    }
    .trace-selected-step {
      display: grid;
      gap: 10px;
    }
    .trace-selected-step h3 {
      margin: 0;
      font-size: 18px;
      letter-spacing: -0.02em;
    }
    .trace-selected-step p {
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
    }
    .trace-selected-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .trace-feed-grid {
      display: block;
      min-height: 0;
    }
    .trace-feed-grid .event-feed {
      min-height: 0;
    }
    .trace-raw-panel {
      display: none;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(0, 0, 0, 0.24);
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow: auto;
      max-height: 42vh;
    }
    body[data-view-mode="raw"] .trace-raw-panel {
      display: block;
    }
    body[data-view-mode="raw"] .trace-human,
    body[data-view-mode="raw"] .trace-agent {
      display: none;
    }
    body[data-view-mode="agent"] .trace-human[data-human-optional="1"] {
      display: none;
    }
    body[data-view-mode="human"] .trace-agent[data-agent-optional="1"] {
      display: none;
    }
    @media (max-width: 1200px) {
      .trace-workbench {
        grid-template-columns: 1fr;
      }
    }
    @media (max-width: 980px) {
      .session-list {
        max-height: 320px;
      }
      .rail-body {
        min-height: unset;
      }
    }
    @media (max-width: 640px) {
      .summary-grid,
      .trace-strip,
      .ops-grid {
        grid-template-columns: 1fr;
      }
    }
"""
