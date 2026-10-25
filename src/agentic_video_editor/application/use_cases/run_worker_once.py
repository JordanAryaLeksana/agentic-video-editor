import logging
from collections.abc import Callable
from dataclasses import dataclass
from agentic_video_editor.domain.processing_job import ProcessingJob
from agentic_video_editor.application.ports.processing_job_repository import ProcessingJobRepository


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RunWorkerOnceUseCase:
    jobs: ProcessingJobRepository
    process: Callable[[ProcessingJob], None]

    def execute(self) -> bool:
        job = self.jobs.claim_next_pending()

        if job is None:
            return False

        try:
            self.process(job)
        except Exception as exc:
            
            logger.exception(
                "Job processing failed: job_id=%s attempt=%s",
                job.id,
                job.attempts,
            )

            failed = self.jobs.mark_failed(
                job.id,
                job.attempts,
            )

            if not failed:
                raise RuntimeError(
                    f"Could not mark job {job.id} as failed"
                ) from exc

            raise
        completed = self.jobs.mark_succeeded(
            job.id, 
            job.attempts,
        )
        if not completed:
            raise RuntimeError(
                f"Could not mark job {job.id} as succeeded"
            )

        return True
