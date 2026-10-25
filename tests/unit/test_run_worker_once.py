from uuid import uuid4
import pytest
from agentic_video_editor.domain.processing_job import (
    ProcessingJob,
    JobType,
    JobStatus,
)

from unittest.mock import Mock
from agentic_video_editor.application.use_cases.run_worker_once import RunWorkerOnceUseCase

def test_worker_return_false_when_no_job() -> None:
    jobs = Mock()
    jobs.claim_next_pending.return_value = None

    process = Mock()

    worker = RunWorkerOnceUseCase(
        jobs=jobs,
        process=process,
    )


    result = worker.execute()

    assert result is False

    jobs.claim_next_pending.assert_called_once()
    process.assert_not_called()
    jobs.mark_succeeded.assert_not_called()
    jobs.mark_failed.assert_not_called()

def test_worker_marks_job_succeeded() -> None:

    job = ProcessingJob(
        id=uuid4(),
        media_id=uuid4(),
        job_type=JobType.GENERATE_THUMBNAIL,
        status=JobStatus.RUNNING,
        attempts=1,
    )

    jobs = Mock()
    jobs.claim_next_pending.return_value = job
    jobs.mark_succeeded.return_value = True

    process = Mock()

    worker = RunWorkerOnceUseCase(
        jobs=jobs,
        process= process,
    )

    result = worker.execute()

    assert result is True
    process.assert_called_once_with(job)
    jobs.mark_succeeded.assert_called_once_with(
        job.id,
        job.attempts,
    )

    jobs.mark_failed.assert_not_called()


def test_worker_marks_failed_when_processor_raises() -> None:
    # Arrange
    job = ProcessingJob(
        id=uuid4(),
        media_id=uuid4(),
        job_type=JobType.GENERATE_THUMBNAIL,
        status=JobStatus.RUNNING,
        attempts=1,
    )

    jobs = Mock()
    jobs.claim_next_pending.return_value = job
    jobs.mark_failed.return_value = True

    process = Mock(
        side_effect=RuntimeError("FFmpeg failed")
    )

    worker = RunWorkerOnceUseCase(
        jobs=jobs,
        process=process,
    )

    # Act & Assert
    with pytest.raises(RuntimeError, match="FFmpeg failed"):
        worker.execute()

    process.assert_called_once_with(job)

    jobs.mark_failed.assert_called_once_with(
        job.id,
        job.attempts,
    )

    jobs.mark_succeeded.assert_not_called()


def test_worker_raises_when_completion_rejected() -> None:
    # Arrange
    job = ProcessingJob(
        id=uuid4(),
        media_id=uuid4(),
        job_type=JobType.GENERATE_THUMBNAIL,
        status=JobStatus.RUNNING,
        attempts=1,
    )

    jobs = Mock()
    jobs.claim_next_pending.return_value = job
    jobs.mark_succeeded.return_value = False

    process = Mock()

    worker = RunWorkerOnceUseCase(
        jobs=jobs,
        process=process,
    )

    # Act & Assert
    with pytest.raises(
        RuntimeError,
        match="Could not mark job",
    ):
        worker.execute()

    process.assert_called_once_with(job)

    jobs.mark_succeeded.assert_called_once_with(
        job.id,
        job.attempts,
    )

    jobs.mark_failed.assert_not_called()


def test_worker_raises_when_failures_update_rejected() -> None:
    job = ProcessingJob(
        id=uuid4(),
        media_id=uuid4(),
        job_type=JobType.GENERATE_THUMBNAIL,
        status=JobStatus.RUNNING,
        attempts=1,
    )

    jobs = Mock()
    jobs.claim_next_pending.return_value = job
    jobs.mark_failed.return_value = False

    process = Mock(
        side_effect=RuntimeError("FFmpeg failed")
    )

    worker = RunWorkerOnceUseCase(
        jobs=jobs,
        process=process,
    )

    # Act & Assert
    with pytest.raises(
        RuntimeError,
        match="Could not mark job",
    ) as exc_info:
        worker.execute()

    process.assert_called_once_with(job)

    jobs.mark_failed.assert_called_once_with(
        job.id,
        job.attempts,
    )

    jobs.mark_succeeded.assert_not_called()

    assert isinstance(
        exc_info.value.__cause__,
        RuntimeError,
    )
    assert str(exc_info.value.__cause__) == "FFmpeg failed"
