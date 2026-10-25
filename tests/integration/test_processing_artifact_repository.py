
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_video_editor.domain.processing_artifact import (
    ArtifactType,
    ProcessingArtifact,
)
from agentic_video_editor.domain.processing_job import (
    JobStatus,
    JobType,
)
from agentic_video_editor.infrastructure.persistence.model import (
    Base,
    MediaAssetRecord,
    ProcessingJobRecord,
)
from agentic_video_editor.infrastructure.persistence.sqlite import (
    configure_sqlite_foreign_keys,
)
from agentic_video_editor.infrastructure.persistence.sqlalchemy_processing_artifact_repository import (
    SQLAlchemyProcessingArtifactRepository,
)


def test_save_and_get_artifact(tmp_path) -> None:
    # Arrange: isolated SQLite database
    database_path = tmp_path / "test.db"

    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}"
    )
    configure_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    media_id = uuid4()
    job_id = uuid4()

    # Create parent records for foreign keys
    with session_factory.begin() as session:
        session.add(
            MediaAssetRecord(
                id=str(media_id),
                original_filename="video.mp4",
                storage_key=f"media/{media_id}/source.mp4",
                size_bytes=1024,
            )
        )

    with session_factory.begin() as session:
        session.add(
            ProcessingJobRecord(
                id=str(job_id),
                media_id=str(media_id),
                job_type=JobType.GENERATE_THUMBNAIL.value,
                status=JobStatus.RUNNING.value,
                attempts=1,
                max_attempts=3,
            )
        )

    repository = SQLAlchemyProcessingArtifactRepository(
        session_factory
    )

    artifact = ProcessingArtifact(
        id=uuid4(),
        job_id=job_id,
        artifact_type=ArtifactType.THUMBNAIL,
        storage_key=f"artifacts/{job_id}/thumbnail.jpg",
        size_bytes=2048,
    )

    # Act
    repository.save(artifact)

    result = repository.get_by_job_and_type(
        job_id,
        ArtifactType.THUMBNAIL,
    )

    # Assert
    assert result == artifact

    engine.dispose()
