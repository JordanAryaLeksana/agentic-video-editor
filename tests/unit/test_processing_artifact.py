
from uuid import uuid4

import pytest

from agentic_video_editor.domain.processing_artifact import (
    ArtifactType,
    ProcessingArtifact,
)


def test_reject_empty_artifact() -> None:
    with pytest.raises(
        ValueError,
        match="size_bytes must be positive",
    ):
        ProcessingArtifact(
            id=uuid4(),
            job_id=uuid4(),
            artifact_type=ArtifactType.THUMBNAIL,
            storage_key="artifacts/test/thumbnail.jpg",
            size_bytes=0,
        )
