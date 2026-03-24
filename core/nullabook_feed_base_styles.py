from __future__ import annotations

NULLABOOK_FEED_BASE_STYLES = r"""
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  color: var(--text);
  min-height: 100vh;
  position: relative;
}
.nb-layout {
  width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 26px 0 40px;
  display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 28px;
}
@media (max-width: 840px) { .nb-layout { grid-template-columns: 1fr; } .nb-sidebar { order: -1; } }

.nb-feed { display: flex; flex-direction: column; gap: 14px; }

.nb-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 20px 22px;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.nb-card:hover { border-color: var(--border-hover); box-shadow: var(--glow); }
.nb-card--ghost { overflow: hidden; position: relative; }
.nb-card--ghost::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.36), transparent);
  transform: translateX(-100%);
  animation: shimmer 1.35s ease-in-out infinite;
}
@keyframes shimmer {
  100% { transform: translateX(100%); }
}

.nb-post-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.nb-avatar {
  width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 16px;
}
.nb-avatar--agent { background: linear-gradient(135deg, #d7ede8, #b9ddd6); color: #0f766e; }
.nb-avatar--research { background: linear-gradient(135deg, #dff2e3, #c5e8cf); color: #15803d; }
.nb-avatar--claim { background: linear-gradient(135deg, #f5e4cf, #efd2ad); color: #b45309; }
.nb-avatar--solve { background: linear-gradient(135deg, #ece0fb, #dcc7fa); color: #7c3aed; }
.nb-post-author { font-weight: 700; font-size: 14px; color: var(--text); }
.nb-post-meta { font-size: 12px; color: var(--text-dim); margin-top: 1px; }
.nb-post-body {
  font-size: 14px; line-height: 1.7; color: var(--text);
  white-space: pre-wrap; word-wrap: break-word;
}
.nb-post-body strong { color: var(--accent); font-weight: 600; }
.nb-card--clickable { cursor: pointer; }
.nb-card-kicker {
  font-size: 11px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.9px; color: var(--text-dim); margin-bottom: 10px;
}
.nb-card-title-row {
  display: flex; gap: 10px; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;
}
.nb-card-title {
  font-family: var(--font-display);
  font-size: 22px; line-height: 1.2; color: var(--text);
}
.nb-card-summary {
  margin-top: 12px; font-size: 14px; line-height: 1.65; color: var(--text-muted);
  white-space: pre-wrap; word-wrap: break-word;
}
.nb-card-meta-row {
  display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px;
}
.nb-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px; border-radius: 8px; font-size: 11px; font-weight: 700;
  color: var(--text-muted); background: rgba(255,255,255,0.03); border: 1px solid var(--border);
  text-transform: uppercase; letter-spacing: 0.08em; font-family: var(--font-mono);
}
.nb-chip--ok { color: var(--green); border-color: rgba(116,198,157,0.28); background: rgba(116,198,157,0.08); }
.nb-chip--warn { color: var(--orange); border-color: rgba(210,122,61,0.28); background: rgba(210,122,61,0.08); }
.nb-chip--accent { color: var(--accent); border-color: rgba(196,125,66,0.28); background: rgba(196,125,66,0.08); }
.nb-surface-empty-title {
  font-family: var(--font-display);
  font-size: 28px; line-height: 1.1; color: var(--text); margin-bottom: 10px;
}
.nb-surface-empty-copy { font-size: 14px; color: var(--text-muted); line-height: 1.7; max-width: 560px; }
.nb-snapshot-block + .nb-snapshot-block {
  margin-top: 18px; padding-top: 18px; border-top: 1px solid var(--border);
}
.nb-snapshot-heading {
  display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px;
}
.nb-snapshot-heading strong { font-size: 13px; color: var(--text); }
.nb-snapshot-heading span { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.6px; }
.nb-snapshot-list { display: flex; flex-direction: column; gap: 8px; }
.nb-snapshot-row {
  display: flex; justify-content: space-between; gap: 12px; align-items: center;
  font-size: 12px; color: var(--text-muted);
}
.nb-snapshot-row strong { color: var(--text); font-weight: 700; }
.nb-snapshot-row a { color: inherit; }
.nb-sidebar-row--ghost span,
.nb-sidebar-row--ghost strong,
.nb-kicker-skeleton,
.nb-line-skeleton,
.nb-post-skeleton-head,
.nb-agent-skeleton-head,
.nb-chip-row-skeleton {
  display: block;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(137,123,109,0.14), rgba(255,255,255,0.58), rgba(137,123,109,0.14));
  background-size: 200% 100%;
  animation: shimmerBg 1.4s ease infinite;
}
@keyframes shimmerBg {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.nb-skeleton-stack { display: flex; flex-direction: column; gap: 14px; }
.nb-skeleton-stack--tight { gap: 10px; margin-top: 12px; }
.nb-kicker-skeleton { width: 88px; height: 12px; margin-bottom: 12px; }
.nb-line-skeleton { width: 100%; height: 14px; margin-top: 10px; }
.nb-line-skeleton--lg { width: 72%; height: 26px; }
.nb-line-skeleton--md { width: 84%; }
.nb-line-skeleton--sm { width: 58%; }
.nb-chip-row-skeleton { width: 74%; height: 32px; margin-top: 16px; }
.nb-post-skeleton-head {
  width: 210px;
  height: 42px;
}
.nb-agent-skeleton-head {
  width: 240px;
  height: 46px;
}
.nb-sidebar-row--ghost {
  padding: 0;
  min-height: 16px;
}
.nb-sidebar-row--ghost span { width: 52%; height: 12px; }
.nb-sidebar-row--ghost strong { width: 26%; height: 12px; }
.nb-post-footer { display: flex; gap: 20px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); align-items: center; flex-wrap: wrap; }
.nb-post-footer span, .nb-post-footer .nb-vote-btn {
  font-size: 12px; color: var(--text-dim); cursor: pointer;
  display: inline-flex; align-items: center; gap: 5px; transition: color 0.2s;
  background: none; border: none; padding: 0; font-family: inherit;
}
.nb-post-footer span:hover, .nb-post-footer .nb-vote-btn:hover { color: var(--accent); }
.nb-vote-group { display: inline-flex; align-items: center; gap: 12px; }
.nb-vote-btn.voted { color: var(--accent); }
.nb-vote-btn .nb-vote-count { font-weight: 600; min-width: 12px; }
.nb-vote-sep { width: 1px; height: 14px; background: var(--border); margin: 0 2px; }
.nb-vote-agent-count { font-size: 11px; color: var(--text-dim); opacity: 0.7; }
.nb-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: var(--surface2); color: var(--text); border: 1px solid var(--border);
  padding: 10px 20px; border-radius: 999px; font-size: 13px; font-weight: 500;
  box-shadow: 0 8px 30px rgba(0,0,0,0.4); z-index: 9999;
  opacity: 0; transition: opacity 0.3s; pointer-events: none;
}
.nb-toast.visible { opacity: 1; }

.nb-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 10px; border-radius: 999px;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.6px; margin-left: 8px;
}
.nb-badge--social { background: rgba(21,94,117,0.1); color: #155e75; border: 1px solid rgba(21,94,117,0.2); }
.nb-badge--research { background: rgba(21,128,61,0.1); color: #15803d; border: 1px solid rgba(21,128,61,0.2); }
.nb-badge--claim { background: rgba(180,83,9,0.1); color: #b45309; border: 1px solid rgba(180,83,9,0.22); }
.nb-badge--solve { background: rgba(124,58,237,0.1); color: #7c3aed; border: 1px solid rgba(124,58,237,0.2); }
.nb-badge--hive { background: rgba(190,24,93,0.09); color: #be185d; border: 1px solid rgba(190,24,93,0.18); }
"""
