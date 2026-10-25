from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from agentic_video_editor.domain.processing_job import (
    JobStatus,
    JobType,
    ProcessingJob,
)
from agentic_video_editor.infrastructure.persistence.model import ProcessingJobRecord
from agentic_video_editor.application.ports.processing_job_repository import (
    ProcessingJobRepositoryError,
)


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
                    max_attempts=job.max_attempts,
                )
                session.add(record)
        except SQLAlchemyError as exc:
            raise ProcessingJobRepositoryError("Failed to save processing job") from exc

    def get_by_id(self, job_id: UUID) -> ProcessingJob | None:
        try:
            with self.session_factory.begin() as session:
                record = session.get(ProcessingJobRecord, str(job_id))

                if record is None:
                    return None

                return ProcessingJob(
                    id=UUID(record.id),
                    media_id=UUID(record.media_id),
                    job_type=JobType(record.job_type),
                    status=JobStatus(record.status),
                    attempts=record.attempts,
                    max_attempts=record.max_attempts,
                )
        except (SQLAlchemyError, ValueError) as exc:
            raise ProcessingJobRepositoryError(
                "Failed to retrieve processing job"
            ) from exc

    def claim_next_pending(self) -> ProcessingJob | None:
        try:
            with self.session_factory.begin() as session:
                candidate = (
                    select(ProcessingJobRecord.id)
                    .where(
                        ProcessingJobRecord.status == JobStatus.PENDING.value,
                        ProcessingJobRecord.attempts < ProcessingJobRecord.max_attempts,
                    )
                    .order_by(ProcessingJobRecord.id)
                    .limit(1)
                    .scalar_subquery()
                )

                statement = (
                    update(ProcessingJobRecord)
                    .where(
                        ProcessingJobRecord.id == candidate,
                        ProcessingJobRecord.status == JobStatus.PENDING.value,
                        ProcessingJobRecord.attempts < ProcessingJobRecord.max_attempts,
                    )
                    .values(
                        status=JobStatus.RUNNING.value,
                        attempts=ProcessingJobRecord.attempts + 1,
                    )
                    .returning(
                        ProcessingJobRecord.id,
                        ProcessingJobRecord.media_id,
                        ProcessingJobRecord.job_type,
                        ProcessingJobRecord.status,
                        ProcessingJobRecord.attempts,
                        ProcessingJobRecord.max_attempts,
                    )
                )

                row = session.execute(statement).one_or_none()

                if row is None:
                    return None

                return ProcessingJob(
                    id=UUID(row.id),
                    media_id=UUID(row.media_id),
                    job_type=JobType(row.job_type),
                    status=JobStatus(row.status),
                    attempts=row.attempts,
                    max_attempts=row.max_attempts,
                )

        except (SQLAlchemyError, ValueError) as exc:
            raise ProcessingJobRepositoryError(
                "Failed to claim processing job"
            ) from exc

        
    def mark_succeeded(
        self,
        job_id: UUID,
        attempt: int,
    ) -> bool:
        return self._finish_job(
            job_id=job_id,
            attempt=attempt,
            status=JobStatus.SUCCEEDED,
        )


    def mark_failed(
        self,
        job_id: UUID,
        attempt: int,
    ) -> bool:
        return self._finish_job(
            job_id=job_id,
            attempt=attempt,
            status=JobStatus.FAILED,
        )


    def _finish_job(
        self,
        job_id: UUID,
        attempt: int,
        status: JobStatus,
    ) -> bool:
        if attempt < 1:
            raise ValueError("attempt must be at least 1")

        try:
            with self.session_factory.begin() as session:
                statement = (
                    update(ProcessingJobRecord)
                    .where(
                        ProcessingJobRecord.id == str(job_id),
                        ProcessingJobRecord.status
                        == JobStatus.RUNNING.value,
                        ProcessingJobRecord.attempts == attempt,
                    )
                    .values(status=status.value)
                    .returning(ProcessingJobRecord.id)
                )

                updated_id = session.execute(
                    statement
                ).scalar_one_or_none()

                return updated_id is not None

        except SQLAlchemyError as exc:
            raise ProcessingJobRepositoryError(
                "Failed to update processing job status"
            ) from exc
