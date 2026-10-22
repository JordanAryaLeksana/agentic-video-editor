from unittest.mock import Mock
from uuid import uuid4

import pytest

from agentic_video_editor.application.use_cases.create_processing_job import (
    CreateProcessingJobUseCase,
    MediaNotFoundError,
)
from agentic_video_editor.domain.media_asset import MediaAsset
from agentic_video_editor.domain.processing_job import (
    JobStatus,
    JobType,
)


def test_create_processing_job():
    media_id = uuid4()

    media = MediaAsset(
        id=media_id,
        original_filename="vlog.mp4",
        storage_key=f"media/{media_id}/source.mp4",
        size_bytes=1024,
    )

    media_repository = Mock()
    media_repository.get_by_id.return_value = media

    job_repository = Mock()

    use_case = CreateProcessingJobUseCase(
        media_repository=media_repository,
        job_repository=job_repository,
    )

    job = use_case.execute(
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
    )

    assert job.media_id == media_id
    assert job.status == JobStatus.PENDING
    assert job.attempts == 0
    assert job.job_type == JobType.GENERATE_THUMBNAIL

    media_repository.get_by_id.assert_called_once_with(media_id)
    job_repository.save.assert_called_once_with(job)


def test_reject_job_for_missing_media():
    media_repository = Mock()
    media_repository.get_by_id.return_value = None

    job_repository = Mock()

    use_case = CreateProcessingJobUseCase(
        media_repository=media_repository,
        job_repository=job_repository,
    )

    with pytest.raises(MediaNotFoundError):
        use_case.execute(media_id=uuid4())

    job_repository.save.assert_not_called()