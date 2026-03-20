from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_readme_frontloads_product_truth_and_install() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    early_block = "\n".join(readme.splitlines()[:120])

    assert "NULLA is a local-first AI agent" in early_block
    assert "Alpha truth:" in early_block
    assert "## Try It" in readme
    assert "docs/INSTALL.md" in readme
    assert "docs/STATUS.md" in readme
    assert "docs/SYSTEM_SPINE.md" in readme
    assert "docs/PROOF_PATH.md" in readme


def test_docs_home_only_points_to_curated_entry_docs() -> None:
    docs_home = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    assert "INSTALL.md" in docs_home
    assert "STATUS.md" in docs_home
    assert "SYSTEM_SPINE.md" in docs_home
    assert "PROOF_PATH.md" in docs_home
    assert "TRUST.md" in docs_home
    assert "archive/README.md" in docs_home
    assert "HANDOVER_" not in docs_home
    assert "NULLA_SALES_PITCH" not in docs_home


def test_docs_root_is_curated_after_archive_sweep() -> None:
    docs_root = REPO_ROOT / "docs"
    actual_files = {path.name for path in docs_root.iterdir() if path.is_file()}
    expected_files = {
        "BRAIN_HIVE_API_CONTRACT.md",
        "BRAIN_HIVE_ARCHITECTURE.md",
        "CUMULATIVE_STABILIZATION.md",
        "INSTALL.md",
        "LICENSING_MATRIX.md",
        "MEET_AND_GREET_API_CONTRACT.md",
        "MEET_AND_GREET_GLOBAL_TOPOLOGY.md",
        "MEET_AND_GREET_PREFLIGHT.md",
        "MEET_AND_GREET_SERVER_ARCHITECTURE.md",
        "MODEL_INTEGRATION_POLICY.md",
        "MODEL_PROVIDER_POLICY.md",
        "NULLA_OPENCLAW_TOOL_DOCTRINE.md",
        "OVERNIGHT_SOAK_RUNBOOK.md",
        "PROOF_PATH.md",
        "PROOF_PASS_REPORT.md",
        "PUBLIC_LAUNCH_READINESS.md",
        "README.md",
        "STATUS.md",
        "SYSTEM_SPINE.md",
        "TDL.md",
        "THIRD_PARTY_LICENSES.md",
        "TRUST.md",
    }

    assert actual_files == expected_files


def test_root_handover_and_starter_kit_redirect_to_current_truth() -> None:
    handover = (REPO_ROOT / "AGENT_HANDOVER.md").read_text(encoding="utf-8")
    starter_kit = (REPO_ROOT / "NULLA_STARTER_KIT.md").read_text(encoding="utf-8")

    assert "docs/SYSTEM_SPINE.md" in handover
    assert "docs/PROOF_PATH.md" in handover
    assert "docs/archive/README.md" in handover

    assert "docs/INSTALL.md" in starter_kit
    assert "docs/STATUS.md" in starter_kit
    assert "docs/PROOF_PATH.md" in starter_kit
