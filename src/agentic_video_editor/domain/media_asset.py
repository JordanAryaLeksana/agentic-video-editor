from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MediaAsset:
    id: UUID
    original_filename: str
    storage_key: str
    size_bytes: str

    def __post_init__(self) -> None:
        if not self.original_filename.strip():
            raise ValueError("original filename cannot be empty")

        if not self.storage_key.strip():
            raise ValueError("storage key cannot be empty")

        if self.size_bytes <= 0:
            raise ValueError("size must be positive")
