from __future__ import annotations

"""NullaBook fabric telemetry styles for workstation dashboard."""

from core.dashboard.workstation_render_nullabook_fabric_ticker_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_TICKER_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_vitals_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_VITALS_STYLES,
)

WORKSTATION_RENDER_NULLABOOK_FABRIC_TELEMETRY_STYLES = (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_VITALS_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_TICKER_STYLES
)
