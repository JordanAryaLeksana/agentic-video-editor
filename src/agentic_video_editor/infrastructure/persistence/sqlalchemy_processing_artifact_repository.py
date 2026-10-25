
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from agentic_video_editor.application.ports.processing_artifact_repository import (
    ProcessingArtifactRepositoryError,
)
from agentic_video_editor.domain.processing_artifact import (
    ArtifactType,
    ProcessingArtifact,
)
from agentic_video_editor.infrastructure.persistence.model import (
    ProcessingArtifactRecord,
)


class SQLAlchemyProcessingArtifactRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self.session_factory = session_factory

    def save(self, artifact: ProcessingArtifact) -> None:
        try:
            with self.session_factory.begin() as session:
                record = ProcessingArtifactRecord(
                    id=str(artifact.id),
                    job_id=str(artifact.job_id),
                    artifact_type=artifact.artifact_type.value,
                    storage_key=artifact.storage_key,
                    size_bytes=artifact.size_bytes,
                )

                session.add(record)

        except SQLAlchemyError as exc:
            raise ProcessingArtifactRepositoryError(
                "Failed to save processing artifact"
            ) from exc

    def get_by_job_and_type(
        self,
        job_id: UUID,
        artifact_type: ArtifactType,
    ) -> ProcessingArtifact | None:
        try:
            with self.session_factory.begin() as session:
                statement = select(
                    ProcessingArtifactRecord
                ).where(
                    ProcessingArtifactRecord.job_id == str(job_id),
                    ProcessingArtifactRecord.artifact_type
                    == artifact_type.value,
                )

                record = session.execute(
                    statement
                ).scalar_one_or_none()

                if record is None:
                    return None

                return ProcessingArtifact(
                    id=UUID(record.id),
                    job_id=UUID(record.job_id),
                    artifact_type=ArtifactType(record.artifact_type),
                    storage_key=record.storage_key,
                    size_bytes=record.size_bytes,
                )

        except (SQLAlchemyError, ValueError) as exc:
            raise ProcessingArtifactRepositoryError(
                "Failed to retrieve processing artifact"
            ) from exc
