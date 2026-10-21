from uuid import uuid4
import pytest

from agentic_video_editor.domain.processing_job import (
    ProcessingJob,
    JobStatus,
    JobType
)

def test_new_job_is_pending():
    job = ProcessingJob(
        id=uuid4(),
        media_id=uuid4(),
        job_type=JobType.GENERATE_THUMBNAIL
    )

    assert job.status == JobStatus.PENDING
    assert job.attempts == 0
    assert job.max_attempts == 3

def test_reject_invalid_max_attemps():
    with pytest.raises(ValueError):
        ProcessingJob(
            id=uuid4(),
            media_id=uuid4(),
            job_type=JobType.GENERATE_THUMBNAIL,
            max_attempts=0,
        )


def test_reject_attemps_above_limit():
    with pytest.raises(ValueError):
        ProcessingJob(
            id=uuid4(),
            media_id=uuid4(),
            job_type=JobType.GENERATE_THUMBNAIL,
            attempts=4,
            max_attempts=3,
        )