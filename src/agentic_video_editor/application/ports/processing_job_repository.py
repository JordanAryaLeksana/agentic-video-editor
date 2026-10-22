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

    def claim_next_pendind(self) -> ProcessingJob | None:
        """Atomically claim one pending job."""

    def mark_succeeded(
        self,
        job_id: UUID,
        attempt: int,
    ) -> bool:
        """Complete a claimed job successfully."""
        ...

    def mark_failed(
        self,
        job_id: UUID,
        attempt: int,
    ) -> bool:
        """Mark a claimed job as failed."""
        ...
