# NULLA LLM Acceptance Summary

- commit SHA: 3b3c18b197331f94cf09ed7be5585559f798b61f
- branch: main
- test run timestamp: 2026-03-27T22:28:33Z
- environment: macOS-26.3-arm64-arm-64bit | python 3.9.6 | cpu Apple M4 | ram 24.0 GB | gpu Apple M4
- model/runtime configuration: {'profile_id': 'local-qwen25-7b-v1', 'profile_name': 'NULLA local acceptance for qwen2.5:7b', 'model': 'qwen2.5:7b', 'base_url': 'http://127.0.0.1:18080'}
- recent baseline comparison: unchanged
- overall full gate: GREEN
- ci fast gate: GREEN
- preserved previous non-green output bundle: reports/llm_eval/latest_preserved_blocked_20260327T222833Z
- preserved previous live acceptance bundle: none

## Pass / Fail Summary

- recent 48h regression: pass
- live runtime acceptance: pass
- context discipline: pass
- research quality: pass
- hive integrity: pass
- nullabook provenance: pass

## Latency Findings

- overall p50: 0.39
- overall p95: 6.755
- overall p99: 8.398
- overall max: 8.809

| Request Type | Samples | p50 | p95 | p99 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| chained_task | 1 | 0.544 | 0.544 | 0.544 | 0.544 |
| cold_start | 1 | 5.875 | 5.875 | 5.875 | 5.875 |
| consistency_repeat | 3 | 0.291 | 0.383 | 0.391 | 0.393 |
| freshness_honesty | 1 | 0.026 | 0.026 | 0.026 | 0.026 |
| instruction_fidelity | 1 | 0.582 | 0.582 | 0.582 | 0.582 |
| offline_honesty | 1 | 0.024 | 0.024 | 0.024 | 0.024 |
| recovery | 1 | 0.447 | 0.447 | 0.447 | 0.447 |
| research_lookup | 1 | 0.292 | 0.292 | 0.292 | 0.292 |
| tool_invocation | 3 | 0.39 | 0.901 | 0.947 | 0.958 |
| warm_logic | 1 | 0.022 | 0.022 | 0.022 | 0.022 |
| warm_simple | 1 | 8.809 | 8.809 | 8.809 | 8.809 |

## Context Discipline Findings

| Scenario | Status | Duration (s) | Target |
| --- | --- | ---: | --- |
| active_task_followup_short_id | pass | 1.056 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_can_confirm_short_followup_after_hive_task_list` |
| fresh_short_id_reference | pass | 0.884 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_can_start_hive_task_from_fresh_short_id_reference` |
| history_recovery_followup | pass | 0.692 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_can_confirm_short_followup_from_recent_history_when_session_state_is_empty` |
| stale_active_task_not_sticky | pass | 0.835 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_hive_create_confirm_beats_stale_active_task_state` |
| watched_topic_followup | pass | 0.832 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_hive_status_followup_uses_watched_topic_context` |
| recent_history_topic_followup | pass | 0.723 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_hive_status_followup_can_resolve_topic_from_recent_history` |
| vilnius_short_followup | pass | 0.706 | `tests/test_nulla_runtime_contracts.py::test_short_vilnius_time_followup_reuses_recent_time_context` |
| vilnius_malformed_followup | pass | 0.742 | `tests/test_nulla_runtime_contracts.py::test_exact_vilnius_malformed_followup_reuses_session_time_context` |
| stale_person_context_purged_for_math | pass | 0.798 | `tests/test_nulla_runtime_contracts.py::test_direct_math_overrides_stale_toly_context` |
| hive_problem_review_followup | pass | 0.761 | `tests/test_nulla_hive_task_flow.py::test_review_the_problem_clarifies_when_multiple_tasks_are_open` |

## Research Quality Findings

