from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from agentic_video_editor.application.ports.media_repository import MediaRepositoryError
from agentic_video_editor.domain.media_asset import MediaAsset
from agentic_video_editor.infrastructure.persistence.model import MediaAssetRecord




class SQLAlchemyMediaRepository:
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def save(self, asset: MediaAsset):

        try:
            with self.session_factory.begin() as session:
                record = MediaAssetRecord(
                    id=str(asset.id),
                    original_filename=asset.original_filename,
                    storage_key=asset.storage_key,
                    size_bytes=asset.size_bytes,
                )

                session.add(record)
        except SQLAlchemyError as exc:
            raise MediaRepositoryError("Unable to retrieve media asset") from exc

    def get_by_id(self, media_id: UUID) -> MediaAsset | None:
        try:
            with self.session_factory.begin() as session:
                record = session.get(MediaAssetRecord, str(media_id))

                if record is None:
                    return None

                return MediaAsset(
                    id=UUID(record.id),
                    original_filename=record.original_filename,
                    storage_key=record.storage_key,
                    size_bytes=record.size_bytes,
                )
        except SQLAlchemyError as exc:
            raise MediaRepositoryError("Unable to retrieve media asset") from exc


