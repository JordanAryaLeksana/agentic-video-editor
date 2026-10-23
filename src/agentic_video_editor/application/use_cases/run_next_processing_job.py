
import logging
from typing import Protocol
from uuid import UUID

logger = logging.getLogger(__name__)


class ClaimedJob(Protocol):
    id: UUID
    attempts: int


class JobRepositoryPort(Protocol):
    def claim_next_pending(self) -> ClaimedJob | None:
        ...

    def mark_succeeded(
        self, job_id: UUID, attempt: int
    ) -> bool:
        ...

    def mark_failed(
        self, job_id: UUID, attempt: int
    ) -> bool:
        ...


class JobHandlerPort(Protocol):
    def handle(self, job: ClaimedJob) -> None:
        ...


class RunNextProcessingJob:
    def __init__(
        self,
        repository: JobRepositoryPort,
        handler: JobHandlerPort,
    ) -> None:
        self.repository = repository
        self.handler = handler

    def execute(self) -> bool:
        job = self.repository.claim_next_pending()

        if job is None:
            return False

        try:
            self.handler.handle(job)

        except Exception:
            logger.exception(
                "Processing failed for job %s",
                job.id,
            )

            updated = self.repository.mark_failed(
                job.id, job.attempts
            )

            if not updated:
                logger.warning(
                    "Could not mark job %s as failed",
                    job.id,
                )

            return True

        updated = self.repository.mark_succeeded(
            job.id, job.attempts
        )

        if not updated:
            logger.warning(
                "Could not mark job %s as succeeded",
                job.id,
            )

        return True
