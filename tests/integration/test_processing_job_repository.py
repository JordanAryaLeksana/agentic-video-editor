
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_video_editor.application.ports.processing_job_repository import (
    ProcessingJobRepositoryError,
)
from agentic_video_editor.domain.processing_job import (
    JobType,
    ProcessingJob,
)
from agentic_video_editor.infrastructure.persistence.model import (
    Base,
    MediaAssetRecord,
)
from agentic_video_editor.infrastructure.persistence.sqlite import (
    configure_sqlite_foreign_keys,
)
from agentic_video_editor.infrastructure.persistence.sqlalchemy_processing_job_repository import (
    SQLAlchemyPreprocessingJob,
)


@pytest.fixture
def job_repository(tmp_path):
    database_path = tmp_path / "jobs.db"

    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}"
    )

    configure_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)
    repository = SQLAlchemyPreprocessingJob(
        session_factory
    )

    # Create a valid media record first.
    media_id = uuid4()

    with session_factory.begin() as session:
        session.add(
            MediaAssetRecord(
                id=str(media_id),
                original_filename="video.mp4",
                storage_key=f"media/{media_id}/source.mp4",
                size_bytes=1024,
            )
        )

    try:
        yield repository, media_id
    finally:
        engine.dispose()


def test_save_and_get_processing_job(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )

    repository.save(job)

    stored_job = repository.get_by_id(job.id)

    assert stored_job == job


def test_get_nonexistent_job(job_repository):
    repository, _ = job_repository

    result = repository.get_by_id(uuid4())

    assert result is None


def test_reject_duplicate_job(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )

    repository.save(job)

    with pytest.raises(ProcessingJobRepositoryError):
        repository.save(job)

    assert repository.get_by_id(job.id) == job


def test_reject_job_with_missing_media(job_repository):
    repository, _ = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=uuid4(),
        job_type=JobType.GENERATE_THUMBNAIL,
    )

    with pytest.raises(ProcessingJobRepositoryError):
        repository.save(job)

    assert repository.get_by_id(job.id) is None
