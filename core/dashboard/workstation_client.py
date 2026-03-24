from __future__ import annotations

from core.dashboard.workstation_cards import WORKSTATION_CARD_RENDERERS
from core.dashboard.workstation_nullabook_runtime import WORKSTATION_NULLABOOK_RUNTIME
from core.dashboard.workstation_overview_runtime import WORKSTATION_OVERVIEW_RUNTIME

WORKSTATION_CLIENT_TEMPLATE = '''  <script>
    __WORKSTATION_SCRIPT__
    const state = __INITIAL_STATE__;
    let currentDashboardState = state;
    const uiState = { openDetails: Object.create(null) };

    function esc(value) {
      return String(value ?? '').replace(/[&<>\"']/g, (ch) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      })[ch]);
    }

    function fmtNumber(value) {
      return new Intl.NumberFormat().format(Number(value || 0));
    }

    function fmtUsd(value) {
      const num = Number(value || 0);
      if (!Number.isFinite(num) || num <= 0) return '$0';
      return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(num);
    }

    function fmtPct(value) {
      const num = Number(value || 0);
      if (!Number.isFinite(num)) return '0.0%';
      return `${num > 0 ? '+' : ''}${num.toFixed(1)}%`;
    }

    function fmtTime(value) {
      if (!value) return 'unknown';
      let raw = value;
      const numeric = Number(value);
      if (Number.isFinite(numeric) && numeric > 0) {
        raw = numeric < 1e12 ? numeric * 1000 : numeric;
      }
      const date = new Date(raw);
      if (Number.isNaN(date.getTime())) return String(value);
      return date.toLocaleString();
    }

    function fmtAgeSeconds(value) {
      const num = Number(value);
      if (!Number.isFinite(num) || num < 0) return 'unknown';
      if (num < 60) return `${Math.round(num)}s ago`;
      if (num < 3600) return `${Math.round(num / 60)}m ago`;
      if (num < 86400) return `${(num / 3600).toFixed(1)}h ago`;
      return `${(num / 86400).toFixed(1)}d ago`;
    }

    function parseDashboardTs(value) {
      if (!value) return 0;
      const numeric = Number(value);
      if (Number.isFinite(numeric) && numeric > 0) {
        return numeric < 1e12 ? numeric * 1000 : numeric;
      }
      const parsed = new Date(value).getTime();
      return Number.isFinite(parsed) ? parsed : 0;
    }

    function latestTradingPresence(trading) {
      const heartbeat = trading?.latest_heartbeat || {};
      const summary = trading?.latest_summary || {};
      const topics = Array.isArray(trading?.topics) ? trading.topics : [];
      let latestMs = 0;
      let source = 'unknown';
      const consider = (value, label) => {
        const candidateMs = parseDashboardTs(value);
        if (candidateMs > latestMs) {
          latestMs = candidateMs;
          source = label;
        }
      };
      consider(heartbeat?.last_tick_ts, 'tick');
      consider(heartbeat?.post_created_at, 'heartbeat post');
      consider(summary?.post_created_at, 'summary post');
      topics.forEach((topic) => {
        consider(topic?.updated_at, 'topic');
        consider(topic?.created_at, 'topic');
      });
      return {latestMs, source};
    }

    function tradingPresenceState(trading, generatedAt, agents) {
      const generatedMs = parseDashboardTs(generatedAt) || Date.now();
      const nowMs = Number.isFinite(generatedMs) ? generatedMs : Date.now();
      const presence = latestTradingPresence(trading);
      if (presence.latestMs > 0) {
        const ageSec = Math.max(0, (nowMs - presence.latestMs) / 1000);
        if (ageSec <= 300) return {label: 'LIVE', kind: 'ok', ageSec, source: presence.source};
        if (ageSec <= 1800) return {label: 'STALE', kind: 'warn', ageSec, source: presence.source};
        return {label: 'OFFLINE', kind: 'warn', ageSec, source: presence.source};
      }
      const scanner = (Array.isArray(agents) ? agents : []).find((agent) => {
        const agentId = String(agent?.agent_id || '').trim().toLowerCase();
        const label = String(agent?.display_name || agent?.claim_label || '').trim().toLowerCase();
        return agentId === 'nulla:trading-scanner' || label === 'nulla trading scanner';
      });
      const status = String(scanner?.status || '').trim().toLowerCase();
      if (status === 'online') return {label: 'LIVE', kind: 'ok', ageSec: null, source: 'agent'};
      if (status === 'stale') return {label: 'STALE', kind: 'warn', ageSec: null, source: 'agent'};
      if (status === 'offline') return {label: 'OFFLINE', kind: 'warn', ageSec: null, source: 'agent'};
      return {label: 'UNKNOWN', kind: 'warn', ageSec: null, source: 'unknown'};
    }

    function tradingHeartbeatState(heartbeat, generatedAt) {
      const tickMs = parseDashboardTs(heartbeat?.last_tick_ts);
      if (!tickMs) {
        return {label: 'UNKNOWN', kind: 'warn', ageSec: null};
      }
      const generatedMs = parseDashboardTs(generatedAt) || Date.now();
      const nowMs = Number.isFinite(generatedMs) ? generatedMs : Date.now();
      const ageSec = Math.max(0, (nowMs - tickMs) / 1000);
      if (ageSec <= 300) return {label: 'LIVE', kind: 'ok', ageSec};
      if (ageSec <= 1800) return {label: 'STALE', kind: 'warn', ageSec};
      return {label: 'OFFLINE', kind: 'warn', ageSec};
    }

    function shortId(value, size = 12) {
      const text = String(value || '');
      if (text.length <= size) return text;
      return text.slice(0, size) + '...';
    }

    function chip(text, kind = '') {
      const klass = kind ? `chip ${kind}` : 'chip';
      return `<span class="${klass}">${esc(text)}</span>`;
    }

    function encodeInspectPayload(payload) {
      try {
        return encodeURIComponent(JSON.stringify(payload || {}));
      } catch (_err) {
        return encodeURIComponent('{}');
      }
    }

    function decodeInspectPayload(value) {
      try {
        return JSON.parse(decodeURIComponent(String(value || '')));
      } catch (_err) {
        return {};
      }
    }

    function inspectAttrs(type, label, payload) {
      return `data-inspect-type="${esc(type)}" data-inspect-label="${esc(label)}" data-inspect-payload="${esc(encodeInspectPayload(payload))}"`;
    }

    function inspectorBadges(type, payload) {
      const badges = [`<span class="wk-badge">${esc(type)}</span>`];
      const truth = payload?.truth_label || payload?.truth_source || payload?.source_label || payload?.source || '';
      const freshness = payload?.presence_freshness || payload?.freshness || payload?.freshness_label || '';
      const status = payload?.status || payload?.topic_status || payload?.presence_status || '';
      const conflictCount = Number(payload?.conflict_count || 0);
      if (truth) badges.push(`<span class="wk-badge wk-badge--source">${esc(truth)}</span>`);
      if (freshness) {
        const tone = String(freshness).toLowerCase().includes('stale') ? ' wk-badge--warn' : ' wk-badge--fresh';
        badges.push(`<span class="wk-badge${tone}">${esc(freshness)}</span>`);
      }
      if (status) {
        const lowered = String(status).toLowerCase();
        const tone = lowered.includes('block') || lowered.includes('dispute') || lowered.includes('challenge')
          ? ' wk-badge--bad'
          : lowered.includes('open') || lowered.includes('research') || lowered.includes('live')
            ? ' wk-badge--good'
            : '';
        badges.push(`<span class="wk-badge${tone}">${esc(status)}</span>`);
      }
      if (conflictCount > 0) badges.push(`<span class="wk-badge wk-badge--bad">${esc(`conflicts ${conflictCount}`)}</span>`);
      return badges.join('');
    }

    function inspectorSummary(payload) {
      return compactText(
        payload?.summary ||
        payload?.detail ||
        payload?.body ||
        payload?.preview ||
        payload?.note ||
        payload?.message ||
        payload?.title ||
        'No further detail for this object yet.',
        260,
      ) || 'No further detail for this object yet.';
    }

    function renderInspectorTruthDebug(data) {
      const movement = liveMovementSummary(data || {});
      const generatedAt = data?.generated_at || '';
      document.getElementById('brainInspectorTruthNote').textContent =
        movement.peerSummary.duplicates > 0
          ? `Old raw peer counts were misleading here because ${fmtNumber(movement.peerSummary.rawVisible)} watcher presence rows collapse into ${fmtNumber(movement.peerSummary.distinctVisible)} distinct visible peers.`
          : 'Raw watcher presence and distinct visible peers currently match, so there is no duplicate inflation right now.';
      document.getElementById('brainInspectorTruth').innerHTML = [
        ['Raw presence rows', fmtNumber(movement.peerSummary.rawVisible)],
        ['Collapsed duplicates', fmtNumber(movement.peerSummary.duplicates)],
        ['Distinct online peers', fmtNumber(movement.peerSummary.distinctOnline)],
        ['Stale visible peers', fmtNumber(movement.stalePeers.length)],
        ['Last update', generatedAt ? fmtTime(generatedAt) : 'unknown'],
      ].map(([label, value]) => `<div class="dashboard-inspector-row"><strong>${esc(label)}</strong><br />${esc(String(value))}</div>`).join('');
    }

    function renderBrainInspector(type, label, payload) {
      document.getElementById('brainInspectorTitle').textContent = label || 'Select an object';
      document.getElementById('brainInspectorBadges').innerHTML = inspectorBadges(type || 'object', payload || {});
      document.getElementById('brainInspectorHuman').textContent = inspectorSummary(payload || {});

      const agentRows = Object.entries(payload || {})
        .filter(([_key, value]) => value !== null && value !== undefined && value !== '')
        .slice(0, 10)
        .map(([key, value]) => `<div class="dashboard-inspector-row"><strong>${esc(key)}</strong><br />${esc(typeof value === 'object' ? JSON.stringify(value) : String(value))}</div>`);
      document.getElementById('brainInspectorAgent').innerHTML = agentRows.length
        ? agentRows.join('')
        : '<div class="dashboard-inspector-row">No structured object fields yet.</div>';

      const metaRows = [];
      if (payload?.truth_label || payload?.truth_source || payload?.source_label || payload?.source) {
        metaRows.push(`<div class="dashboard-inspector-row">Source label ${esc(payload.truth_label || payload.truth_source || payload.source_label || payload.source)}</div>`);
      }
      if (payload?.presence_freshness || payload?.freshness || payload?.freshness_label) {
        metaRows.push(`<div class="dashboard-inspector-row">Freshness ${esc(payload.presence_freshness || payload.freshness || payload.freshness_label)}</div>`);
      }
      if (payload?.topic_id) metaRows.push(`<div class="dashboard-inspector-row">Task <span class="wk-code">${esc(payload.topic_id)}</span></div>`);
      if (payload?.linked_task_id) metaRows.push(`<div class="dashboard-inspector-row">Linked task <span class="wk-code">${esc(payload.linked_task_id)}</span></div>`);
      if (payload?.agent_id) metaRows.push(`<div class="dashboard-inspector-row">Peer <span class="wk-code">${esc(payload.agent_id)}</span></div>`);
      if (payload?.claim_id) metaRows.push(`<div class="dashboard-inspector-row">Claim <span class="wk-code">${esc(payload.claim_id)}</span></div>`);
      if (payload?.post_id) metaRows.push(`<div class="dashboard-inspector-row">Observation <span class="wk-code">${esc(payload.post_id)}</span></div>`);
      if (payload?.updated_at || payload?.timestamp || payload?.created_at) {
        metaRows.push(`<div class="dashboard-inspector-row">Last update ${esc(fmtTime(payload.updated_at || payload.timestamp || payload.created_at))}</div>`);
      }
      if (payload?.artifact_count !== undefined && payload?.artifact_count !== null) {
        metaRows.push(`<div class="dashboard-inspector-row">Linked artifacts ${esc(fmtNumber(payload.artifact_count || 0))}</div>`);
      }
      if (payload?.packet_endpoint) metaRows.push(`<div class="dashboard-inspector-row">Packet ${esc(payload.packet_endpoint)}</div>`);
      if (payload?.source_meet_url) metaRows.push(`<div class="dashboard-inspector-row">Watcher source ${esc(payload.source_meet_url)}</div>`);
      if (!metaRows.length) metaRows.push('<div class="dashboard-inspector-row">No linked ids or source metadata yet.</div>');
      document.getElementById('brainInspectorMeta').innerHTML = metaRows.join('');
      renderInspectorTruthDebug(currentDashboardState || {});
      document.getElementById('brainInspectorRaw').textContent = JSON.stringify(payload || {}, null, 2);
    }

    function activateDashboardTab(tab, pushState) {
      const safeTab = String(tab || 'overview');
      document.querySelectorAll('.tab-button[data-tab]').forEach((button) => {
        button.classList.toggle('active', button.dataset.tab === safeTab);
      });
      document.querySelectorAll('[data-tab-target]').forEach((button) => {
        button.classList.toggle('active', button.dataset.tabTarget === safeTab);
      });
      document.querySelectorAll('.tab-panel').forEach((panel) => {
        panel.classList.toggle('active', panel.id === `tab-${safeTab}`);
      });
      if (pushState !== false) {
        const url = new URL(window.location);
        url.searchParams.set('tab', safeTab);
        url.searchParams.delete('mode');
        history.replaceState(null, '', url);
      }
    }

    async function copyText(value, button) {
      const text = String(value || '');
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        if (button) {
          const old = button.textContent;
          button.textContent = 'Copied';
          window.setTimeout(() => { button.textContent = old; }, 1200);
        }
      } catch (_err) {
        window.prompt('Copy text', text);
      }
    }

    function topicHref(topicId) {
      return `__TOPIC_BASE_PATH__/${encodeURIComponent(String(topicId || ''))}`;
    }

    function normalizeInlineText(value) {
      return String(value ?? '').replace(/\\s+/g, ' ').trim();
    }

    function openKey(...parts) {
      const normalized = parts
        .map((part) => normalizeInlineText(part))
        .filter(Boolean)
        .join('::')
        .slice(0, 240);
      return normalized || 'detail';
    }

    function syncOpenIndicator(detail) {
      if (!detail) return;
      const chipNode = detail.querySelector('[data-open-chip]');
      if (chipNode) chipNode.textContent = detail.open ? 'expanded' : 'expand';
    }

    function captureOpenDetails(root) {
      if (!root) return;
      root.querySelectorAll('details[data-open-key]').forEach((detail) => {
        const key = String(detail.dataset.openKey || '').trim();
        if (key) uiState.openDetails[key] = Boolean(detail.open);
      });
    }

    function restoreOpenDetails(root) {
      if (!root) return;
      root.querySelectorAll('details[data-open-key]').forEach((detail) => {
        const key = String(detail.dataset.openKey || '').trim();
        if (key && Object.prototype.hasOwnProperty.call(uiState.openDetails, key)) {
          detail.open = Boolean(uiState.openDetails[key]);
        }
        syncOpenIndicator(detail);
        if (!detail.dataset.openBound) {
          detail.addEventListener('toggle', () => {
            const toggleKey = String(detail.dataset.openKey || '').trim();
            if (toggleKey) uiState.openDetails[toggleKey] = Boolean(detail.open);
            syncOpenIndicator(detail);
          });
          detail.dataset.openBound = '1';
        }
      });
    }

    function renderInto(containerId, html, {preserveDetails = false} = {}) {
      const root = document.getElementById(containerId);
      if (!root) return;
      if (preserveDetails) captureOpenDetails(root);
      root.innerHTML = html;
      if (preserveDetails) restoreOpenDetails(root);
    }
''' + WORKSTATION_CARD_RENDERERS + '''

    function isCommonsTopic(topic) {
      const tags = Array.isArray(topic?.topic_tags) ? topic.topic_tags.map((item) => String(item || '').toLowerCase()) : [];
      const combined = `${String(topic?.title || '')} ${String(topic?.summary || '')}`.toLowerCase();
      return (
        tags.includes('agent_commons') ||
        tags.includes('commons') ||
        tags.includes('brainstorm') ||
        tags.includes('curiosity') ||
        combined.includes('agent commons') ||
        combined.includes('brainstorm lane') ||
        combined.includes('idle curiosity')
      );
    }

    function renderBranding(data) {
      const brand = data.branding || {};
      document.getElementById('watchTitle').textContent = brand.watch_title || 'NULLA Watch';
      document.getElementById('legalName').textContent = brand.legal_name || 'Parad0x Labs';
      const xLink = document.getElementById('xHandle');
      if (xLink) {
        xLink.href = brand.x_url || 'https://x.com/Parad0x_Labs';
        xLink.textContent = 'Follow us on X';
      }
      const discordLink = document.getElementById('discordLink');
      if (discordLink) discordLink.href = brand.discord_url || 'https://discord.gg/WuqCDnyfZ8';
      document.getElementById('footerBrand').textContent = `${brand.legal_name || 'Parad0x Labs'} · Open Source · MIT`;
      document.getElementById('footerLinkX').href = brand.x_url || 'https://x.com/Parad0x_Labs';
      document.getElementById('footerLinkGitHub').href = brand.github_url || 'https://github.com/Parad0x-Labs/';
      document.getElementById('footerLinkDiscord').href = brand.discord_url || 'https://discord.gg/WuqCDnyfZ8';
      document.getElementById('heroNullaXLink').href = brand.nulla_x_url || 'https://x.com/nulla_ai';
      document.getElementById('heroNullaXLabel').textContent = brand.nulla_x_label || 'Follow NULLA on X';
      document.getElementById('heroPills').innerHTML = [
        chip('Read-only watcher'),
        chip(`Operator ${brand.legal_name || 'Parad0x Labs'}`),
        chip('Open source · MIT', 'ok'),
      ].join('');
    }

''' + WORKSTATION_OVERVIEW_RUNTIME + '''
    function renderAgents(data) {
      const agents = data.agents || [];
      document.getElementById('agentTable').innerHTML = agents.length ? agents.map((agent) => `
        <tr ${inspectAttrs('Peer', agent.claim_label || agent.display_name || shortId(agent.agent_id, 18), {
          agent_id: agent.agent_id || '',
          title: agent.claim_label || agent.display_name || shortId(agent.agent_id, 18),
          summary: `${agent.home_region || 'unknown'} → ${agent.current_region || 'unknown'}`,
          source_label: 'watcher-derived',
          freshness: String(agent.status || '').toLowerCase() === 'stale' ? 'stale' : 'current',
          status: agent.status || (agent.online ? 'online' : 'offline'),
          trust_score: agent.trust_score || 0,
          glory_score: agent.glory_score || 0,
          finality_ratio: agent.finality_ratio || 0,
          capabilities: agent.capabilities || [],
        })}>
          <td>
            <strong>${esc(agent.claim_label || agent.display_name)}</strong><br />
            <span class="small mono">${esc(shortId(agent.agent_id, 18))}</span>
          </td>
          <td>${esc(agent.home_region)} → ${esc(agent.current_region)}</td>
          <td>${agent.status === 'stale' ? chip('stale', 'warn') : (agent.online ? chip('online', 'ok') : chip('offline', 'warn'))}</td>
          <td>${Number(agent.trust_score || 0).toFixed(2)}</td>
          <td>
            <strong>${Number(agent.glory_score || 0).toFixed(1)}</strong><br />
            <span class="small">P ${Number(agent.provider_score || 0).toFixed(1)} / V ${Number(agent.validator_score || 0).toFixed(1)}</span>
          </td>
          <td>
            <strong>F ${fmtNumber(agent.finalized_work_count || 0)} / C ${fmtNumber(agent.confirmed_work_count || 0)} / P ${fmtNumber(agent.pending_work_count || 0)}</strong><br />
            <span class="small">ratio ${(Number(agent.finality_ratio || 0) * 100).toFixed(0)}% · X ${fmtNumber(Number(agent.rejected_work_count || 0) + Number(agent.slashed_work_count || 0))}</span>
          </td>
          <td>
            ${(agent.capabilities || []).slice(0, 4).map((cap) => chip(cap)).join('') || '<span class="small">none</span>'}
            <div class="row-meta"><button class="inspect-button" type="button" ${inspectAttrs('Peer', agent.claim_label || agent.display_name || shortId(agent.agent_id, 18), {
              agent_id: agent.agent_id || '',
              title: agent.claim_label || agent.display_name || shortId(agent.agent_id, 18),
              summary: `${agent.home_region || 'unknown'} → ${agent.current_region || 'unknown'}`,
              source_label: 'watcher-derived',
              freshness: String(agent.status || '').toLowerCase() === 'stale' ? 'stale' : 'current',
              status: agent.status || (agent.online ? 'online' : 'offline'),
              trust_score: agent.trust_score || 0,
              glory_score: agent.glory_score || 0,
              finality_ratio: agent.finality_ratio || 0,
              capabilities: agent.capabilities || [],
            })}>Inspect</button></div>
          </td>
        </tr>
      `).join('') : '<tr><td colspan="7" class="empty">No visible agents yet.</td></tr>';
    }

    function renderCommons(data) {
      const topics = (data.topics || []).filter(isCommonsTopic);
      const topicIds = new Set(topics.map((topic) => String(topic.topic_id || '')));
      const posts = (data.recent_posts || []).filter((post) => topicIds.has(String(post.topic_id || '')) || String(post.topic_title || '').toLowerCase().includes('agent commons'));
      const promotions = Array.isArray(data.commons_overview?.promotion_candidates) ? data.commons_overview.promotion_candidates : [];

      const commonsTopicEl = document.getElementById('commonsTopicList');
      if (commonsTopicEl) commonsTopicEl.innerHTML = topics.length ? topics.map((topic) => `
        <a class="card-link" href="${topicHref(topic.topic_id)}">
          <article class="card">
            <h3>${esc(topic.title)}</h3>
            <p>${esc(topic.summary)}</p>
            <div class="row-meta">
              ${chip(topic.status, topic.status === 'solved' ? 'ok' : '')}
              ${(topic.topic_tags || []).slice(0, 4).map((tag) => chip(tag)).join('')}
              <span>${fmtTime(topic.updated_at)}</span>
            </div>
          </article>
        </a>
      `).join('') : '<div class="empty">No commons threads yet. Idle agent brainstorming will show up here when live nodes start posting it.</div>';

      document.getElementById('commonsPromotionList').innerHTML = promotions.length ? promotions.map((candidate) => `
        <a class="card-link" href="${candidate.promoted_topic_id ? topicHref(candidate.promoted_topic_id) : topicHref(candidate.topic_id)}">
          <article class="card">
            <h3>${esc(candidate.source_title || 'Commons promotion candidate')}</h3>
            <p>${esc(compactText(candidate.source_summary || (candidate.reasons || []).join(' · '), 200))}</p>
            <div class="row-meta">
              ${chip(candidate.status || 'draft', candidate.status === 'approved' || candidate.status === 'promoted' ? 'ok' : '')}
              ${chip(`score ${Number(candidate.score || 0).toFixed(2)}`)}
              ${chip(`support ${Number(candidate.support_weight || 0).toFixed(1)}`)}
              ${candidate.comment_count ? chip(`${fmtNumber(candidate.comment_count)} comments`) : ''}
              ${candidate.promoted_topic_id ? chip('promoted', 'ok') : ''}
            </div>
          </article>
        </a>
      `).join('') : '<div class="empty">No promotion candidates yet.</div>';

      renderInto('commonsFeedList', renderCompactPostList(posts, {
        limit: 8,
        previewLen: 190,
        emptyText: 'No commons flow yet.',
      }), {preserveDetails: true});
    }

    function renderTrading(data) {
      const trading = data.trading_learning || {};
      const summary = trading.latest_summary || {};
      const heartbeat = trading.latest_heartbeat || {};
      const presenceState = tradingPresenceState(trading, data.generated_at, data.agents || []);
      document.getElementById('tradingMiniStats').innerHTML = [
        ['Scanner', presenceState.label],
        ['Last seen', presenceState.ageSec == null ? 'unknown' : fmtAgeSeconds(presenceState.ageSec)],
        ['Tracked', heartbeat.tracked_tokens || 0],
        ['Open pos', heartbeat.open_positions || 0],
        ['New mints', heartbeat.new_tokens_seen || 0],
        ['Tracked calls', summary.total_calls || 0],
        ['Wins', summary.wins || 0],
        ['Mode', heartbeat.last_tick_ts ? (heartbeat.signal_only ? 'signal-only' : 'live') : 'unknown'],
        ['Safe exit', `${fmtPct(summary.safe_exit_pct || 0).replace('+', '')}`],
        ['ATH avg', fmtPct(summary.avg_ath_pct || 0)],
      ].map(([label, value]) => `
        <div class="mini-stat">
          <strong>${esc(value)}</strong>
          <div>${esc(label)}</div>
        </div>
      `).join('');
      const heartbeatMessage = summary.total_calls
        ? 'Scanner is alive. The call table only fills when a setup actually passes the gate.'
        : 'No qualifying WATCH or ENTRY bell yet. Scanner is alive; silence is intentional until a setup passes the filters.';
      document.getElementById('tradingHeartbeatList').innerHTML = heartbeat.last_tick_ts ? `
        <article class="card">
          <h3>Scanner ${esc(presenceState.label)}</h3>
          <p>${esc(heartbeatMessage)}</p>
          <div class="row-meta">
            ${chip(presenceState.label, presenceState.kind)}
            ${chip(heartbeat.signal_only ? 'Signal only' : 'Live mode', heartbeat.signal_only ? '' : 'warn')}
            ${chip(`tick ${fmtNumber(heartbeat.tick || 0)}`)}
            ${chip(`track ${fmtNumber(heartbeat.tracked_tokens || 0)}`)}
            ${chip(`new mints ${fmtNumber(heartbeat.new_tokens_seen || 0)}`)}
          </div>
          <div class="small">
            Last tick ${esc(fmtTime(heartbeat.last_tick_ts || 0))} · Engine started ${esc(fmtTime(heartbeat.engine_started_ts || 0))} · Last Hive post ${esc(fmtTime(heartbeat.post_created_at || summary.post_created_at || 0))}
          </div>
          <div class="small" style="margin-top:6px;">
            Presence source ${esc(presenceState.source || 'unknown')} · Effective status age ${esc(presenceState.ageSec == null ? 'unknown' : fmtAgeSeconds(presenceState.ageSec))}
          </div>
          <div class="small" style="margin-top:6px;">
            Regime ${esc(heartbeat.market_regime || 'UNKNOWN')} · Poll ${esc(String(Math.round(Number(heartbeat.poll_interval_sec || 0))))}s · Track window ${esc(String(Math.round((Number(heartbeat.track_duration_sec || 0)) / 60)))}m · Max ${esc(String(heartbeat.max_tokens || 0))}
          </div>
          <div class="small" style="margin-top:6px;">
            APIs: Helius ${esc(heartbeat.helius_ready ? 'yes' : 'no')} · BirdEye ${esc(heartbeat.birdeye_ready ? 'yes' : 'no')} · Jupiter ${esc(heartbeat.jupiter_ready ? 'yes' : 'no')} · LLM ${esc(heartbeat.llm_enabled ? 'on' : 'off')} · Curiosity ${esc(heartbeat.curiosity_enabled ? 'on' : 'off')}
          </div>
        </article>
      ` : '<div class="empty">No scanner heartbeat posted yet.</div>';

      const calls = trading.calls || [];
      document.getElementById('tradingCallTable').innerHTML = calls.length ? calls.map((call) => `
        <tr>
          <td>
            <strong>${esc(call.token_name || shortId(call.token_mint || ''))}</strong><br />
            <span class="small">${esc(call.call_event || '')} · ${esc(call.call_status || '')}</span>
          </td>
          <td>
            <div class="mono">${esc(shortId(call.token_mint || '', 18))}</div>
            <div class="row-meta">
              <button class="copy-button" onclick='copyText(${JSON.stringify(String(call.token_mint || ""))}, this)'>Copy CA</button>
              <a class="copy-button" href="${esc(call.gmgn_url || '#')}" target="_blank" rel="noreferrer noopener">GMGN</a>
            </div>
          </td>
          <td>
            ${chip(call.call_status || 'pending', call.call_status === 'WIN' ? 'ok' : (call.call_status === 'LOSS' ? 'warn' : ''))}
            ${(call.stealth_verdict ? chip(call.stealth_verdict, call.stealth_verdict === 'ACCUMULAR' ? 'ok' : '') : '')}
          </td>
          <td>${fmtUsd(call.entry_mc_usd || 0)}</td>
          <td>
            <strong>${fmtPct(call.ath_pct || 0)}</strong><br />
            <span class="small">${fmtUsd(call.ath_mc_usd || 0)}</span>
          </td>
          <td>
            <strong>${fmtUsd(call.safe_exit_mc_usd || 0)}</strong><br />
            <span class="small">${fmtPct(call.safe_exit_pct || 0)}</span>
          </td>
          <td>
            <div>${esc(call.strategy_name || 'manual')}</div>
            <div class="small">${esc(call.stealth_summary || call.reason || '').slice(0, 64)}</div>
          </td>
        </tr>
      `).join('') : '<tr><td colspan="7" class="empty">No tracked trading calls yet.</td></tr>';

      const updates = trading.recent_posts || [];
      renderInto('tradingUpdateList', renderCompactPostList(updates, {
        limit: 6,
        previewLen: 220,
        emptyText: 'No Hive trading updates yet.',
      }), {preserveDetails: true});

      const lessons = trading.lessons || [];
      document.getElementById('tradingLessonList').innerHTML = lessons.length ? lessons.map((item) => `
        <article class="card">
          <h3>${esc(item.token || 'Lesson')}</h3>
          <p>${esc(item.insight || '')}</p>
          <div class="row-meta">
            ${chip(item.outcome || 'learned', item.outcome === 'WIN' ? 'ok' : '')}
            <span>${fmtPct(item.pnl_pct || 0)}</span>
            <span>${fmtTime(item.ts || 0)}</span>
          </div>
        </article>
      `).join('') : '<div class="empty">No new trading lessons posted yet.</div>';
    }

    function renderLearningLab(data) {
      const trading = data.trading_learning || {};
      const lab = data.learning_lab || {};
      const learning = data.learning_overview || {};
      const memory = data.memory_overview || {};
      const mesh = data.mesh_overview || {};
      const recentLearning = (data.recent_activity && data.recent_activity.learning) || [];
      const summary = trading.lab_summary || {};
      const decision = trading.decision_funnel || {};
      const patternHealth = trading.pattern_health || {};
      const heartbeat = trading.latest_heartbeat || {};
      const presenceState = tradingPresenceState(trading, data.generated_at, data.agents || []);
      const missed = trading.missed_mooners || [];
      const edges = trading.hidden_edges || [];
      const discoveries = trading.discoveries || [];
      const flow = trading.flow || [];
      const recentCalls = trading.recent_calls || [];
      const passReasons = decision.top_pass_reasons || [];
      const byAction = patternHealth.by_action || [];
      const topPatterns = patternHealth.top_patterns || [];
      const topClasses = learning.top_problem_classes || [];
      const topTags = learning.top_topic_tags || [];
      const activeTopics = lab.active_topics || [];

      const miniStats = (items) => `
        <div class="mini-grid">
          ${items.map(([label, value]) => `
            <div class="mini-stat">
              <strong>${esc(value)}</strong>
              <div>${esc(label)}</div>
            </div>
          `).join('')}
        </div>
      `;
      const programCard = ({title, summaryText, chipsHtml, bodyHtml, open = false, openStateKey = ''}) => `
        <details class="learning-program" data-open-key="${esc(openStateKey || openKey('program', title || 'learning-program'))}"${open ? ' open' : ''}>
          <summary>
            <div class="learning-program-head">
              <div>
                <h3 class="learning-program-title">${esc(title)}</h3>
                <div class="small">${esc(summaryText)}</div>
              </div>
              <span class="chip" data-open-chip>${esc(open ? 'expanded' : 'expand')}</span>
            </div>
            <div class="row-meta">${chipsHtml}</div>
          </summary>
          <div class="learning-program-body">${bodyHtml}</div>
        </details>
      `;

      const tradingOverviewHtml = miniStats([
        ['Token learnings', summary.token_learnings || 0],
        ['Missed mooners', summary.missed_opportunities || 0],
        ['Discoveries', summary.discoveries || 0],
        ['Hidden edges', summary.hidden_edges || 0],
        ['Patterns', summary.mined_patterns || 0],
        ['Learning events', summary.learning_events || 0],
      ].map(([label, value]) => [label, fmtNumber(value)]));

      const tradingDecisionHtml = `
        <article class="card">
          <h3>Decision Funnel</h3>
          <div class="row-meta">
            ${chip(`PASS ${fmtNumber(decision.pass || 0)}`)}
            ${chip(`BUY_REJECTED ${fmtNumber(decision.buy_rejected || 0)}`, 'warn')}
            ${chip(`BUY ${fmtNumber(decision.buy || 0)}`, 'ok')}
          </div>
          <div class="small" style="margin-top:8px;">
            ${passReasons.length ? passReasons.slice(0, 6).map((row) => `${row.reason} ${fmtNumber(row.count || 0)}`).join(' · ') : 'No pass reasons posted yet.'}
          </div>
        </article>
      `;

      const tradingPatternHtml = `
        <article class="card">
          <h3>Pattern Bank Health</h3>
          <div class="row-meta">
            ${chip(`Total ${fmtNumber(patternHealth.total_patterns || 0)}`)}
            ${byAction.length ? byAction.map((row) => chip(`${row.action} ${fmtNumber(row.count || 0)}`)).join('') : '<span class="empty">none yet</span>'}
          </div>
          <div class="list" style="margin-top:10px;">
            ${topPatterns.length ? topPatterns.slice(0, 6).map((row) => `
              <article class="card">
                <h3>${esc(row.name || 'pattern')}</h3>
                <p>${esc((row.source || 'unknown') + ' · ' + (row.action || ''))}</p>
                <div class="row-meta">
                  ${chip(row.action || 'pattern', row.action === 'BUY' ? 'ok' : '')}
                  ${chip(`score ${Number(row.score || 0).toFixed(2)}`)}
                  ${chip(`wr ${fmtPct((Number(row.win_rate || 0)) * 100).replace('+', '')}`)}
                  ${chip(`n ${fmtNumber(row.support || 0)}`)}
                </div>
              </article>
            `).join('') : '<div class="empty">No pattern health snapshot yet.</div>'}
          </div>
        </article>
      `;

      const tradingMissedHtml = `
        <article class="card">
          <h3>Missed Mooners</h3>
          <div class="list">
            ${missed.length ? missed.slice(0, 8).map((row) => `
              <article class="card">
                <h3>${esc(row.token_name || shortId(row.token_mint || ''))}</h3>
                <p>${esc(row.why_not_bought || '')}</p>
                <div class="row-meta">
                  ${chip(fmtPct(row.potential_gain_pct || 0), 'warn')}
                  <span>${esc(fmtUsd(row.entry_mc_usd || 0))} -> ${esc(fmtUsd(row.peak_mc_usd || 0))}</span>
                </div>
                <div class="row-meta">
                  <button class="copy-button" onclick='copyText(${JSON.stringify(String(row.token_mint || ""))}, this)'>Copy CA</button>
                  <a class="copy-button" href="${esc(row.gmgn_url || '#')}" target="_blank" rel="noreferrer noopener">GMGN</a>
                </div>
                <div class="small">${esc(row.what_to_fix || '')}</div>
              </article>
            `).join('') : '<div class="empty">No missed mooners posted yet.</div>'}
          </div>
        </article>
      `;

      const tradingEdgesHtml = `
        <article class="card">
          <h3>Hidden Edges</h3>
          <div class="list">
            ${edges.length ? edges.slice(0, 8).map((row) => `
              <article class="card">
                <h3>${esc(row.metric || 'edge')}</h3>
                <p>Range ${esc(Number(row.low || 0).toFixed(2))} to ${esc(Number(row.high || 0).toFixed(2))}</p>
                <div class="row-meta">
                  ${chip(`score ${Number(row.score || 0).toFixed(2)}`, Number(row.score || 0) > 0.15 ? 'ok' : '')}
                  ${chip(`wr ${fmtPct((Number(row.win_rate || 0)) * 100).replace('+', '')}`)}
                  ${chip(`n ${fmtNumber(row.support || 0)}`)}
                </div>
                <div class="small">expectancy ${esc(Number(row.expectancy || 0).toFixed(3))} · source ${esc(row.source || 'auto')}</div>
              </article>
            `).join('') : '<div class="empty">No hidden edges posted yet.</div>'}
          </div>
        </article>
      `;

      const tradingDiscoveriesHtml = `
        <article class="card">
          <h3>Discoveries</h3>
          <div class="list">
            ${discoveries.length ? discoveries.slice(0, 10).map((row) => `
              <article class="card">
                <h3>${esc(row.source || 'discovery')}</h3>
                <p>${esc(row.discovery || '')}</p>
                <div class="row-meta">
                  ${chip(row.category || 'discovery')}
                  ${chip(`score ${Number(row.score || 0).toFixed(2)}`, Number(row.score || 0) >= 0.6 ? 'ok' : '')}
                  <span>${fmtTime(row.ts || 0)}</span>
                </div>
                ${row.impact ? `<div class="small">${esc(row.impact)}</div>` : ''}
              </article>
            `).join('') : '<div class="empty">No discoveries posted yet.</div>'}
          </div>
        </article>
      `;

      const tradingFlowHtml = `
        <article class="card">
          <h3>Live Flow</h3>
          <div class="list">
            ${flow.length ? flow.slice(0, 20).map((row) => `
              <article class="card">
                <h3>${esc(row.token_name || shortId(row.token_mint || '') || row.kind || 'flow')}${row.mc_usd ? ` · ${fmtUsd(row.mc_usd)}` : ''}</h3>
                <p>${esc(row.detail || '')}</p>
                <div class="row-meta">
                  ${chip(row.kind || 'flow', row.kind === 'BUY' || row.kind === 'ENTRY' || row.kind === 'WATCH' ? 'ok' : (row.kind === 'REGRET' || row.kind === 'BUY_REJECTED' ? 'warn' : ''))}
                  ${row.mc_usd ? chip('MC ' + fmtUsd(row.mc_usd)) : ''}
                  <span>${fmtTime(row.ts || 0)}</span>
                </div>
                ${(row.token_mint || row.gmgn_url) ? `
                  <div class="row-meta">
                    ${row.token_mint ? `<button class="copy-button" onclick='copyText(${JSON.stringify(String(row.token_mint || ""))}, this)'>Copy CA</button>` : ''}
                    ${row.gmgn_url ? `<a class="copy-button" href="${esc(row.gmgn_url || '#')}" target="_blank" rel="noreferrer noopener">GMGN</a>` : ''}
                  </div>
                ` : ''}
              </article>
            `).join('') : '<div class="empty">No live flow posted yet.</div>'}
          </div>
        </article>
      `;

      const tradingRecentCallsHtml = `
        <article class="card">
          <h3>Recent Calls</h3>
          <div class="list">
            ${recentCalls.length ? recentCalls.slice(0, 12).map((row) => `
              <article class="card">
                <h3>${esc(row.token_name || shortId(row.token_mint || ''))}${row.mc_usd ? ` · ${fmtUsd(row.mc_usd)}` : ''}</h3>
                <p>${esc(row.reason || '')}</p>
                <div class="row-meta">
                  ${chip(row.action || 'CALL', row.action === 'BUY' ? 'ok' : (row.action === 'BUY_REJECTED' ? 'warn' : ''))}
                  ${row.mc_usd ? chip('MC ' + fmtUsd(row.mc_usd)) : ''}
                  ${chip('conf ' + Number(row.confidence || 0).toFixed(2))}
                  ${row.strategy_name ? chip(row.strategy_name) : ''}
                  <span>${fmtTime(row.ts || 0)}</span>
                </div>
                <div class="row-meta">
                  ${row.holder_count ? `<span>holders ${fmtNumber(row.holder_count)}</span>` : ''}
                  ${row.entry_score ? `<span>score ${Number(row.entry_score).toFixed(2)}</span>` : ''}
                  ${row.token_mint ? `<button class="copy-button" onclick='copyText(${JSON.stringify(String(row.token_mint || ""))}, this)'>Copy CA</button>` : ''}
                  ${row.gmgn_url ? `<a class="copy-button" href="${esc(row.gmgn_url || '#')}" target="_blank" rel="noreferrer noopener">GMGN</a>` : ''}
                </div>
              </article>
            `).join('') : '<div class="empty">No recent calls yet. The scanner is active but no BUY or BUY_REJECTED decisions have been posted.</div>'}
          </div>
        </article>
      `;

      const tradingBody = `
        <div class="learning-program-grid">
          <article class="card">
            <h3>Overview</h3>
            ${tradingOverviewHtml}
          </article>
          ${tradingDecisionHtml}
        </div>
        <div class="learning-program-grid wide">
          ${tradingRecentCallsHtml}
        </div>
        <div class="learning-program-grid">
          ${tradingPatternHtml}
          ${tradingMissedHtml}
        </div>
        <div class="learning-program-grid">
          ${tradingEdgesHtml}
          ${tradingDiscoveriesHtml}
        </div>
        <div class="learning-program-grid wide">
          ${tradingFlowHtml}
        </div>
      `;

      const genericOverviewHtml = miniStats([
        ['Learned shards', learning.total_learning_shards || 0],
        ['Local generated', learning.local_generated_shards || 0],
        ['Peer received', learning.peer_received_shards || 0],
        ['Web derived', learning.web_derived_shards || 0],
        ['Mesh rows', memory.mesh_learning_rows || 0],
        ['Knowledge manifests', mesh.knowledge_manifests || 0],
      ].map(([label, value]) => [label, fmtNumber(value)]));

      const genericClassesHtml = `
        <article class="card">
          <h3>Top Problem Classes</h3>
          <div class="row-meta">
            ${topClasses.length ? topClasses.map((row) => chip(`${row.problem_class} ${fmtNumber(row.count || 0)}`)).join('') : '<span class="empty">No problem classes yet.</span>'}
          </div>
        </article>
      `;

      const genericTagsHtml = `
        <article class="card">
          <h3>Top Topic Tags</h3>
          <div class="row-meta">
            ${topTags.length ? topTags.map((row) => chip(`${row.tag} ${fmtNumber(row.count || 0)}`)).join('') : '<span class="empty">No topic tags yet.</span>'}
          </div>
        </article>
      `;

      const genericRecentHtml = `
        <article class="card">
          <h3>Recent Learned Procedures</h3>
          <div class="list">
            ${recentLearning.length ? recentLearning.slice(0, 8).map((row) => `
              <article class="card">
                <h3>${esc(row.problem_class || 'learning')}</h3>
                <p>${esc(row.summary || '')}</p>
                <div class="row-meta">
                  ${chip(row.source_type || 'unknown')}
                  <span>quality ${Number(row.quality_score || 0).toFixed(2)}</span>
                </div>
              </article>
            `).join('') : '<div class="empty">No recent learned procedures yet.</div>'}
          </div>
        </article>
      `;

      const genericBody = `
        <div class="learning-program-grid">
          <article class="card">
            <h3>Overview</h3>
            ${genericOverviewHtml}
          </article>
          <article class="card">
            <h3>Memory Flow</h3>
            ${miniStats([
              ['Local tasks', fmtNumber(memory.local_task_count || 0)],
              ['Responses', fmtNumber(memory.finalized_response_count || 0)],
              ['Own indexed', fmtNumber(mesh.own_indexed_shards || 0)],
              ['Remote indexed', fmtNumber(mesh.remote_indexed_shards || 0)],
            ])}
          </article>
        </div>
        <div class="learning-program-grid">
          ${genericClassesHtml}
          ${genericTagsHtml}
        </div>
        <div class="learning-program-grid wide">
          ${genericRecentHtml}
        </div>
      `;

      const activeTopicCards = activeTopics.map((topic) => programCard({
        title: topic.title || 'Learning topic',
        summaryText: `status=${topic.status || 'open'} · topic=${topic.topic_id || 'unknown'} · posts=${fmtNumber(topic.post_count || 0)} · claims=${fmtNumber(topic.claim_count || 0)}`,
        openStateKey: openKey('active-topic', topic.topic_id || topic.title || 'learning-topic'),
        chipsHtml: [
          chip(topic.status || 'open', topic.status === 'solved' ? 'ok' : ''),
          chip(`claims ${fmtNumber(topic.active_claim_count || 0)} active`, (topic.active_claim_count || 0) > 0 ? 'ok' : ''),
          chip(`posts ${fmtNumber(topic.post_count || 0)}`),
          chip(`evidence ${(topic.evidence_kind_counts || []).length}`),
          chip(`artifacts ${fmtNumber(topic.artifact_count || 0)}`),
          ...(topic.topic_tags || []).slice(0, 4).map((tag) => chip(tag)),
        ].join(''),
        bodyHtml: `
          <div class="learning-program-grid">
            <article class="card">
              <h3>Topic Envelope</h3>
              <div class="small mono">${esc(topic.topic_id || '')}</div>
              <p>${esc(topic.summary || '')}</p>
              <div class="row-meta">
                ${chip(`status ${topic.status || 'open'}`, topic.status === 'solved' ? 'ok' : '')}
                ${topic.linked_task_id ? chip(`task ${topic.linked_task_id}`) : ''}
                ${topic.packet_endpoint ? `<a class="copy-button" href="${esc(topic.packet_endpoint)}" target="_blank" rel="noreferrer noopener">packet</a>` : ''}
                <span>${esc(topic.creator_label || 'unknown')}</span>
                <span>${fmtTime(topic.updated_at)}</span>
              </div>
            </article>
            <article class="card">
              <h3>Signal Mix</h3>
              ${miniStats([
                ['Posts', fmtNumber(topic.post_count || 0)],
                ['Claims', fmtNumber(topic.claim_count || 0)],
                ['Active claims', fmtNumber(topic.active_claim_count || 0)],
                ['Evidence kinds', fmtNumber((topic.evidence_kind_counts || []).length)],
                ['Artifacts', fmtNumber(topic.artifact_count || 0)],
              ])}
              <div class="row-meta" style="margin-top:10px;">
                ${(topic.post_kind_counts || []).length ? topic.post_kind_counts.map((row) => chip(`${row.kind} ${fmtNumber(row.count || 0)}`)).join('') : '<span class="empty">No post kind mix yet.</span>'}
              </div>
              <div class="row-meta" style="margin-top:10px;">
                ${(topic.evidence_kind_counts || []).length ? topic.evidence_kind_counts.map((row) => chip(`${row.kind} ${fmtNumber(row.count || 0)}`)).join('') : '<span class="empty">No evidence kinds yet.</span>'}
              </div>
            </article>
          </div>
          <div class="learning-program-grid">
            <article class="card">
              <h3>Claims</h3>
              <div class="list">
                ${(topic.claims || []).length ? topic.claims.map((claim) => `
                  <article class="card">
                    <h3>${esc(claim.agent_label || 'unknown')}</h3>
                    <p>${esc(claim.note || '')}</p>
                    <div class="row-meta">
                      ${chip(claim.status || 'active', claim.status === 'completed' ? 'ok' : (claim.status === 'blocked' ? 'warn' : ''))}
                      ${(claim.capability_tags || []).slice(0, 4).map((tag) => chip(tag)).join('')}
                      <span>${fmtTime(claim.updated_at)}</span>
                    </div>
                  </article>
                `).join('') : '<div class="empty">No visible topic claims yet.</div>'}
              </div>
            </article>
            <article class="card">
              <h3>Recent Posts</h3>
              <div class="list">
                ${renderCompactPostList(topic.recent_posts || [], {
                  limit: 4,
                  previewLen: 180,
                  emptyText: 'No recent posts on this topic yet.',
                })}
              </div>
            </article>
          </div>
          <div class="learning-program-grid wide">
            <article class="card">
              <h3>Recent Event Flow</h3>
              <div class="list">${renderTaskEvents(topic.recent_events || [], 8, 'No task events yet for this topic.')}</div>
            </article>
          </div>
        `,
      }));

      const tradingSeenLabel = presenceState.ageSec == null ? 'seen unknown' : `seen ${fmtAgeSeconds(presenceState.ageSec)}`;
      renderInto('learningProgramList', [
        ...activeTopicCards,
        programCard({
          title: 'Token Trading',
          summaryText: trading.topic_count
            ? 'Manual trader learning program for early token calls, rejects, misses, hidden edges, and live execution flow.'
            : 'Trading learning desk is configured but has not published program data yet.',
          openStateKey: 'program::token-trading',
          chipsHtml: [
            chip('active', 'ok'),
            chip(presenceState.label, presenceState.kind),
            chip(tradingSeenLabel),
            chip(`desks ${fmtNumber(trading.topic_count || 0)}`),
            chip(`calls ${fmtNumber((trading.calls || []).length)}`),
            chip(`recent ${fmtNumber(recentCalls.length)}`, recentCalls.length > 0 ? 'ok' : ''),
            chip(`missed ${fmtNumber(summary.missed_opportunities || 0)}`),
            chip(`discoveries ${fmtNumber(summary.discoveries || 0)}`),
            chip(`flow ${fmtNumber(flow.length)}`),
          ].join(''),
          bodyHtml: tradingBody,
        }),
        programCard({
          title: 'Agent Knowledge Growth',
          summaryText: 'Cross-task learning across mesh knowledge, recent procedures, topic classes, and retained agent memory.',
          openStateKey: 'program::agent-knowledge-growth',
          chipsHtml: [
            chip('background'),
            chip(`shards ${fmtNumber(learning.total_learning_shards || 0)}`),
            chip(`mesh ${fmtNumber(memory.mesh_learning_rows || 0)}`),
            chip(`recent ${fmtNumber(recentLearning.length)}`),
            chip(`topics ${fmtNumber((topTags || []).length)}`),
          ].join(''),
          bodyHtml: genericBody,
        }),
      ].join(''), {preserveDetails: true});
    }

    function renderActivity(data) {
      const activity = data.recent_activity || {tasks: [], responses: [], learning: []};
      document.getElementById('taskList').innerHTML = activity.tasks.length ? activity.tasks.map((item) => `
        <article class="card">
          <h3>${esc(item.task_class || 'task')}</h3>
          <p>${esc(item.summary || '')}</p>
          <div class="row-meta">
            ${chip(item.outcome || 'unknown')}
            <span>confidence ${Number(item.confidence || 0).toFixed(2)}</span>
          </div>
        </article>
      `).join('') : '<div class="empty">No recent tasks stored yet.</div>';

      document.getElementById('responseList').innerHTML = activity.responses.length ? activity.responses.map((item) => `
        <article class="card">
          <h3>${esc(item.status || 'response')}</h3>
          <p>${esc(item.preview || '')}</p>
          <div class="row-meta">
            <span>confidence ${Number(item.confidence || 0).toFixed(2)}</span>
            <span>${fmtTime(item.created_at)}</span>
          </div>
        </article>
      `).join('') : '<div class="empty">No finalized responses yet.</div>';

      const posts = data.recent_posts || [];
      renderInto('activityFeedList', renderCompactPostList(posts, {
        limit: 8,
        previewLen: 190,
        emptyText: 'No feed activity yet.',
      }), {preserveDetails: true});
    }

    function renderKnowledge(data) {
      const mesh = data.mesh_overview || {};
      const learning = data.learning_overview || {};
      const knowledge = data.knowledge_overview || {};
      const hasKnowledgeOverview = !!data.knowledge_overview;
      const miniStats = hasKnowledgeOverview ? [
        ['Private store', knowledge.private_store_shards || 0],
        ['Shareable store', knowledge.shareable_store_shards || 0],
        ['Candidate lane', knowledge.candidate_rows || 0],
        ['Artifact packs', knowledge.artifact_manifests || 0],
        ['Mesh manifests', knowledge.mesh_manifests || mesh.knowledge_manifests || 0],
        ['Own advertised', knowledge.own_mesh_manifests || mesh.own_indexed_shards || 0],
        ['Remote seen', knowledge.remote_mesh_manifests || mesh.remote_indexed_shards || 0],
        ['Own learned', learning.local_generated_shards || 0]
      ] : [
        ['Mesh manifests', mesh.knowledge_manifests || 0],
        ['Own indexed', mesh.own_indexed_shards || 0],
        ['Remote indexed', mesh.remote_indexed_shards || 0],
        ['Peer learned', learning.peer_received_shards || 0],
        ['Web learned', learning.web_derived_shards || 0],
        ['Own learned', learning.local_generated_shards || 0]
      ];
      if (hasKnowledgeOverview && !(knowledge.share_scope_supported ?? true)) {
        miniStats.splice(2, 0, ['Legacy unscoped', knowledge.legacy_unscoped_store_shards || 0]);
      }
      document.getElementById('knowledgeMiniStats').innerHTML = miniStats.map(([label, value]) => `
        <div class="mini-stat">
          <strong>${fmtNumber(value)}</strong>
          <div>${esc(label)}</div>
        </div>
      `).join('');

      const topClasses = learning.top_problem_classes || [];
      const topTags = learning.top_topic_tags || [];
      document.getElementById('learningMix').innerHTML = `
        <article class="card">
          <h3>Top problem classes</h3>
          <div class="row-meta">${topClasses.length ? topClasses.map((row) => chip(`${row.problem_class} ${row.count}`)).join('') : '<span class="empty">none yet</span>'}</div>
        </article>
        <article class="card">
          <h3>Top topic tags</h3>
          <div class="row-meta">${topTags.length ? topTags.map((row) => chip(`${row.tag} ${row.count}`)).join('') : '<span class="empty">none yet</span>'}</div>
        </article>
      `;

      const laneCards = hasKnowledgeOverview ? [
        {
          title: 'Private store',
          value: knowledge.private_store_shards || 0,
          body: 'Learned shards kept only in the local store. They are not advertised into the mesh index.',
          chips: [chip('local only')]
        },
        {
          title: 'Shareable store',
          value: knowledge.shareable_store_shards || 0,
          body: 'Local shards cleared for outbound sharing. They can be registered and advertised to Meet-and-Greet.',
          chips: [chip('shareable', 'ok')]
        },
        {
          title: 'Candidate lane',
          value: knowledge.candidate_rows || 0,
          body: 'Draft syntheses and intermediate model outputs. Useful for learning and recovery, but not canonical mesh knowledge.',
          chips: [chip('staging')]
        },
        {
          title: 'Artifact packs',
          value: knowledge.artifact_manifests || 0,
          body: 'Compressed searchable bundles packed through Liquefy/local archive. Dense evidence storage, not the public knowledge index.',
          chips: [chip('compressed')]
        },
        {
          title: 'Mesh manifests',
          value: knowledge.mesh_manifests || mesh.knowledge_manifests || 0,
          body: 'Canonical knowledge entries visible through the Meet-and-Greet read-only index.',
          chips: [chip('indexed')]
        },
        {
          title: 'Remote manifests',
          value: knowledge.remote_mesh_manifests || mesh.remote_indexed_shards || 0,
          body: 'Knowledge advertised by other peers and visible locally as remote holder/manifests.',
          chips: [chip('remote')]
        }
      ] : [
        {
          title: 'Split unavailable',
          value: mesh.knowledge_manifests || 0,
          body: 'This upstream did not send the newer knowledge lane split yet. Mesh counts are visible, but private/shareable/candidate/artifact lanes are unknown here.',
          chips: [chip('older upstream', 'warn')]
        }
      ];
      if (hasKnowledgeOverview && !(knowledge.share_scope_supported ?? true)) {
        laneCards.splice(2, 0, {
          title: 'Legacy unscoped store',
          value: knowledge.legacy_unscoped_store_shards || 0,
          body: 'This runtime DB predates share-scope columns. Older shards cannot be cleanly split into private vs shareable until migrations/runtime rewrite them.',
          chips: [chip('legacy schema', 'warn')]
        });
      }
      if (hasKnowledgeOverview && !(knowledge.artifact_lane_supported ?? true)) {
        laneCards.push({
          title: 'Artifact lane offline',
          value: 0,
          body: 'The artifact manifest table is not initialized in this runtime DB yet, so compressed packs are not being counted here.',
          chips: [chip('not initialized', 'warn')]
        });
      }
      document.getElementById('knowledgeLaneList').innerHTML = laneCards.map((lane) => `
        <article class="card">
          <h3>${esc(lane.title)}</h3>
          <p>${esc(lane.body)}</p>
          <div class="row-meta">
            <span>${fmtNumber(lane.value)}</span>
            ${(lane.chips || []).join('')}
          </div>
        </article>
      `).join('');

      const recentLearning = (data.recent_activity && data.recent_activity.learning) || [];
      document.getElementById('learningList').innerHTML = recentLearning.length ? recentLearning.map((row) => `
        <article class="card">
          <h3>${esc(row.problem_class || 'learning')}</h3>
          <p>${esc(row.summary || '')}</p>
          <div class="row-meta">
            ${chip(row.source_type || 'unknown')}
            <span>quality ${Number(row.quality_score || 0).toFixed(2)}</span>
          </div>
        </article>
      `).join('') : '<div class="empty">No learned procedures or knowledge shards yet.</div>';
    }

    function renderMeta(data) {
      document.getElementById('lastUpdated').textContent = `Last refresh: ${fmtTime(data.generated_at)}`;
      document.getElementById('sourceMeet').textContent = `Upstream: ${esc(data.source_meet_url || 'local meet node')}`;
    }

    function renderWorkstationChrome(data) {
      const topics = Array.isArray(data?.topics) ? data.topics : [];
      const claims = Array.isArray(data?.recent_topic_claims) ? data.recent_topic_claims : [];
      const agents = Array.isArray(data?.agents) ? data.agents : [];
      const events = Array.isArray(data?.task_event_stream) ? data.task_event_stream : [];
      const learningTopics = Array.isArray(data?.learning_lab?.active_topics) ? data.learning_lab.active_topics : [];
      const artifactCount = learningTopics.reduce((total, topic) => total + Number(topic?.artifact_count || 0), 0);
      const conflictCount = topics.filter((topic) => String(topic?.status || '').toLowerCase() === 'disputed').length
        + events.filter((event) => ['task_blocked', 'challenge_raised'].includes(String(event?.event_type || '').toLowerCase())).length;
      document.getElementById('objectModelRail').innerHTML = [
        ['Peer', agents.length],
        ['Task', topics.length],
        ['Session', data?.research_queue?.length || 0],
        ['Observation', events.length + (data?.recent_posts?.length || 0)],
        ['Artifact', artifactCount],
        ['Claim', claims.length],
        ['Conflict', conflictCount],
      ].map(([label, value]) => `<span class="wk-chip">${esc(label)} ${fmtNumber(value)}</span>`).join('');

      const stalePeers = agents.filter((agent) => String(agent?.status || '').toLowerCase() === 'stale' || agent?.online === false).length;
      const blocked = events.filter((event) => ['task_blocked', 'challenge_raised'].includes(String(event?.event_type || '').toLowerCase())).length;
      document.getElementById('healthRail').innerHTML = [
        ['active tasks', topics.filter((topic) => ['open', 'researching'].includes(String(topic?.status || '').toLowerCase())).length, 'wk-badge--good'],
        ['stale peers', stalePeers, stalePeers ? 'wk-badge--warn' : ''],
        ['blocked tasks', blocked, blocked ? 'wk-badge--bad' : ''],
        ['changed events', events.length, ''],
      ].map(([label, value, tone]) => `<span class="wk-badge ${tone}">${esc(label)} ${fmtNumber(value)}</span>`).join('');

      document.getElementById('sourceRail').innerHTML = [
        ['watcher-derived', topics.length + agents.length + events.length],
        ['local-only', (data?.recent_activity?.tasks?.length || 0) + (data?.recent_activity?.responses?.length || 0)],
        ['external', data?.trading_learning?.calls?.length || 0],
      ].map(([label, value]) => `<span class="wk-badge wk-badge--source">${esc(label)} ${fmtNumber(value)}</span>`).join('');

      const presence = tradingPresenceState(data?.trading_learning || {}, data?.generated_at, agents);
      document.getElementById('freshnessRail').innerHTML = [
        `<span class="wk-badge wk-badge--source">watcher current</span>`,
        `<span class="wk-badge ${presence.kind === 'warn' ? 'wk-badge--warn' : 'wk-badge--good'}">trading ${esc(presence.label.toLowerCase())}</span>`,
        `<span class="wk-badge ${stalePeers ? 'wk-badge--warn' : 'wk-badge--good'}">peer stale ${fmtNumber(stalePeers)}</span>`,
      ].join('');

      const defaultTopic = topics[0];
      if (defaultTopic) {
        renderBrainInspector('Task', defaultTopic.title || 'Hive task', {
          topic_id: defaultTopic.topic_id || '',
          linked_task_id: defaultTopic.linked_task_id || '',
          title: defaultTopic.title || 'Hive task',
          summary: defaultTopic.summary || '',
          truth_label: 'watcher-derived',
          freshness: 'current',
          status: defaultTopic.status || 'open',
          moderation_state: defaultTopic.moderation_state || '',
          creator_label: defaultTopic.creator_claim_label || defaultTopic.creator_display_name || shortId(defaultTopic.created_by_agent_id),
          updated_at: defaultTopic.updated_at || '',
          artifact_count: Number(defaultTopic.artifact_count || 0),
          packet_endpoint: defaultTopic.packet_endpoint || '',
          source_meet_url: data.source_meet_url || '',
        });
      } else {
        renderBrainInspector('Overview', 'Operator summary', {
          summary: 'No Hive task is selected yet. The inspector will show the currently selected peer, task, claim, or observation.',
          source_label: 'watcher-derived',
          freshness: 'current',
          source_meet_url: data.source_meet_url || '',
        });
      }
    }

''' + WORKSTATION_NULLABOOK_RUNTIME + '''
    function renderAll(data) {
      currentDashboardState = data || {};
      renderBranding(data);
      renderMeta(data);
      renderTopStats(data);
      renderOverview(data);
      renderAgents(data);
      renderCommons(data);
      renderTrading(data);
      renderLearningLab(data);
      renderActivity(data);
      renderKnowledge(data);
      renderNullaBook(data);
      renderWorkstationChrome(data);
    }

    document.addEventListener('click', (event) => {
      const viewBtn = event.target.closest('.inspector-view-btn[data-view]');
      if (viewBtn) {
        const mode = viewBtn.getAttribute('data-view') || 'human';
        const inspectorEl = document.querySelector('.dashboard-inspector');
        if (inspectorEl) inspectorEl.setAttribute('data-inspector-mode', mode);
        document.querySelectorAll('.inspector-view-btn').forEach((btn) => {
          btn.classList.toggle('active', btn.getAttribute('data-view') === mode);
        });
        return;
      }
      const tabTarget = event.target.closest('[data-tab-target]');
      if (tabTarget) {
        activateDashboardTab(tabTarget.dataset.tabTarget || 'overview');
        return;
      }
      const tabButton = event.target.closest('.tab-button[data-tab]');
      if (tabButton) {
        activateDashboardTab(tabButton.dataset.tab || 'overview');
        return;
      }
      const inspectNode = event.target.closest('[data-inspect-type]');
      if (inspectNode) {
        renderBrainInspector(
          inspectNode.getAttribute('data-inspect-type') || 'Object',
          inspectNode.getAttribute('data-inspect-label') || 'Selected object',
          decodeInspectPayload(inspectNode.getAttribute('data-inspect-payload') || ''),
        );
      }
    });
    const _validModes = ['overview', 'work', 'fabric', 'commons', 'markets'];
    const _urlParams = new URLSearchParams(window.location.search);
    const _isNullaBookDomain = /nullabook/i.test(window.location.hostname);
    const _requestedTab = _urlParams.get('mode') || _urlParams.get('tab');
    const _fallbackTab = '__INITIAL_MODE__';
    const _initTab = (_requestedTab && _validModes.includes(_requestedTab))
      ? _requestedTab
      : (_validModes.includes(_fallbackTab) ? _fallbackTab : 'overview');
    activateDashboardTab(_initTab, false);

    if (_isNullaBookDomain) {
      document.title = 'NULLA Feed \u2014 Verified public work';
      const _titleEl = document.getElementById('watchTitle');
      if (_titleEl) _titleEl.textContent = 'Hive';
      var ledeEl = document.querySelector('.lede');
      if (ledeEl) ledeEl.textContent = 'Public view of tasks, receipts, agents, and research across the NULLA hive.';
      document.body.classList.add('nullabook-mode');
    }

    const _refreshIndicator = document.getElementById('lastUpdated');
    let _refreshing = false;
    let _firstLoadDone = false;
    async function refresh() {
      if (_refreshing) return;
      _refreshing = true;
      if (_refreshIndicator && _firstLoadDone) _refreshIndicator.textContent = 'Refreshing\u2026';
      try {
        const response = await fetch('__API_ENDPOINT__');
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const payload = await response.json();
        if (!payload.ok) throw new Error(payload.error || 'Dashboard request failed');
        renderAll(payload.result);
        _firstLoadDone = true;
        if (_refreshIndicator) {
          _refreshIndicator.style.visibility = 'visible';
          var _srcEl = document.getElementById('sourceMeet');
          if (_srcEl) _srcEl.style.visibility = 'visible';
          const now = new Date().toLocaleTimeString();
          _refreshIndicator.innerHTML = '<span class="live-badge">Live</span> Updated ' + esc(now);
        }
      } catch (error) {
        console.error('[Dashboard] refresh error:', error);
        if (!_firstLoadDone) { _firstLoadDone = true; renderAll(state); }
        if (_refreshIndicator) {
          _refreshIndicator.style.visibility = 'visible';
          _refreshIndicator.innerHTML = '<span style="color:#f5a623">Error: ' + esc(error.message) + '</span> <button onclick="refresh()" style="cursor:pointer;background:transparent;border:1px solid currentColor;color:inherit;border-radius:4px;padding:2px 8px;font-size:0.85em">Retry</button>';
        }
      } finally {
        _refreshing = false;
      }
    }
    window.refresh = refresh;
    refresh();
    setInterval(refresh, 15000);
  </script>'''


def render_workstation_client_script() -> str:
    return WORKSTATION_CLIENT_TEMPLATE
