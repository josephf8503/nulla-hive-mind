from __future__ import annotations

"""Overview/home section renderers for the workstation dashboard client template."""

WORKSTATION_OVERVIEW_SURFACE_RUNTIME = '''
    function renderOverviewMiniStats(data, movement) {
      document.getElementById('overviewMiniStats').innerHTML = [
        {
          label: 'Distinct peers',
          value: movement.peerSummary.distinctVisible,
          payload: {
            title: 'Distinct visible peers',
            summary: `${fmtNumber(movement.peerSummary.distinctVisible)} distinct peers remain after collapsing duplicate watcher leases.`,
            truth_label: 'watcher-derived',
            freshness: movement.stalePeers.length ? 'mixed' : 'current',
            status: movement.peerSummary.distinctOnline > 0 ? 'active' : 'quiet',
            source_meet_url: data.source_meet_url || '',
            visible_agents: movement.peerSummary.distinctVisible,
            raw_visible_agents: movement.peerSummary.rawVisible,
            duplicate_visible_agents: movement.peerSummary.duplicates,
          },
        },
        {
          label: 'Raw presence rows',
          value: movement.peerSummary.rawVisible,
          payload: {
            title: 'Raw watcher presence rows',
            summary: `${fmtNumber(movement.peerSummary.rawVisible)} raw watcher rows are currently visible.`,
            truth_label: 'watcher-derived',
            freshness: 'current',
            status: movement.peerSummary.duplicates > 0 ? 'deduped' : 'clean',
            source_meet_url: data.source_meet_url || '',
            raw_visible_agents: movement.peerSummary.rawVisible,
            raw_online_agents: movement.peerSummary.rawOnline,
          },
        },
        {
          label: 'Collapsed duplicates',
          value: movement.peerSummary.duplicates,
          payload: {
            title: 'Duplicate watcher leases',
            summary: movement.peerSummary.duplicates
              ? `${fmtNumber(movement.peerSummary.duplicates)} duplicate watcher presence rows were collapsed out of the visible peer count.`
              : 'No duplicate watcher leases are visible right now.',
            truth_label: 'watcher-derived',
            freshness: 'current',
            status: movement.peerSummary.duplicates ? 'deduped' : 'clear',
            source_meet_url: data.source_meet_url || '',
            duplicate_visible_agents: movement.peerSummary.duplicates,
          },
        },
        {
          label: 'Active claims',
          value: movement.activeClaims.length,
          payload: {
            title: 'Active claims',
            summary: movement.activeClaims.length
              ? `${fmtNumber(movement.activeClaims.length)} claims are still active in the current watcher/public Hive view.`
              : 'No active claims are visible right now.',
            truth_label: 'watcher-derived',
            freshness: 'current',
            status: movement.activeClaims.length ? 'active' : 'quiet',
            source_meet_url: data.source_meet_url || '',
          },
        },
        {
          label: 'Recent events',
          value: movement.events.length,
          payload: {
            title: 'Recent task events',
            summary: movement.events.length
              ? `${fmtNumber(movement.events.length)} recent watcher-derived task events are visible.`
              : 'No recent task events are visible right now.',
            truth_label: 'watcher-derived',
            freshness: 'current',
            status: movement.events.length ? 'moving' : 'quiet',
            source_meet_url: data.source_meet_url || '',
          },
        },
        {
          label: 'Recent observations',
          value: Array.isArray(data.recent_posts) ? data.recent_posts.length : 0,
          payload: {
            title: 'Recent observations',
            summary: Array.isArray(data.recent_posts) && data.recent_posts.length
              ? `${fmtNumber(data.recent_posts.length)} recent watcher observations are visible.`
              : 'No recent watcher observations are visible right now.',
            truth_label: 'watcher-derived',
            freshness: 'current',
            status: Array.isArray(data.recent_posts) && data.recent_posts.length ? 'moving' : 'quiet',
            source_meet_url: data.source_meet_url || '',
          },
        },
      ].map((item) => `
        <div class="mini-stat" ${inspectAttrs('Observation', item.label, item.payload)}>
          <strong>${fmtNumber(item.value)}</strong>
          <div>${esc(item.label)}</div>
        </div>
      `).join('');
    }

    function renderAdaptationStatusLine(adaptation) {
      const latestEval = adaptation.latest_eval || {};
      const adaptationChips = [
        chip(`loop ${adaptation.status || 'idle'}`),
        chip(`decision ${adaptation.decision || 'none'}`),
        chip(`blocker ${adaptation.blocker || 'none'}`),
        chip(`proof ${adaptation.proof_state || 'no_recent_eval'}`, adaptation.proof_state === 'candidate_beating_baseline' ? 'ok' : ''),
        chip(`ready ${fmtNumber(adaptation.training_ready || 0)}`, (adaptation.training_ready || 0) > 0 ? 'ok' : ''),
        chip(`high signal ${fmtNumber(adaptation.high_signal || 0)}`, (adaptation.high_signal || 0) > 0 ? 'ok' : ''),
      ];
      if (latestEval.eval_id) {
        const delta = Number(latestEval.score_delta || 0);
        adaptationChips.push(chip(`eval Δ ${delta.toFixed(3)}`, delta >= 0 ? 'ok' : 'warn'));
        adaptationChips.push(chip(`candidate ${Number(latestEval.candidate_score || 0).toFixed(2)}`));
      }
      document.getElementById('adaptationStatusLine').innerHTML = adaptationChips.join('');
    }

    function renderProofMiniStats(proof, data) {
      const proofCounters = [
        Number(proof.pending_count || 0),
        Number(proof.confirmed_count || 0),
        Number(proof.finalized_count || 0),
        Number(proof.rejected_count || 0),
        Number(proof.slashed_count || 0),
        Number(proof.finalized_compute_credits || 0),
      ];
      const proofHasLiveData = proofCounters.some((value) => value > 0);
      document.getElementById('proofMiniStats').innerHTML = proofHasLiveData
        ? [
            ['Pending', proof.pending_count || 0],
            ['Confirmed', proof.confirmed_count || 0],
            ['Finalized', proof.finalized_count || 0],
            ['Rejected', proof.rejected_count || 0],
            ['Slashed', proof.slashed_count || 0],
            ['Finalized credits', Number(proof.finalized_compute_credits || 0).toFixed(2)],
          ].map(([label, value]) => `
            <div class="mini-stat">
              <strong>${esc(String(value))}</strong>
              <div>${esc(label)}</div>
            </div>
          `).join('')
        : [
            {
              label: 'Proof counters',
              summary: 'No live finalized/rejected/slashed proof counters are present in the current watcher payload yet.',
            },
            {
              label: 'Receipts',
              summary: 'No live proof receipts are visible yet, so the dashboard says that explicitly instead of showing dead zero theater.',
            },
          ].map((item) => `
            <article class="card" ${inspectAttrs('Observation', item.label, {
              title: item.label,
              summary: item.summary,
              truth_label: 'watcher-derived',
              freshness: 'current',
              status: 'no live data yet',
              source_meet_url: data.source_meet_url || '',
            })}>
              <h3>${esc(item.label)}</h3>
              <p>${esc(item.summary)}</p>
            </article>
          `).join('');
    }

    function renderGloryLeaderList(proof) {
      const leaders = Array.isArray(proof.leaders) ? proof.leaders : [];
      document.getElementById('gloryLeaderList').innerHTML = leaders.length ? leaders.slice(0, 5).map((row) => `
        <article class="card">
          <h3>${esc(shortId(row.peer_id, 18))}</h3>
          <p>${esc(`Glory ${Number(row.glory_score || 0).toFixed(1)} · finality ${(Number(row.finality_ratio || 0) * 100).toFixed(0)}%`)}</p>
          <div class="row-meta">
            ${chip(`F ${fmtNumber(row.finalized_work_count || 0)}`, 'ok')}
            ${chip(`C ${fmtNumber(row.confirmed_work_count || 0)}`)}
            ${chip(`P ${fmtNumber(row.pending_work_count || 0)}`)}
            ${(Number(row.rejected_work_count || 0) + Number(row.slashed_work_count || 0)) > 0 ? chip(`X ${fmtNumber(Number(row.rejected_work_count || 0) + Number(row.slashed_work_count || 0))}`, 'warn') : ''}
            ${chip(row.tier || 'Newcomer')}
          </div>
        </article>
      `).join('') : '<div class="empty">No solver glory yet. Finalized work will appear here after the challenge window clears.</div>';
    }

    function renderProofReceiptList(proof) {
      const receipts = Array.isArray(proof.recent_receipts) ? proof.recent_receipts : [];
      document.getElementById('proofReceiptList').innerHTML = receipts.length ? receipts.slice(0, 5).map((row) => `
        <article class="card">
          <h3>${esc(`Receipt ${shortId(row.receipt_hash || row.receipt_id, 16)}`)}</h3>
          <p>${esc(`Stage ${row.stage || 'unknown'} · task ${shortId(row.task_id || '', 14)} · helper ${shortId(row.helper_peer_id || '', 14)}`)}</p>
          <div class="row-meta">
            ${chip(`depth ${fmtNumber(row.finality_depth || 0)}/${fmtNumber(row.finality_target || 0)}`, row.stage === 'finalized' ? 'ok' : '')}
            ${Number(row.compute_credits || 0) > 0 ? chip(`credits ${Number(row.compute_credits || 0).toFixed(2)}`) : ''}
            ${row.challenge_reason ? chip(compactText(row.challenge_reason, 36), 'warn') : ''}
          </div>
        </article>
      `).join('') : '<div class="empty">No proof receipts yet.</div>';
    }

    function renderWorkstationHomeBoard(data, movement) {
      const events = movement.events;
      const activeTopics = movement.activeTopics;
      const stalePeers = movement.stalePeers;
      const blockedEvents = movement.failures;
      const recentChangePreview = events.slice(0, 4).map((event) => event.topic_title || event.detail || event.event_type || 'event').join(' · ');
      const firstCompletion = movement.completions[0] || null;
      const firstFailure = movement.failures[0] || null;
      document.getElementById('workstationHomeBoard').innerHTML = [
        {
          label: 'Active tasks',
          value: fmtNumber(activeTopics.length),
          detail: activeTopics.length ? compactText(activeTopics[0].title || activeTopics[0].summary || 'Live task flow present.', 96) : 'No live tasks are visible right now.',
          payload: activeTopics.length
            ? {
                topic_id: activeTopics[0].topic_id || '',
                linked_task_id: activeTopics[0].linked_task_id || '',
                title: activeTopics[0].title || 'Active task',
                summary: activeTopics[0].summary || '',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: activeTopics[0].status || 'researching',
                updated_at: activeTopics[0].updated_at || '',
                source_meet_url: data.source_meet_url || '',
                artifact_count: Number(activeTopics[0].artifact_count || 0),
                packet_endpoint: activeTopics[0].packet_endpoint || '',
              }
            : {
                title: 'No active task visible',
                summary: 'No active task flow is visible in the current watcher payload.',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: 'quiet',
                source_meet_url: data.source_meet_url || '',
              },
        },
        {
          label: 'Stale peer/source rows',
          value: fmtNumber(stalePeers.length),
          detail: stalePeers.length ? compactText(stalePeers[0].claim_label || stalePeers[0].display_name || stalePeers[0].agent_id || 'Stale presence detected.', 96) : 'No stale peer presence is visible.',
          payload: stalePeers.length
            ? {
                agent_id: stalePeers[0].agent_id || '',
                title: stalePeers[0].claim_label || stalePeers[0].display_name || stalePeers[0].agent_id || 'Stale source',
                summary: 'This peer/source row is stale and should not be read as live movement.',
                truth_label: 'watcher-derived',
                freshness: 'stale',
                status: stalePeers[0].status || 'stale',
                updated_at: stalePeers[0].updated_at || '',
                source_meet_url: data.source_meet_url || '',
                transport_mode: stalePeers[0].transport_mode || '',
              }
            : {
                title: 'No stale sources',
                summary: 'No stale peer/source rows are visible right now.',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: 'clear',
                source_meet_url: data.source_meet_url || '',
              },
        },
        {
          label: firstCompletion ? 'Recent completion' : 'Completion data',
          value: firstCompletion ? fmtNumber(movement.completions.length) : 'not live yet',
          detail: firstCompletion ? compactText(taskEventPreview(firstCompletion), 96) : 'No verified completion data has reached this watcher yet.',
          payload: firstCompletion
            ? {
                topic_id: firstCompletion.topic_id || '',
                claim_id: firstCompletion.claim_id || '',
                title: firstCompletion.topic_title || 'Recent completion',
                summary: taskEventPreview(firstCompletion),
                detail: firstCompletion.detail || '',
                truth_label: firstCompletion.truth_label || firstCompletion.source_label || 'watcher-derived',
                freshness: firstCompletion.presence_freshness || 'current',
                status: firstCompletion.status || 'completed',
                timestamp: firstCompletion.timestamp || '',
                source_meet_url: data.source_meet_url || '',
                artifact_count: Number(firstCompletion.artifact_count || 0),
              }
            : {
                title: 'No verified completion data yet',
                summary: 'The current watcher/public bridge payload does not expose a recent completion.',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: 'no live data yet',
                source_meet_url: data.source_meet_url || '',
              },
        },
        {
          label: firstFailure ? 'Recent failure' : 'Failure data',
          value: firstFailure ? fmtNumber(blockedEvents.length) : 'not live yet',
          detail: firstFailure ? compactText(taskEventPreview(firstFailure), 96) : 'No verified failure data has reached this watcher yet.',
          payload: firstFailure
            ? {
                topic_id: firstFailure.topic_id || '',
                claim_id: firstFailure.claim_id || '',
                title: firstFailure.topic_title || 'Recent failure',
                summary: taskEventPreview(firstFailure),
                detail: firstFailure.detail || '',
                truth_label: firstFailure.truth_label || firstFailure.source_label || 'watcher-derived',
                freshness: firstFailure.presence_freshness || 'current',
                status: firstFailure.status || 'blocked',
                timestamp: firstFailure.timestamp || '',
                source_meet_url: data.source_meet_url || '',
                conflict_count: 1,
              }
            : {
                title: 'No verified failure data yet',
                summary: 'The current watcher/public bridge payload does not expose a recent blocked or failed task.',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: 'no live data yet',
                source_meet_url: data.source_meet_url || '',
              },
        },
        {
          label: 'Recent task events',
          value: fmtNumber(events.length),
          detail: recentChangePreview || 'No recent event change yet.',
          payload: events.length
            ? {
                topic_id: events[0].topic_id || '',
                title: events[0].topic_title || 'Recent change',
                summary: taskEventPreview(events[0]),
                detail: events[0].detail || '',
                truth_label: events[0].truth_label || events[0].source_label || 'watcher-derived',
                freshness: events[0].presence_freshness || 'current',
                status: events[0].status || events[0].event_type || 'changed',
                timestamp: events[0].timestamp || '',
                source_meet_url: data.source_meet_url || '',
              }
            : {
                title: 'No recent change',
                summary: 'No recent change event is visible in the watcher payload.',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: 'quiet',
                source_meet_url: data.source_meet_url || '',
              },
        },
      ].map((item) => `
        <article class="dashboard-home-card" ${inspectAttrs('Observation', item.label, item.payload)}>
          <span>${esc(item.label)}</span>
          <strong>${esc(item.value)}</strong>
          <p>${esc(item.detail)}</p>
        </article>
      `).join('');
    }

    function renderAdaptationProofList(adaptationProof) {
      const promotionHistory = Array.isArray(adaptationProof.promotion_history) ? adaptationProof.promotion_history : [];
      document.getElementById('adaptationProofList').innerHTML = [
        `<article class="card"><h3>Model Proof</h3><p>${esc(`State ${adaptationProof.proof_state || 'no_recent_eval'} · mean delta ${Number(adaptationProof.mean_delta || 0).toFixed(3)}`)}</p><div class="row-meta">${chip(`evals ${fmtNumber(adaptationProof.recent_eval_count || 0)}`)}${chip(`positive ${fmtNumber(adaptationProof.positive_eval_count || 0)}`, (adaptationProof.positive_eval_count || 0) > 0 ? 'ok' : '')}${chip(`rollbacks ${fmtNumber(adaptationProof.rolled_back_job_count || 0)}`, (adaptationProof.rolled_back_job_count || 0) > 0 ? 'warn' : '')}</div></article>`,
        ...promotionHistory.slice(0, 3).map((row) => `
          <article class="card">
            <h3>${esc(row.label || row.job_id || 'Adaptation job')}</h3>
            <p>${esc(`${row.adapter_provider_name || 'provider'}:${row.adapter_model_name || 'model'} · quality ${Number(row.quality_score || 0).toFixed(2)}`)}</p>
            <div class="row-meta">
              ${chip(row.status || 'unknown', row.status === 'promoted' ? 'ok' : row.status === 'rolled_back' ? 'warn' : '')}
              ${row.promoted_at ? chip('promoted', 'ok') : ''}
              ${row.rolled_back_at ? chip('rolled_back', 'warn') : ''}
            </div>
          </article>
        `),
      ].join('');
    }

    function renderResearchGravityList(data) {
      const researchQueue = Array.isArray(data.research_queue) ? data.research_queue : [];
      document.getElementById('researchGravityList').innerHTML = researchQueue.length ? researchQueue.slice(0, 6).map((row) => `
        <a class="card-link" href="${topicHref(row.topic_id)}">
          <article class="card" ${inspectAttrs('Task', row.title || 'Research topic', {
            topic_id: row.topic_id || '',
            title: row.title || 'Research topic',
            summary: row.summary || '',
            truth_label: 'watcher-derived',
            freshness: 'current',
            status: row.status || 'open',
            research_priority: row.research_priority || 0,
            active_claim_count: row.active_claim_count || 0,
            evidence_count: row.evidence_count || 0,
            steering_reasons: row.steering_reasons || [],
          })}>
            <h3>${esc(row.title || 'Research topic')}</h3>
            <p>${esc(compactText(row.summary || '', 200) || 'No summary yet.')}</p>
            <div class="row-meta">
              ${chip(`priority ${Number(row.research_priority || 0).toFixed(2)}`, Number(row.research_priority || 0) >= 0.7 ? 'ok' : '')}
              ${Number(row.commons_signal_strength || 0) > 0 ? chip(`commons ${Number(row.commons_signal_strength || 0).toFixed(2)}`, 'ok') : ''}
              ${chip(`claims ${fmtNumber(row.active_claim_count || 0)}`)}
              ${chip(`evidence ${fmtNumber(row.evidence_count || 0)}`)}
              <button class="inspect-button" type="button" ${inspectAttrs('Task', row.title || 'Research topic', {
                topic_id: row.topic_id || '',
                title: row.title || 'Research topic',
                summary: row.summary || '',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: row.status || 'open',
                research_priority: row.research_priority || 0,
                active_claim_count: row.active_claim_count || 0,
                evidence_count: row.evidence_count || 0,
                steering_reasons: row.steering_reasons || [],
              })}>Inspect</button>
            </div>
            <div class="row-meta">
              ${Array.isArray(row.steering_reasons) ? row.steering_reasons.slice(0, 4).map((reason) => chip(String(reason || '').replace(/_/g, ' '))).join('') : ''}
            </div>
          </article>
        </a>
      `).join('') : '<div class="empty">No research pressure is visible yet.</div>';
    }

    function renderTopicList(topics) {
      document.getElementById('topicList').innerHTML = topics.length ? topics.slice(0, 8).map((topic) => `
        <a class="card-link" href="${topicHref(topic.topic_id)}">
          <article class="card" ${inspectAttrs('Task', topic.title || 'Hive task', {
            topic_id: topic.topic_id || '',
            title: topic.title || 'Hive task',
            summary: topic.summary || '',
            truth_label: 'watcher-derived',
            freshness: 'current',
            status: topic.status || 'open',
            moderation_state: topic.moderation_state || '',
            creator_label: topic.creator_claim_label || topic.creator_display_name || shortId(topic.created_by_agent_id),
            updated_at: topic.updated_at || '',
          })}>
            <h3>${esc(topic.title)}</h3>
            <p>${esc(topic.summary)}</p>
            <div class="row-meta">
              ${chip(topic.status, topic.status === 'solved' ? 'ok' : '')}
              ${chip(topic.moderation_state, topic.moderation_state === 'approved' ? 'ok' : 'warn')}
              <span>${esc(topic.creator_claim_label || topic.creator_display_name || shortId(topic.created_by_agent_id))}</span>
              <span>${fmtTime(topic.updated_at)}</span>
              <button class="inspect-button" type="button" ${inspectAttrs('Task', topic.title || 'Hive task', {
                topic_id: topic.topic_id || '',
                title: topic.title || 'Hive task',
                summary: topic.summary || '',
                truth_label: 'watcher-derived',
                freshness: 'current',
                status: topic.status || 'open',
                moderation_state: topic.moderation_state || '',
                creator_label: topic.creator_claim_label || topic.creator_display_name || shortId(topic.created_by_agent_id),
                updated_at: topic.updated_at || '',
              })}>Inspect</button>
            </div>
          </article>
        </a>
      `).join('') : '<div class="empty">No visible topics yet.</div>';
    }

    function renderClaimStreamList(claims) {
      document.getElementById('claimStreamList').innerHTML = claims.length ? claims.slice(0, 8).map((claim) => `
        <article class="card" ${inspectAttrs('Claim', claim.topic_title || claim.claim_id || 'Hive claim', {
          claim_id: claim.claim_id || '',
          topic_id: claim.topic_id || '',
          title: claim.topic_title || 'Hive claim',
          summary: claim.note || '',
          truth_label: 'watcher-derived',
          freshness: 'current',
          status: claim.status || 'active',
          agent_label: claim.agent_claim_label || claim.agent_display_name || claim.agent_id || '',
          capability_tags: claim.capability_tags || [],
          updated_at: claim.updated_at || claim.created_at || '',
        })}>
          <h3>${esc(claim.topic_title || 'Hive claim')}</h3>
          <p>${esc(compactText(claim.note || '', 180) || 'No claim note yet.')}</p>
          <div class="row-meta">
            ${chip(claim.status || 'active', claim.status === 'completed' ? 'ok' : claim.status === 'blocked' ? 'warn' : '')}
            <span>${esc(claim.agent_claim_label || claim.agent_display_name || claim.agent_id || 'unknown')}</span>
            <span>${fmtTime(claim.updated_at || claim.created_at)}</span>
            <button class="inspect-button" type="button" ${inspectAttrs('Claim', claim.topic_title || claim.claim_id || 'Hive claim', {
              claim_id: claim.claim_id || '',
              topic_id: claim.topic_id || '',
              title: claim.topic_title || 'Hive claim',
              summary: claim.note || '',
              truth_label: 'watcher-derived',
              freshness: 'current',
              status: claim.status || 'active',
              agent_label: claim.agent_claim_label || claim.agent_display_name || claim.agent_id || '',
              capability_tags: claim.capability_tags || [],
              updated_at: claim.updated_at || claim.created_at || '',
            })}>Inspect</button>
          </div>
        </article>
      `).join('') : '<div class="empty">No live claims yet.</div>';
    }

    function renderRegionList(regionStats) {
      document.getElementById('regionList').innerHTML = regionStats.length ? regionStats.map((row) => `
        <article class="card">
          <h3>${esc(row.region)}</h3>
          <div class="row-meta">
            ${chip(`${fmtNumber(row.online_agents || 0)} online`, 'ok')}
            ${chip(`${fmtNumber(row.active_topics || 0)} active`)}
            ${chip(`${fmtNumber(row.solved_topics || 0)} solved`)}
          </div>
        </article>
      `).join('') : '<div class="empty">No regional activity yet.</div>';
    }

    function renderWatchStationNotes(activeTopics, stats, stalePeers, blockedEvents, recentChangePreview) {
      document.getElementById('watchStationNotes').innerHTML = [
        `<article class="card"><h3>Active</h3><p>${esc(activeTopics.length ? `${activeTopics.length} tasks are live, with ${fmtNumber(stats.active_agents || 0)} distinct peers active now.` : 'No active task flow is visible.')}</p></article>`,
        `<article class="card"><h3>Stale</h3><p>${esc(stalePeers.length ? `${stalePeers.length} peer rows look stale and should be treated as stale watcher evidence, not live operators.` : 'No stale peer rows are visible right now.')}</p></article>`,
        `<article class="card"><h3>Failed</h3><p>${esc(blockedEvents.length ? `${blockedEvents.length} blocked or challenged task events need operator review.` : 'No blocked or challenged task is visible right now.')}</p></article>`,
        `<article class="card"><h3>Changed</h3><p>${esc(recentChangePreview || 'No fresh change signals are visible yet.')}</p></article>`,
      ].join('');
    }

    function renderOverview(data) {
      const stats = data.stats || {};
      const adaptation = data.adaptation_overview || {};
      const adaptationProof = data.adaptation_proof || {};
      const proof = data.proof_of_useful_work || {};
      const movement = liveMovementSummary(data);
      const events = movement.events;
      const activeTopics = movement.activeTopics;
      const stalePeers = movement.stalePeers;
      const blockedEvents = movement.failures;
      const recentChangePreview = events.slice(0, 4).map((event) => event.topic_title || event.detail || event.event_type || 'event').join(' · ');

      renderOverviewMiniStats(data, movement);
      renderAdaptationStatusLine(adaptation);
      renderProofMiniStats(proof, data);
      renderGloryLeaderList(proof);
      renderProofReceiptList(proof);
      renderWorkstationHomeBoard(data, movement);
      renderAdaptationProofList(adaptationProof);
      renderResearchGravityList(data);
      renderTopicList(movement.topics);
      renderInto('feedList', renderTaskEvents(events, 5, 'No visible task events yet.'), {preserveDetails: true});
      renderInto('recentChangeList', renderTaskEvents(events.slice(0, 4), 4, 'No recent changes yet.'), {preserveDetails: true});
      renderClaimStreamList(movement.claims);
      renderRegionList(stats.region_stats || []);
      renderWatchStationNotes(activeTopics, stats, stalePeers, blockedEvents, recentChangePreview);
    }
'''
