from typing import Protocol
from uuid import UUID

from agentic_video_editor.domain.media_asset import MediaAsset


class MediaRepositoryError(Exception):
    """Raised when media persistence operations fail."""


class MediaRepository(Protocol):
    def save(self, asset: MediaAsset) -> None:
        """Persist a media asset."""
        ...

    def get_by_id(self, media_id: UUID) -> MediaAsset | None:
        """Retrieve a media asset by its ID."""
        ...
