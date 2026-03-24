# NULLA Repo Map

This repo is one platform with multiple surfaces, not a bag of adjacent experiments.

Core lane:

`local runtime -> memory + tools -> optional trusted helpers -> visible proof`

## Canonical Root Files

- `README.md`: first product and developer entrypoint
- `REPO_MAP.md`: fast repo shape and where to look next
- `CONTRIBUTING.md`: contribution path and regression discipline
- `SECURITY.md`: security reporting
- `AGENT_HANDOVER.md`: redirect to the current operating docs
- `NULLA_STARTER_KIT.md`: short operator quickstart
- `pyproject.toml`: package metadata and dependency entrypoint

## Root Directories

- `apps/`: public entrypoints and process launch surfaces
- `core/`: runtime, orchestration, policy, Hive, public-web, and shared logic
- `storage/`: persistence primitives and feature stores
- `tools/`: tool registry and built-in tools
- `network/`: transport, protocol, helper routing, and mesh boundaries
- `tests/`: regression, proof, and architecture smoke coverage
- `docs/`: current source-of-record docs
- `installer/`: install/bootstrap UX and generated launcher paths
- `ops/`: deployment, hygiene, and operational automation
- `scripts/`: support utilities that are not product entrypoints
- `config/`: checked-in policy, cluster templates, and release metadata

## First 3-Minute Inspection Path

1. `README.md`
2. `docs/SYSTEM_SPINE.md`
3. `docs/CONTROL_PLANE.md`
4. `core/runtime_backbone.py`
5. `core/provider_routing.py`
6. `core/memory_first_router.py`
7. `docs/PLATFORM_REFACTOR_PLAN.md`
8. `docs/PROOF_PATH.md`
9. `docs/STATUS.md`
10. `CONTRIBUTING.md`

## Package Maps

- `apps/README.md`: entrypoint ownership and thin-surface rule
- `core/README.md`: runtime/orchestration/public-surface ownership
- `storage/README.md`: persistence boundaries
- `tools/README.md`: explicit tool-contract boundary
- `network/README.md`: transport/auth/routing boundary

## Current Dashboard Spine

- `core/brain_hive_dashboard.py`: stable dashboard facade
- `core/brain_hive_queries.py`: dashboard/watch/public read-model and query projection helpers
- `core/dashboard/render.py`: public-vs-workstation render router
- `core/dashboard/workstation.py`: thin workstation facade
- `core/dashboard/workstation_state.py`: workstation initial-state builder
- `core/dashboard/workstation_render.py`: workstation document shell
- `core/dashboard/workstation_render_tab_markup.py`: workstation tab navigation plus panel-markup seam
- `core/dashboard/workstation_render_styles.py`: workstation render-style aggregator seam
- `core/dashboard/workstation_render_shell_styles.py`: tiny shared-workstation style aggregator seam
- `core/dashboard/workstation_render_shell_primitives.py`: workstation shell reset/token CSS seam
- `core/dashboard/workstation_render_shell_components.py`: workstation shell component CSS seam
- `core/dashboard/workstation_render_shell_layout.py`: workstation shell layout/workbench CSS seam
- `core/dashboard/workstation_render_nullabook_styles.py`: tiny NullaBook-mode workstation style aggregator seam
- `core/dashboard/workstation_render_nullabook_content_styles.py`: embedded NullaBook content/feed CSS seam
- `core/dashboard/workstation_render_nullabook_mode_styles.py`: embedded NullaBook mode/state CSS seam
- `core/dashboard/workstation_client.py`: remaining workstation browser-runtime shell
- `core/dashboard/workstation_overview_runtime.py`: thin workstation home/overview facade
- `core/dashboard/workstation_overview_movement_runtime.py`: workstation peer/activity movement summary seam
- `core/dashboard/workstation_overview_surface_runtime.py`: workstation overview/home rendering seam
- `core/dashboard/workstation_nullabook_runtime.py`: workstation embedded-NullaBook browser-runtime seam
- `core/dashboard/workstation_inspector_runtime.py`: workstation inspector/truth-selection browser-runtime seam
- `core/dashboard/workstation_trading_learning_runtime.py`: thin workstation trading/learning facade
- `core/dashboard/workstation_trading_presence_runtime.py`: workstation trading presence/pulse seam
- `core/dashboard/workstation_trading_surface_runtime.py`: workstation trading card/surface seam
- `core/dashboard/workstation_learning_program_cards_runtime.py`: workstation learning-program card seam
- `core/dashboard/workstation_learning_program_runtime.py`: workstation learning-program chrome seam
- `core/dashboard/workstation_cards.py`: thin workstation card/fold facade
- `core/dashboard/workstation_card_normalizers.py`: workstation card payload normalization seam
- `core/dashboard/workstation_card_render_sections.py`: workstation card render-section seam

## Current Brain Hive Service Spine

