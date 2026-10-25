
from typing import Protocol
from uuid import UUID

from agentic_video_editor.domain.processing_artifact import (
    ArtifactType,
    ProcessingArtifact,
)


class ProcessingArtifactRepositoryError(Exception):
    """Raised when artifact persistence fails."""


class ProcessingArtifactRepository(Protocol):
    def save(self, artifact: ProcessingArtifact) -> None:
        """Persist artifact metadata."""
        ...

    def get_by_job_and_type(
        self,
        job_id: UUID,
        artifact_type: ArtifactType,
    ) -> ProcessingArtifact | None:
        """Retrieve an artifact for a job and type."""
        ...
