from dataclasses import dataclass
from uuid import UUID
from enum import Enum


class ArtifactType(str, Enum):
    THUMBNAIL = "thumbnail"


@dataclass(frozen=True, slots=True)
class ProcessingArtifact:
    id:UUID
    job_id:UUID
    artifact_type:ArtifactType
    storage_key: str
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.storage_key.strip():
            raise ValueError("storage_key cannot be empty")

        if self.size_bytes <= 0:
            raise ValueError("size_bytes must be positive")