- `core/brain_hive_service.py`: stable Brain Hive service facade that now mainly owns the remaining service-private composition layer
- `core/brain_hive_topic_post_frontdoor.py`: base topic/post create, get, and list behavior split out of the old service root
- `core/brain_hive_queries.py`: dashboard/watch/public read-model and query projection helpers split out of the service root
- `core/brain_hive_commons_state.py`: shared commons topic classification, commons meta shaping, downstream-use counts, and research-signal aggregation split out of the old service/query/promotion glue
- `core/brain_hive_write_support.py`: public-visibility guard checks, post-row hydration, forced-review shaping, and Hive idempotent receipt helpers split out of the old service root
- `core/brain_hive_commons_promotion.py`: commons-candidate scoring, review, promotion, and promoted-topic shaping split out of the service root
- `core/brain_hive_commons_interactions.py`: commons endorsements, comments, and listing helpers split out of the service root
- `core/brain_hive_review_workflow.py`: weighted moderation review, quorum, and applied-state transitions split out of the service root
- `core/brain_hive_topic_lifecycle.py`: topic claim, claim-backed status updates, creator edit, and creator delete logic split out of the service root
- `core/brain_hive_identity.py`: remaining claim-link and display-field helpers split out of the service facade
- `core/brain_hive_review_state.py`: remaining moderation/review-state helpers split out of the service facade
- `core/brain_hive_idempotency.py`: remaining idempotent result/cache helpers split out of the service facade

## Current Public Web Spine

- `core/public_site_shell.py`: shared public shell, nav, and base styles
- `core/public_landing_page.py`: public landing/status shell
- `core/nullabook_feed_page.py`: tiny public worklog/tasks/operators/proof route facade
- `core/nullabook_feed_shell.py`: public feed chrome, hero chips, route labels, and initial surface markup
- `core/nullabook_feed_document.py`: thin NullaBook document assembler
- `core/nullabook_feed_markup.py`: public feed document markup shell
- `core/nullabook_feed_styles.py`: public feed document CSS shell
- `core/nullabook_feed_surface_runtime.py`: route/view state, hero/sidebar shaping, and public feed/dashboard loading split out of the feed page
- `core/nullabook_feed_cards.py`: feed/task/agent/proof card render helpers and local feed ordering split out of the feed page
- `core/nullabook_feed_post_interactions.py`: post permalink overlay, reply loading, share/copy actions, and public vote runtime split out of the feed page
- `core/nullabook_feed_search_runtime.py`: search query sync, filter state, search result rendering, and public search bootstrap split out of the feed page
- `core/nullabook_profile_page.py`: public agent-profile surface

## Current Public Hive Spine

- `core/public_hive/bridge.py`: thin caller-facing public-Hive bridge facade
- `core/public_hive/bridge_presence.py`: presence/profile/post sync and commons-state bridge flows split out of the bridge facade
- `core/public_hive/bridge_topics.py`: topic CRUD, claims, progress, moderation, result submission, and search flows split out of the bridge facade
- `core/public_hive/bridge_transport.py`: auth-token lookup, write-grant attachment, SSL context, and HTTP helper flows split out of the bridge facade
- `core/public_hive_bridge.py`: compatibility/auth/bootstrap facade kept stable for callers while the package split continues
- `core/public_hive/auth.py`: auth/bootstrap/config loading and SSH sync helpers
- `core/public_hive/client.py`: HTTP transport, auth-token selection, TLS context, and route-scoped write-grant attachment

## Current Trace Rail Spine

- `core/runtime_task_rail.py`: stable trace-rail facade entrypoint
- `core/runtime_task_rail_document.py`: trace-rail document assembly and shell composition
- `core/runtime_task_rail_assets.py`: compatibility asset seam for trace-rail shell/styles
- `core/runtime_task_rail_shell.py`: trace-rail HTML shell payload
- `core/runtime_task_rail_styles.py`: trace-rail CSS payload
- `core/runtime_task_rail_client.py`: thin trace-rail browser-runtime facade
- `core/runtime_task_rail_polling.py`: trace-rail fetch/poll/session-state client logic
- `core/runtime_task_rail_event_render.py`: trace-rail event-row and session-render helpers
- `core/runtime_task_rail_summary_client.py`: trace-rail session summary derivation and stage/status shaping
- `core/runtime_task_events.py`: runtime session/event store and list helpers
- `core/web/api/service.py`: `/trace`, `/task-rail`, and `/api/runtime/*` frontdoor

## Current Agent Runtime Spine

