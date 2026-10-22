
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
from agentic_video_editor.domain.processing_job import (
    JobStatus,
    JobType,
    ProcessingJob,
)
from concurrent.futures import ThreadPoolExecutor
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

def test_claim_pending_job_once(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )

    repository.save(job)

    claimed = repository.claim_next_pending()

    assert claimed is not None
    assert claimed.id == job.id
    assert claimed.status == JobStatus.RUNNING
    assert claimed.attempts == 1

    # Claiming again must not return the same job.
    second_claim = repository.claim_next_pending()

    assert second_claim is None

    # The updated state must be persisted.
    stored_job = repository.get_by_id(job.id)

    assert stored_job == claimed


def test_two_workers_cannot_claim_same_job(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )

    repository.save(job)

    # Simulate two workers trying to claim work.
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda _: repository.claim_next_pending(),
                range(2),
            )
        )

    successful_claims = [
        result for result in results if result is not None
    ]

    assert len(successful_claims) == 1
    assert successful_claims[0].id == job.id

    stored_job = repository.get_by_id(job.id)

    assert stored_job is not None
    assert stored_job.status == JobStatus.RUNNING
    assert stored_job.attempts == 1



def test_mark_job_succeeded(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )
    repository.save(job)

    claimed = repository.claim_next_pending()
    assert claimed is not None

    result = repository.mark_succeeded(
        claimed.id,
        claimed.attempts,
    )

    assert result is True

    stored = repository.get_by_id(job.id)
    assert stored is not None
    assert stored.status == JobStatus.SUCCEEDED

    # A completed job cannot be completed again.
    assert repository.mark_succeeded(
        claimed.id, claimed.attempts
    ) is False


def test_mark_job_failed(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )
    repository.save(job)

    claimed = repository.claim_next_pending()
    assert claimed is not None

    assert repository.mark_failed(
        claimed.id,
        claimed.attempts,
    ) is True

    stored = repository.get_by_id(job.id)
    assert stored is not None
    assert stored.status == JobStatus.FAILED


def test_reject_incorrect_attempt(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )
    repository.save(job)

    claimed = repository.claim_next_pending()
    assert claimed is not None

    result = repository.mark_succeeded(
        job_id=claimed.id,
        attempt=claimed.attempts + 1,
    )

    assert result is False

    stored = repository.get_by_id(job.id)
    assert stored is not None
    assert stored.status == JobStatus.RUNNING


def test_pending_job_cannot_complete(job_repository):
    repository, media_id = job_repository

    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )
    repository.save(job)

    # No worker has claimed this job yet.
    result = repository.mark_succeeded(
        job_id=job.id,
        attempt=1,
    )

    assert result is False

    stored = repository.get_by_id(job.id)
    assert stored is not None
    assert stored.status == JobStatus.PENDING
