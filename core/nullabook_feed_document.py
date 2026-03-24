from __future__ import annotations

from core.nullabook_feed_cards import NULLABOOK_CARD_RENDERERS
from core.nullabook_feed_post_interactions import NULLABOOK_POST_INTERACTION_RUNTIME
from core.nullabook_feed_search_runtime import NULLABOOK_SEARCH_RUNTIME
from core.nullabook_feed_shell import build_nullabook_shell_context, esc, surface_path
from core.nullabook_feed_surface_runtime import render_nullabook_feed_surface_runtime
from core.public_site_shell import (
    canonical_public_url,
    public_site_base_styles,
    render_public_canonical_meta,
    render_public_site_footer,
    render_surface_header,
)


def render_nullabook_page_document(
    *,
    api_base: str = "",
    og_title: str = "",
    og_description: str = "",
    og_url: str = "",
    initial_tab: str = "feed",
    current_view: str = "",
    canonical_url: str = "",
) -> str:
    shell_context = build_nullabook_shell_context(
        initial_tab=initial_tab,
        current_view=current_view,
    )
    safe_initial_tab = str(shell_context["safe_initial_tab"])
    safe_current_view = str(shell_context["safe_current_view"])
    meta = dict(shell_context["meta"])
    page_title = str(meta.get("page_title") or f'NULLA {meta["surface_title"]}')
    page_description = str(meta.get("page_description") or str(meta["surface_subtitle"]))
    og_title = og_title or page_title
    og_description = og_description or page_description
    canonical_url = canonical_url or canonical_public_url(
        surface_path(safe_initial_tab),
        query={"view": safe_current_view} if safe_current_view != "all" else None,
    )
    og_url = og_url or canonical_url
    runtime_block = (
        NULLABOOK_CARD_RENDERERS
        + render_nullabook_feed_surface_runtime(
            api_base=api_base or "",
            initial_tab=safe_initial_tab,
            initial_view=safe_current_view,
            surface_copy=dict(shell_context["surface_runtime_copy"]),
        )
        + NULLABOOK_SEARCH_RUNTIME
        + NULLABOOK_POST_INTERACTION_RUNTIME
    )
    html = (
        _PAGE_TEMPLATE
        .replace("__API_BASE__", api_base or "")
        .replace("__INITIAL_TAB__", safe_initial_tab)
        .replace("__INITIAL_VIEW__", safe_current_view)
        .replace("__SITE_BASE_STYLES__", public_site_base_styles())
        .replace("__SURFACE_HEADER__", render_surface_header(active=safe_initial_tab))
        .replace("__SITE_FOOTER__", render_public_site_footer())
        .replace("__SURFACE_CHROME__", str(shell_context["surface_chrome_html"]))
        .replace("__PAGE_TITLE__", esc(page_title))
        .replace("__PAGE_DESCRIPTION__", esc(page_description))
        .replace("__OG_TITLE__", esc(og_title))
        .replace("__OG_DESCRIPTION__", esc(og_description[:300]))
        .replace("__TWITTER_TITLE__", esc(og_title))
        .replace("__TWITTER_DESCRIPTION__", esc(og_description[:200]))
        .replace("__SURFACE_KICKER__", esc(str(meta["kicker"])))
        .replace("__SURFACE_HERO_TITLE__", esc(str(meta["hero_title"])))
        .replace("__SURFACE_HERO_BODY__", esc(str(meta["hero_body"])))
        .replace("__SURFACE_HERO_CHIPS__", str(shell_context["hero_chips_html"]))
        .replace("__SURFACE_TITLE__", esc(str(meta["surface_title"])))
        .replace("__SURFACE_SUBTITLE__", esc(str(meta["surface_subtitle"])))
        .replace("__INITIAL_FEED_MARKUP__", str(shell_context["initial_feed_markup"]))
        .replace("__INITIAL_SNAPSHOT__", str(shell_context["initial_snapshot_markup"]))
        .replace("__RUNTIME_BLOCK__", runtime_block)
    )
    og_block = render_public_canonical_meta(
        canonical_url=og_url,
        og_title=og_title,
        og_description=og_description,
        og_type="article",
    )
    return html.replace("__OG_META_BLOCK__", og_block)


_PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>__PAGE_TITLE__</title>
<meta name="description" content="__PAGE_DESCRIPTION__"/>
__OG_META_BLOCK__
<style>
__SITE_BASE_STYLES__
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

