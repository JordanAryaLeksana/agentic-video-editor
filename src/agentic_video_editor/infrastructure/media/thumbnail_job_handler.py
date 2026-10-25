
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from agentic_video_editor.application.ports.media_repository import (
    MediaRepository,
)
from agentic_video_editor.application.ports.media_storage import (
    MediaStorageError,
)
from agentic_video_editor.application.ports.processing_artifact_repository import (
    ProcessingArtifactRepository,
)
from agentic_video_editor.application.use_cases.run_next_processing_job import (
    ClaimedJob,
)
from agentic_video_editor.domain.processing_artifact import (
    ArtifactType,
    ProcessingArtifact,
)
from agentic_video_editor.domain.processing_job import (
    JobType,
    ProcessingJob,
)
from agentic_video_editor.infrastructure.media.ffmpeg_thumbnail_processor import (
    FFmpegThumbnailProcessor,
)
from agentic_video_editor.infrastructure.storage.local_media_storage import (
    LocalMediaStorage,
)

logger = logging.getLogger(__name__)


class ThumbnailJobHandler:
    def __init__(
        self,
        media_repository: MediaRepository,
        storage: LocalMediaStorage,
        processor: FFmpegThumbnailProcessor,
        artifacts: ProcessingArtifactRepository,
    ) -> None:
        self.media_repository = media_repository
        self.storage = storage
        self.processor = processor
        self.artifacts = artifacts

    def handle(self, job: ClaimedJob) -> None:
        if not isinstance(job, ProcessingJob):
            raise TypeError("Expected ProcessingJob")

        if job.job_type != JobType.GENERATE_THUMBNAIL:
            raise ValueError("Unsupported job type")

        media = self.media_repository.get_by_id(job.media_id)

        if media is None:
            raise RuntimeError("Media asset not found")

        source_path = self.storage.path_for_processing(
            media.storage_key
        )

        artifact_key = f"artifacts/{job.id}/thumbnail.jpg"

        with TemporaryDirectory(prefix="ave-thumbnail-") as directory:
            output_path = Path(directory) / "thumbnail.jpg"

            self.processor.generate(
                source_path=source_path,
                output_path=output_path,
            )

            with output_path.open("rb") as source:
                size_bytes = self.storage.save(
                    artifact_key,
                    source,
                )

        artifact = ProcessingArtifact(
            id=uuid4(),
            job_id=job.id,
            artifact_type=ArtifactType.THUMBNAIL,
            storage_key=artifact_key,
            size_bytes=size_bytes,
        )

        try:
            self.artifacts.save(artifact)
        except Exception:
            try:
                self.storage.delete(artifact_key)
            except MediaStorageError:
                logger.exception(
                    "Failed to clean up artifact %s",
                    artifact_key,
                )
            raise
