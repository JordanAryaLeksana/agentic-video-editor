
from uuid import UUID, uuid4

from agentic_video_editor.application.ports.media_repository import (
    MediaRepository,
)
from agentic_video_editor.application.ports.processing_job_repository import (
    ProcessingJobRepository,
)
from agentic_video_editor.domain.processing_job import (
    JobType,
    ProcessingJob,
)


class MediaNotFoundError(Exception):
    """Raised when the requested media does not exist."""


class CreateProcessingJobUseCase:
    def __init__(
        self,
        media_repository: MediaRepository,
        job_repository: ProcessingJobRepository,
    ) -> None:
        self._media_repository = media_repository
        self._job_repository = job_repository

    def execute(
        self,
        media_id: UUID,
        job_type: JobType = JobType.GENERATE_THUMBNAIL,
    ) -> ProcessingJob:
        # 1. Verify the media exists.
        media = self._media_repository.get_by_id(media_id)

        if media is None:
            raise MediaNotFoundError(
                f"Media not found: {media_id}"
            )

        # 2. Create a new processing job.
        job = ProcessingJob(
            id=uuid4(),
            media_id=media.id,
            job_type=job_type,
        )

        # 3. Persist the job.
        self._job_repository.save(job)

        return job
