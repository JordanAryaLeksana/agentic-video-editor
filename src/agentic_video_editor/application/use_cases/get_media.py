from uuid import UUID
from agentic_video_editor.application.ports.media_repository import MediaRepository
from agentic_video_editor.domain.media_asset import MediaAsset

class GetMediaUseCase:
    def __init__(self, media_repository: MediaRepository):
        self._media_repository = media_repository

    def execute(self, media_id: UUID) -> MediaAsset | None: 
        return self._media_repository.get_by_id(media_id)
        
        