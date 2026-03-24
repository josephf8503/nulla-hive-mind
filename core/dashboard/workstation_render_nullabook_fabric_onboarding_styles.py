from __future__ import annotations

"""NullaBook fabric onboarding and community styles for workstation dashboard."""

from core.dashboard.workstation_render_nullabook_fabric_community_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_COMMUNITY_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_onboarding_steps_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_ONBOARDING_STEPS_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_responsive_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_RESPONSIVE_STYLES,
)

WORKSTATION_RENDER_NULLABOOK_FABRIC_ONBOARDING_STYLES = (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_ONBOARDING_STEPS_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_COMMUNITY_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_RESPONSIVE_STYLES
)
