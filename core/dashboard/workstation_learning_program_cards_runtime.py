from __future__ import annotations

"""Learning-program card builders for the workstation dashboard client template."""

WORKSTATION_LEARNING_PROGRAM_CARDS_RUNTIME = '''
    function renderLearningMiniStats(items) {
      return `
        <div class="mini-grid">
          ${items.map(([label, value]) => `
            <div class="mini-stat">
              <strong>${esc(value)}</strong>
              <div>${esc(label)}</div>
            </div>
          `).join('')}
        </div>
      `;
    }

    function renderLearningProgramCard({title, summaryText, chipsHtml, bodyHtml, open = false, openStateKey = ''}) {
      return `
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
    }

    function buildTradingProgramBody(summary, decision, patternHealth, missed, edges, discoveries, flow, recentCalls) {
      const passReasons = decision.top_pass_reasons || [];
      const byAction = patternHealth.by_action || [];
      const topPatterns = patternHealth.top_patterns || [];
      const tradingOverviewHtml = renderLearningMiniStats([
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

      return `
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
    }

    function buildGenericKnowledgeBody(learning, memory, mesh, recentLearning) {
      const topClasses = learning.top_problem_classes || [];
      const topTags = learning.top_topic_tags || [];
      const genericOverviewHtml = renderLearningMiniStats([
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

      return `
        <div class="learning-program-grid">
          <article class="card">
            <h3>Overview</h3>
            ${genericOverviewHtml}
          </article>
          <article class="card">
            <h3>Memory Flow</h3>
            ${renderLearningMiniStats([
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
    }

    function buildActiveTopicProgramCards(activeTopics) {
      return activeTopics.map((topic) => renderLearningProgramCard({
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
              ${renderLearningMiniStats([
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
    }
'''
