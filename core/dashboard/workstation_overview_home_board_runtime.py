from __future__ import annotations

"""Workstation overview home-board card rendering helpers."""

WORKSTATION_OVERVIEW_HOME_BOARD_RUNTIME = '''
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
'''
