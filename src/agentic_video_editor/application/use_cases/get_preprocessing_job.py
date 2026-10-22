from uuid import UUID

from agentic_video_editor.application.ports.processing_job_repository import (
    ProcessingJobRepository
)

from agentic_video_editor.domain.processing_job import (
    ProcessingJob
)

class GetProcessingJobUseCase:
    def __init__(
        self,
        job_repository: ProcessingJobRepository,
    ) -> None:
        self._job_repository = job_repository

    def execute(
        self,
        job_id: UUID,
    ) -> ProcessingJob | None:
        return self._job_repository.get_by_id(job_id)