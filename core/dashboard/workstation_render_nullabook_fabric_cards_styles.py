from __future__ import annotations

"""NullaBook fabric card and proof styles for workstation dashboard."""

from core.dashboard.workstation_render_nullabook_fabric_proof_card_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_PROOF_CARD_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_stat_card_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_STAT_CARD_STYLES,
)

WORKSTATION_RENDER_NULLABOOK_FABRIC_CARDS_STYLES = (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_STAT_CARD_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_PROOF_CARD_STYLES
)
