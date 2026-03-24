from __future__ import annotations

"""NullaBook telemetry, fabric, proof, and onboarding styles for the workstation dashboard."""

from core.dashboard.workstation_render_nullabook_fabric_cards_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_CARDS_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_onboarding_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_ONBOARDING_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_telemetry_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_TELEMETRY_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_timeline_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_TIMELINE_STYLES,
)

WORKSTATION_RENDER_NULLABOOK_FABRIC_STYLES = (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_TELEMETRY_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_TIMELINE_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_CARDS_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_ONBOARDING_STYLES
)