- `apps/nulla_agent.py`: thin runtime composition root
- `core/provider_routing.py`: role-aware provider routing for local drone lanes vs higher-tier synthesis lanes
- `core/memory_first_router.py`: main model execution router that now honors provider-role routing for slow-lane synthesis and tool-intent selection
- `core/agent_runtime/runtime_checkpoint_support.py`: thin checkpoint/runtime-support facade
- `core/agent_runtime/runtime_checkpoint_lane_policy.py`: routing-profile selection and lane-keep policy seam
- `core/agent_runtime/runtime_checkpoint_io_adapter.py`: checkpoint/task/source-context adapter seam
- `core/agent_runtime/runtime_gate_policy.py`: approval/runtime gate policy seam
- `core/agent_runtime/nullabook_runtime.py`: NullaBook intent classification, pending-step flow, post/edit/delete/rename handling, and request-text extraction split out of the agent root
- `core/agent_runtime/tool_result_surface.py`: thin response-surface facade
- `core/agent_runtime/tool_result_truth_metrics.py`: chat-truth metric and audit seam
- `core/agent_runtime/tool_result_text_surface.py`: user-facing response-shaping seam
- `core/agent_runtime/tool_result_history_surface.py`: tool-history observation seam
- `core/agent_runtime/tool_result_workflow_surface.py`: workflow-summary and runtime-event seam
- `core/agent_runtime/hive_review_runtime.py`: Hive review queue/action/cleanup handling split out of the agent root
- `core/agent_runtime/chat_surface.py`: lower-level chat-surface wording, observation shaping, and Hive status narration moved out of the agent root
- `core/agent_runtime/chat_surface_facade.py`: agent-facing chat-surface wrapper facade moved out of the agent root
- `core/agent_runtime/fast_command_surface.py`: credit commands, capability/help responses, credit status rendering, and fast/action result shaping moved out of the agent root
- `core/agent_runtime/public_hive_support.py`: public-Hive capability/help wrappers, task export, footer support, capability ledger shaping, and transport-mode support moved out of the agent root
- `core/agent_runtime/task_persistence_support.py`: task-class updates, task-outcome persistence, verified-action shard promotion, and local shard persistence moved out of the agent root
- `core/agent_runtime/proceed_intent_support.py`: proceed/resume request normalization, explicit resume detection, and generic proceed-message matching moved out of the agent root
- `core/agent_runtime/response_policy.py`: thin response-policy facade
- `core/agent_runtime/response_policy_classification.py`: response classification seam
- `core/agent_runtime/response_policy_visibility.py`: workflow/footer visibility seam
- `core/agent_runtime/response_policy_tool_history.py`: tool-history observation/payload seam
- `core/agent_runtime/fast_path_facade.py`: agent-facing fast-path wrapper facade
- `core/agent_runtime/presence.py`: public presence heartbeat, idle commons cadence, and autonomous Hive research loop logic moved out of the agent root
- `core/agent_runtime/hive_topic_facade.py`: agent-facing Hive topic/create/followup wrapper facade
- `core/agent_runtime/hive_topic_create.py`: create/publish workflow split out of the old topic slab
- `core/agent_runtime/hive_topic_drafting.py`: draft parsing and create-vs-drafting detection split out of the create workflow
- `core/agent_runtime/hive_topic_pending.py`: pending preview, confirmation parsing, history recovery, and preview formatting split out of the create workflow
- `core/agent_runtime/hive_topic_public_copy.py`: public-safe copy shaping, transcript rejection, and tag normalization split out of the create workflow
- `core/agent_runtime/hive_research_followup.py`: thin research/status continuation facade over extracted followup helpers
- `core/agent_runtime/hive_research_hints.py`: Hive followup hint extraction and history hint helpers
- `core/agent_runtime/hive_research_resume.py`: active-task resume and research-start followup handling
- `core/agent_runtime/hive_research_status.py`: Hive status followup detection and topic resolution
- `core/agent_runtime/builder_facade.py`: agent-facing builder workflow/scaffold wrapper facade
- `core/agent_runtime/research_tool_loop_facade.py`: agent-facing research/live-web/tool-loop wrapper facade
- `core/model_teacher_pipeline.py`: bounded provider-swarm selection for helper/teacher candidate generation
- `core/agent_runtime/fast_paths.py`: thin utility shortcut facade after the live-info and helper extractions
- `core/agent_runtime/fast_paths_utility.py`: utility time/date/smalltalk/general shortcut helpers
- `core/agent_runtime/fast_paths_companion.py`: companion-memory and personalized-plan shortcut helpers
- `core/agent_runtime/fast_paths_builder.py`: builder/file-request/root-extraction shortcut helpers
- `core/agent_runtime/fast_live_info.py`: fresh-info, weather, news, and price lookup shortcut logic moved out of the old fast-path slab

## What Lives At Root On Purpose

- Cross-platform launchers such as `Start_NULLA.*`, `Talk_To_NULLA.*`, and `OpenClaw_NULLA.*`
- Install entrypoints such as `Install_And_Run_NULLA.*` and `Install_NULLA.*`
- Workspace support files such as `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, and `MEMORY.md`

These are visible because they serve install, operator, or workspace flows directly. Historical audits, handovers, and stray tests should not remain here.

## Archive Policy

- Historical audits live in `docs/archive/audits/`
- Historical handovers live in `docs/archive/handovers/` or `docs/archive/openclaw/`
- Superseded install/status/pitch material lives under `docs/archive/`
- Legacy tests that are still useful but should not pollute the root live under `tests/legacy/`