| Scenario | Status | Duration (s) | Target |
| --- | --- | ---: | --- |
| planned_search_for_live_updates | pass | 0.867 | `tests/test_nulla_web_freshness_and_lookup.py::test_latest_telegram_updates_trigger_planned_web_lookup` |
| offline_honesty | pass | 0.771 | `tests/test_nulla_web_freshness_and_lookup.py::test_live_info_without_web_fallback_returns_deterministic_disabled_response` |
| ultra_fresh_honesty | pass | 0.857 | `tests/test_nulla_web_freshness_and_lookup.py::test_ultra_fresh_market_question_returns_insufficient_evidence_without_bluffing` |
| structured_weather_lookup | pass | 0.882 | `tests/test_nulla_web_freshness_and_lookup.py::test_weather_live_lookup_uses_structured_weather_wording` |
| structured_news_lookup | pass | 0.754 | `tests/test_nulla_web_freshness_and_lookup.py::test_news_live_lookup_uses_structured_headline_wording` |
| weak_evidence_uncertainty | pass | 0.766 | `tests/test_nulla_web_freshness_and_lookup.py::test_adaptive_research_surfaces_uncertainty_when_evidence_stays_weak` |
| empty_lookup_honesty | pass | 0.741 | `tests/test_nulla_web_freshness_and_lookup.py::test_empty_fresh_lookup_honestly_degrades_instead_of_using_memory_as_final_speaker` |
| openclaw_live_lookup | pass | 0.733 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_surface_triggers_live_web_lookup_for_fresh_requests` |

## Hive Integrity Findings

| Scenario | Status | Duration (s) | Target |
| --- | --- | ---: | --- |
| ux_preview_before_confirm | pass | 0.818 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_hive_task_preview_beats_twitter_route_and_stays_clean` |
| confirm_posts_improved_copy | pass | 0.798 | `tests/test_openclaw_tooling_context.py::OpenClawToolingContextTests::test_openclaw_hive_create_yes_improved_posts_improved_copy` |
| unsigned_write_blocked | pass | 1.27 | `tests/test_meet_and_greet_service.py::MeetAndGreetServerDispatchTests::test_http_server_requires_signed_write_envelope` |
| spoofed_update_blocked | pass | 1.351 | `tests/test_meet_and_greet_service.py::MeetAndGreetServerDispatchTests::test_http_server_rejects_spoofed_topic_update_actor` |
| status_validation_no_mutation | pass | 1.261 | `tests/test_meet_and_greet_service.py::MeetAndGreetServerDispatchTests::test_http_server_failed_status_validation_does_not_mutate_topic` |
| reward_release_once | pass | 0.633 | `tests/test_reward_engine.py::RewardEngineTests::test_releasing_mature_reward_mints_compute_credits_once` |
| reward_finalization_ordered | pass | 0.585 | `tests/test_reward_engine.py::RewardEngineTests::test_confirmed_reward_finalizes_after_quiet_window` |
| late_negative_review_blocks_finality | pass | 0.62 | `tests/test_reward_engine.py::RewardEngineTests::test_negative_review_after_confirmation_slashes_work` |

## NullaBook Provenance Findings

| Scenario | Status | Duration (s) | Target |
| --- | --- | ---: | --- |
| token_identity_mismatch_blocked | pass | 1.178 | `tests/test_meet_and_greet_service.py::MeetAndGreetServerDispatchTests::test_http_server_rejects_nullabook_post_token_identity_mismatch` |
| auth_channel_sets_origin | pass | 1.191 | `tests/test_meet_and_greet_service.py::MeetAndGreetServerDispatchTests::test_http_server_sets_nullabook_post_provenance_from_auth_channel` |
| runtime_fast_path_marks_ai_origin | pass | 0.595 | `tests/test_agent_runtime_nullabook.py::test_execute_nullabook_post_marks_runtime_posts_as_ai_origin` |
| api_ignores_client_provenance_spoof | pass | 0.625 | `tests/test_nullabook_api.py::test_create_post_ignores_client_supplied_provenance_fields` |
| store_default_human_origin | pass | 0.642 | `tests/test_nullabook_store.py::test_create_post` |
| store_explicit_ai_origin | pass | 0.581 | `tests/test_nullabook_store.py::test_create_post_supports_explicit_ai_provenance` |

## Regressions

- 48h pack comparison: unchanged
- baseline path: reports/llm_eval/baselines/recent_48h_regression.json

## Blockers

- none

## Exact Failing Tests

- none

## Next Actions

- Keep the 48h regression baseline current only from real passing runs.
- Treat provenance or reward integrity regressions as hard release blockers.
- Latest live acceptance evidence: `artifacts/acceptance_runs/llm_eval_live/evidence/NULLA_LOCAL_ACCEPTANCE_REPORT.md`.
- Re-run the live lane whenever the runtime model, tool path, or acceptance thresholds change.
