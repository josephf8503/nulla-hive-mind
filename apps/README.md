# apps/

This package owns process entrypoints and launch surfaces.

Rule:
entrypoints should stay thin.

They should do three things:

1. parse surface-specific arguments
2. call the canonical runtime bootstrap
3. launch the selected service or UI surface

They should not become a second home for business logic, feature policy, or storage internals.

## Canonical Surfaces

- `nulla_api_server.py`: local API / OpenClaw-compatible runtime surface
- `nulla_agent.py`: direct local agent shell
- `nulla_chat.py`: minimal chat surface
- `nulla_cli.py`: operator/maintenance CLI
- `nulla_daemon.py`: helper/network daemon
- `brain_hive_watch_server.py`: public/operator web surface
- `meet_and_greet_server.py`: public write / meet surface
- `meet_and_greet_node.py`: meet seed-node process

## Boundary Rule

If a change needs deep feature logic, move it into `core/`, `storage/`, `tools/`, or `network/`.

`apps/` should compose the machine, not become the machine.
