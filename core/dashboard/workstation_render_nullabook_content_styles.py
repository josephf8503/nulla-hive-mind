from __future__ import annotations

"""NullaBook content styles for the workstation dashboard."""

from core.dashboard.workstation_render_nullabook_directory_styles import (
    WORKSTATION_RENDER_NULLABOOK_DIRECTORY_STYLES,
)
from core.dashboard.workstation_render_nullabook_fabric_styles import (
    WORKSTATION_RENDER_NULLABOOK_FABRIC_STYLES,
)
from core.dashboard.workstation_render_nullabook_feed_styles import (
    WORKSTATION_RENDER_NULLABOOK_FEED_STYLES,
)

WORKSTATION_RENDER_NULLABOOK_CONTENT_STYLES = (
    WORKSTATION_RENDER_NULLABOOK_FEED_STYLES
    + WORKSTATION_RENDER_NULLABOOK_DIRECTORY_STYLES
    + WORKSTATION_RENDER_NULLABOOK_FABRIC_STYLES
)
