from uuid import UUID
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from agentic_video_editor.domain.processing_job import (
    JobStatus,
    JobType,
    ProcessingJob,
)
from agentic_video_editor.infrastructure.persistence.model import ProcessingJobRecord
from agentic_video_editor.application.ports.processing_job_repository import ProcessingJobRepositoryError
class SQLAlchemyPreprocessingJob:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def save(self, job: ProcessingJob) -> None:
        try:
            with self.session_factory.begin() as session:
                record = ProcessingJobRecord(
                    id=str(job.id),
                    media_id=str(job.media_id),
                    job_type=job.job_type.value,
                    status=job.status.value,
                    attempts=job.attempts,
                    max_attempts= job.max_attempts,
                )
                session.add(record)
        except SQLAlchemyError as exc:
            raise ProcessingJobRepositoryError(
                "Failed to save processing job"
            ) from exc

    def get_by_id(self, job_id:UUID) -> ProcessingJob|None:
        try:
            with self.session_factory.begin() as session:
                record = session.get(
                    ProcessingJobRecord,
                    str(job_id)
                )

                if record is None:
                    return None

                return ProcessingJob(
                    id=UUID(record.id),
                    media_id=UUID(record.media_id),
                    job_type=JobType(record.job_type),
                    status=JobStatus(record.status),
                    attempts=record.attempts,
                    max_attempts=record.max_attempts
                )
        except (SQLAlchemyError, ValueError ) as exc:
            raise ProcessingJobRepositoryError(
                "Failed to retrieve processing job"
            ) from exc
