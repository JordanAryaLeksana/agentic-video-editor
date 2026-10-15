import logging
from pathlib import Path
from uuid import uuid4

from agentic_video_editor.application.ports.media_probe import MediaProbe
from agentic_video_editor.application.ports.media_repository import MediaRepository
from agentic_video_editor.application.ports.media_storage import (
    MediaStorage,
    MediaStorageError,
)
from agentic_video_editor.domain.media_asset import MediaAsset

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


class RegisterMediaUseCase:
    def __init__(
        self,
        media_probe: MediaProbe,
        media_storage: MediaStorage,
        media_repository: MediaRepository,
    ):
        self._probe = media_probe
        self._storage = media_storage
        self._repository = media_repository

    def execute(
        self,
        source_path: Path,
        original_filename: str,
    ):
        # 1. Normalize user-provided filename
        filename = Path(original_filename.replace("\\", "/")).name.strip()
        if not filename or filename in {".", ".."}:
            raise ValueError("Invalid original filename")

        # 2. validate video using existing probe
        self._probe.probe(source_path)
        # 3. Generate Media_entity and Storage
        media_id = uuid4()
        extension = Path(filename).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            extension = ".bin"

        storage_key = f"media/{media_id}/source{extension}"
        # 4. Persist the pyhsical file
        with source_path.open("rb") as source:
            size_bytes = self._storage.save(storage_key, source)
        # 5. Create Domain entity and persist record

        try:
            asset = MediaAsset(
                id=media_id,
                original_filename=filename,
                storage_key=storage_key,
                size_bytes=size_bytes,
            )

            self._repository.save(asset)

        except Exception:
            # compensate if registration failed
            try:
                self._storage.delete(storage_key)
            except MediaStorageError:
                (
                    logger.exception(
                        "Failed To CleanUp Orphaned Media: %s",
                        storage_key,
                    ),
                )
            raise

        return asset