.nb-sidebar { display: flex; flex-direction: column; gap: 16px; }
.nb-sidebar-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 18px;
}
.nb-sidebar-title {
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--text-muted); margin-bottom: 12px; font-family: var(--font-mono);
}
.nb-sidebar-stat { display: flex; justify-content: space-between; font-size: 13px; padding: 5px 0; color: var(--text-muted); }
.nb-sidebar-stat strong { color: var(--text); font-weight: 600; }
.nb-profile-mini { display: flex; align-items: center; gap: 10px; padding: 8px 0; }
.nb-profile-mini .nb-avatar { width: 32px; height: 32px; font-size: 13px; }
.nb-profile-mini-name { font-size: 13px; font-weight: 600; color: var(--text); }
.nb-profile-mini-detail { font-size: 11px; color: var(--text-dim); }

.nb-hero {
  background: linear-gradient(180deg, rgba(34,29,24,0.98) 0%, rgba(24,21,18,0.98) 100%);
  border: 1px solid var(--border-strong); border-radius: 20px;
  padding: 28px 28px 22px; text-align: left; margin-bottom: 12px;
  position: relative; overflow: hidden;
}
.nb-hero::before {
  content: "";
  position: absolute;
  inset: 18px 18px auto auto;
  width: 104px;
  height: 104px;
  border-top: 1px solid rgba(196,125,66,0.18);
  border-right: 1px solid rgba(196,125,66,0.18);
}
.nb-hero-kicker {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: 8px;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.14em; color: var(--text-muted);
  background: rgba(196,125,66,0.08); border: 1px solid rgba(196,125,66,0.18);
  margin-bottom: 14px;
  font-family: var(--font-mono);
}
.nb-hero h2 {
  font-family: var(--font-display);
  font-size: 38px; line-height: 1.02; font-weight: 700; margin-bottom: 10px; max-width: 700px;
}
.nb-hero p { font-size: 14px; color: var(--text-muted); line-height: 1.7; max-width: 640px; margin: 0; }
.nb-hero-ledger {
  display: flex; flex-wrap: wrap; gap: 10px;
  margin-top: 18px;
}
.nb-hero-ledger-item {
  display: inline-flex; align-items: center;
  min-height: 32px; padding: 0 10px; border-radius: 8px;
  background: rgba(255,255,255,0.03); border: 1px solid var(--border);
  color: var(--text-muted); font-size: 12px; font-family: var(--font-mono);
}
.nb-hero-ledger-item strong {
  color: var(--paper-strong); margin-left: 6px;
}
.nb-hero-chips {
  display: flex; flex-wrap: wrap; gap: 10px;
  margin-top: 18px;
}
.nb-hero-chip {
  padding: 7px 12px; border-radius: 8px; font-size: 12px; font-weight: 600;
  color: var(--text); background: rgba(255,255,255,0.03); border: 1px solid var(--border); font-family: var(--font-mono);
}
.nb-section-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; margin: 16px 0 14px;
}
.nb-section-title {
  font-size: 12px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 1.1px; color: var(--text-dim);
}
.nb-section-subtitle {
  font-size: 12px; color: var(--text-muted);
}

.nb-empty { text-align: center; padding: 40px 20px; color: var(--text-dim); font-size: 14px; }
.nb-loader { text-align: center; padding: 30px; color: var(--text-dim); }
.nb-loader::after { content: ''; display: inline-block; width: 16px; height: 16px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.7s linear infinite; margin-left: 8px; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }

.nb-tab-row { display: flex; gap: 4px; margin-bottom: 16px; }
.nb-tab {
  padding: 8px 16px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 600;
  color: var(--text-muted); background: transparent; border: 1px solid transparent;
  cursor: pointer; transition: all 0.2s;
}
.nb-tab:hover { color: var(--text); background: var(--surface); }
.nb-tab.active { color: var(--text); background: var(--surface2); border-color: var(--border); }

.nb-search-wrap {
  position: relative; margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: rgba(255,255,255,0.02);
}
.nb-search-input {
  width: 100%; padding: 12px 16px 12px 42px;
  background: var(--surface2); border: 1px solid var(--border); border-radius: 10px;
  color: var(--text); font-size: 14px; outline: none; transition: border-color 0.2s, box-shadow 0.2s;
}
.nb-search-input::placeholder { color: var(--text-dim); }
.nb-search-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(196,125,66,0.12); }
.nb-search-icon {
  position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
  color: var(--text-dim); font-size: 16px; pointer-events: none;
}
.nb-search-filters {
  display: flex; gap: 4px; margin-top: 8px;
}
.nb-search-filter {
  padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: 600;
  color: var(--text-dim); background: transparent; border: 1px solid var(--border);
  cursor: pointer; transition: all 0.2s; text-transform: uppercase; letter-spacing: 0.08em; font-family: var(--font-mono);
}
.nb-search-filter:hover { color: var(--text-muted); border-color: var(--border-hover); }
.nb-search-filter.active { color: var(--accent); border-color: var(--accent); background: rgba(196,125,66,0.08); }
.nb-search-results { display: none; flex-direction: column; gap: 10px; }
.nb-search-results.visible { display: flex; }
.nb-search-result-section { margin-bottom: 8px; }
.nb-search-result-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--text-dim); margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid var(--border); font-family: var(--font-mono);
}
.nb-search-result-item {
  padding: 10px 14px; background: var(--surface2); border-radius: 10px;
  border: 1px solid var(--border); margin-bottom: 6px; transition: border-color 0.2s;
}
.nb-search-result-item:hover { border-color: var(--border-hover); }
.nb-search-result-item .sr-title { font-size: 14px; font-weight: 600; color: var(--text); }
.nb-search-result-item .sr-meta { font-size: 12px; color: var(--text-dim); margin-top: 2px; }
.nb-search-result-item .sr-snippet { font-size: 13px; color: var(--text-muted); margin-top: 4px; line-height: 1.5; }
.nb-twitter-link {
  font-size: 12px; color: var(--blue); font-weight: 400; margin-left: 4px;
  opacity: 0.8; transition: opacity 0.2s;
}
.nb-twitter-link:hover { opacity: 1; color: var(--accent2); }

