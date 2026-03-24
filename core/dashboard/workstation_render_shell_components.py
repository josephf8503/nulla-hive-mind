from __future__ import annotations

"""Shared workstation dashboard component styles."""

WORKSTATION_RENDER_SHELL_COMPONENTS = """
    .stats {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .stat {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      display: grid;
      gap: 8px;
      box-shadow: var(--shadow);
    }
    .stat[data-inspect-type],
    .dashboard-home-card[data-inspect-type],
    .mini-stat[data-inspect-type] {
      cursor: pointer;
      transition: border-color 0.14s ease, transform 0.14s ease, box-shadow 0.14s ease;
    }
    .stat[data-inspect-type]:hover,
    .stat[data-inspect-type]:focus-visible,
    .dashboard-home-card[data-inspect-type]:hover,
    .dashboard-home-card[data-inspect-type]:focus-visible,
    .mini-stat[data-inspect-type]:hover,
    .mini-stat[data-inspect-type]:focus-visible {
      border-color: rgba(97, 218, 251, 0.34);
      transform: translateY(-1px);
      outline: none;
    }
    .stat-label {
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .stat-value {
      font-size: 30px;
      font-weight: 700;
      line-height: 1;
    }
    .stat-detail {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }
    .tab-button {
      border: 1px solid var(--line);
      background: var(--panel-alt);
      color: var(--ink);
      border-radius: 999px;
      padding: 9px 14px;
      font-size: 13px;
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .tab-button.active {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    .copy-button {
      border: 1px solid var(--line);
      background: var(--panel-alt);
      color: var(--ink);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 11px;
      cursor: pointer;
    }
    .copy-button:hover,
    .copy-button:focus-visible {
      border-color: var(--accent);
      color: var(--accent-strong);
      outline: none;
    }
    .tab-panel {
      display: none;
      gap: 16px;
    }
    .tab-panel.active {
      display: grid;
    }
    .cols-2 {
      grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
    }
    .subgrid {
      display: grid;
      gap: 14px;
    }
    .section-title {
      margin: 0 0 10px;
      font-size: 20px;
    }
    .list {
      display: grid;
      gap: 10px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--panel);
      padding: 14px;
    }
    .card-link {
      display: block;
      color: inherit;
      text-decoration: none;
    }
    .card-link:hover h3,
    .card-link:focus-visible h3 {
      color: var(--accent-strong);
    }
    .card h3 {
      margin: 0 0 6px;
      font-size: 17px;
    }
    .card p {
      margin: 0;
      line-height: 1.45;
      color: var(--muted);
      font-size: 14px;
    }
    .row-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted);
    }
    .chip {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 8px;
      background: var(--chip);
      border: 1px solid var(--line);
      font-size: 11px;
    }
    .chip.ok {
      background: rgba(95, 229, 166, 0.12);
      color: var(--ok);
      border-color: rgba(95, 229, 166, 0.24);
    }
    .chip.warn {
      background: rgba(245, 178, 92, 0.12);
      color: var(--warn);
      border-color: rgba(245, 178, 92, 0.26);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    th {
      color: var(--muted);
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.1em;
      font-weight: 600;
    }
    .mini-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .learning-program {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .learning-program summary {
      list-style: none;
      cursor: pointer;
      padding: 18px;
      display: grid;
      gap: 12px;
      background: var(--panel);
    }
    .learning-program summary::-webkit-details-marker {
      display: none;
    }
    .learning-program summary:hover,
    .learning-program[open] summary {
      background: var(--panel-alt);
    }
    .learning-program-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }
    .learning-program-title {
      margin: 0;
      font-size: 19px;
    }
    .learning-program-body {
      border-top: 1px solid var(--line);
      padding: 18px;
      display: grid;
      gap: 16px;
      background: var(--panel);
    }
    .learning-program-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .learning-program-grid.wide {
      grid-template-columns: 1fr;
    }
    .mini-stat {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
      background: var(--panel);
    }
    .mini-stat strong {
      display: block;
      font-size: 24px;
      margin-bottom: 4px;
    }
    .fold-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--panel);
      overflow: hidden;
    }
    .fold-card summary {
      list-style: none;
      cursor: pointer;
      padding: 12px 14px;
      display: grid;
      gap: 8px;
      background: var(--panel);
    }
    .fold-card summary::-webkit-details-marker {
      display: none;
    }
    .fold-card summary:hover,
    .fold-card[open] summary {
      background: var(--panel-alt);
    }
    .fold-title-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }
    .fold-title {
      margin: 0;
      font-size: 14px;
      font-weight: 700;
      line-height: 1.35;
      color: var(--ink);
    }
    .fold-stamp {
      flex: 0 0 auto;
      font-size: 11px;
      color: var(--muted);
      text-align: right;
      white-space: nowrap;
    }
    .fold-preview {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .fold-body {
      border-top: 1px solid var(--line);
      padding: 12px 14px;
      display: grid;
      gap: 10px;
      background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
    }
    .body-pre {
      margin: 0;
      white-space: pre-wrap;
      line-height: 1.55;
      color: var(--muted);
      font-size: 13px;
    }
    .list-note {
      color: var(--muted);
      font-size: 12px;
      margin: 0 0 2px;
    }
    .empty {
      color: var(--muted);
      font-style: italic;
    }
    footer {
      margin-top: 0;
      padding-top: 12px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: space-between;
    }
    .footer-stack {
      display: grid;
      gap: 8px;
      justify-items: end;
      text-align: right;
    }
    .footer-link-row {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .social-link {
      width: 34px;
      height: 34px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--panel-alt);
      color: var(--ink);
      text-decoration: none;
    }
    .social-link:hover,
    .social-link:focus-visible {
      border-color: var(--accent);
      color: var(--accent-strong);
      outline: none;
    }
    .social-link svg {
      width: 16px;
      height: 16px;
      fill: currentColor;
    }
    .hero-follow-link {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line);
      background: var(--panel-alt);
      color: var(--ink);
      border-radius: 999px;
      padding: 8px 12px;
      text-decoration: none;
      line-height: 1;
      font-size: 12px;
      font-weight: 600;
    }
    .hero-follow-link:hover,
    .hero-follow-link:focus-visible {
      border-color: var(--accent);
      color: var(--accent-strong);
      outline: none;
    }
    .hero-action-row {
      margin-top: 16px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .hero-follow-link svg {
      width: 14px;
      height: 14px;
      fill: currentColor;
    }
"""
