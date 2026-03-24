from __future__ import annotations

from .bridge_presence_commons import PublicHiveBridgePresenceCommonsMixin
from .bridge_presence_nullabook import PublicHiveBridgePresenceNullabookMixin
from .bridge_presence_sync import PublicHiveBridgePresenceSyncMixin


class PublicHiveBridgePresenceMixin(
    PublicHiveBridgePresenceSyncMixin,
    PublicHiveBridgePresenceNullabookMixin,
    PublicHiveBridgePresenceCommonsMixin,
):
    pass
