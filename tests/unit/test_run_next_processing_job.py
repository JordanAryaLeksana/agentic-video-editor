
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4
import pytest
from agentic_video_editor.application.use_cases.run_next_processing_job import (
    RunNextProcessingJob,
)


def test_no_pending_job() -> None:
    repository = Mock()
    handler = Mock()

    repository.claim_next_pending.return_value = None

    use_case = RunNextProcessingJob(repository, handler)

    result = use_case.execute()

    assert result is False
    handler.handle.assert_not_called()
    repository.mark_succeeded.assert_not_called()
    repository.mark_failed.assert_not_called()


def test_job_processed_successfully() -> None:
    repository = Mock()
    handler = Mock()

    job = SimpleNamespace(
        id=uuid4(),
        attempts=1,
    )

    repository.claim_next_pending.return_value = job
    repository.mark_succeeded.return_value = True

    use_case = RunNextProcessingJob(repository, handler)

    result = use_case.execute()

    assert result is True
    handler.handle.assert_called_once_with(job)
    repository.mark_succeeded.assert_called_once_with(
        job.id, job.attempts
    )
    repository.mark_failed.assert_not_called()


def test_job_processing_failure() -> None:
    repository = Mock()
    handler = Mock()

    job = SimpleNamespace(
        id=uuid4(),
        attempts=1,
    )

    repository.claim_next_pending.return_value = job
    repository.mark_failed.return_value = True

    handler.handle.side_effect = RuntimeError(
        "FFmpeg processing failed"
    )

    use_case = RunNextProcessingJob(repository, handler)

    result = use_case.execute()

    assert result is True
    repository.mark_failed.assert_called_once_with(
        job.id, job.attempts
    )
    repository.mark_succeeded.assert_not_called()


def test_failure_transition_rejected_raises_error() -> None:
    # Arrange
    repository = Mock()
    handler = Mock()

    job = SimpleNamespace(
        id=uuid4(),
        attempts=1,
    )

    repository.claim_next_pending.return_value = job
    repository.mark_failed.return_value = False

    handler.handle.side_effect = RuntimeError(
        "FFmpeg processing failed"
    )

    use_case = RunNextProcessingJob(
        repository,
        handler,
    )

    # Act
    with pytest.raises(
        RuntimeError,
        match="Could not mark job",
    ) as exc_info:
        use_case.execute()

    # Assert
    handler.handle.assert_called_once_with(job)

    repository.mark_failed.assert_called_once_with(
        job.id,
        job.attempts,
    )

    repository.mark_succeeded.assert_not_called()

    assert str(exc_info.value.__cause__) == (
        "FFmpeg processing failed"
    )