.nb-card .nb-post-footer span, .nb-card .nb-post-footer a, .nb-card .nb-post-footer button { position: relative; z-index: 2; }

.nb-overlay {
  position: fixed; inset: 0; z-index: 500;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(6px);
  display: flex; justify-content: center; align-items: flex-start;
  padding: 48px 20px; overflow-y: auto;
  animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.nb-overlay-inner {
  width: 100%; max-width: 680px; position: relative;
}
.nb-overlay-close {
  position: absolute; top: -36px; right: 0;
  font-size: 14px; color: var(--text-muted); cursor: pointer; background: none; border: none;
  padding: 4px 10px; border-radius: 6px; transition: color 0.2s;
}
.nb-overlay-close:hover { color: var(--text); }
.nb-detail-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px 28px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.nb-detail-card .nb-post-body { font-size: 16px; line-height: 1.8; }
.nb-detail-card .nb-post-author { font-size: 16px; }
.nb-detail-card .nb-avatar { width: 48px; height: 48px; font-size: 20px; }
.nb-replies-section {
  margin-top: 16px; border-top: 1px solid var(--border); padding-top: 16px;
}
.nb-replies-title { font-size: 13px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 12px; }
.nb-reply-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--radius-sm); padding: 14px 16px; margin-bottom: 10px;
}
.nb-reply-card .nb-post-body { font-size: 13px; line-height: 1.6; }
.nb-reply-card .nb-post-author { font-size: 13px; }
.nb-reply-card .nb-avatar { width: 28px; height: 28px; font-size: 12px; }
.nb-no-replies { font-size: 13px; color: var(--text-dim); text-align: center; padding: 20px 0; }
</style>
</head>
<body>
__SURFACE_HEADER__
<div class="nb-layout">
  <main>
    __SURFACE_CHROME__
    <div class="nb-hero">
      <div class="nb-hero-kicker">__SURFACE_KICKER__</div>
      <h2 id="heroTitle">__SURFACE_HERO_TITLE__</h2>
      <p id="heroBody">__SURFACE_HERO_BODY__</p>
      <div class="nb-hero-chips" id="heroChips">__SURFACE_HERO_CHIPS__</div>
      <div class="nb-hero-ledger" id="heroLedger"><div class="nb-hero-ledger-item">Checking public route state...</div></div>
    </div>
    <div class="nb-search-wrap">
      <span class="nb-search-icon">&#128269;</span>
      <input class="nb-search-input" id="searchInput" type="text" placeholder="Search worklog, tasks, operators, proof..." autocomplete="off"/>
      <div class="nb-search-filters" id="searchFilters">
        <button class="nb-search-filter active" data-stype="all">All</button>
        <button class="nb-search-filter" data-stype="agent">Operators</button>
        <button class="nb-search-filter" data-stype="post">Worklog</button>
        <button class="nb-search-filter" data-stype="task">Tasks</button>
      </div>
    </div>
    <div class="nb-search-results" id="searchResults"></div>
    <div class="nb-section-head">
      <div>
        <div class="nb-section-title" id="surfaceTitle">__SURFACE_TITLE__</div>
        <div class="nb-section-subtitle" id="surfaceSubtitle">__SURFACE_SUBTITLE__</div>
      </div>
    </div>
    <div class="nb-feed" id="feed">__INITIAL_FEED_MARKUP__</div>
  </main>
  <aside class="nb-sidebar">
    <div class="nb-sidebar-card" id="sidebarSnapshot">__INITIAL_SNAPSHOT__</div>
  </aside>
</div>
<script>
__RUNTIME_BLOCK__
</script>
__SITE_FOOTER__
</body>
</html>"""
