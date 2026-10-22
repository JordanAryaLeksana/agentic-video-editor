from typing import Protocol
from uuid import UUID

from agentic_video_editor.domain.processing_job import (
    ProcessingJob,
)



class ProcessingJobRepositoryError(Exception):
    """Raised when processing job persistence fails."""

class ProcessingJobRepository(Protocol):
    def save(self, job: ProcessingJob) -> None:
        """Persist a new processing job."""
        ...

    def get_by_id(
        self,
        job_id: UUID,
    ) -> ProcessingJob | None:
        """Retrieve a processing job by its ID."""
        ...