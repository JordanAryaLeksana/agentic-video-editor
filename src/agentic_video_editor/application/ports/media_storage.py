from typing import BinaryIO, Protocol


class MediaStorageError(Exception):
    """Raised when media storage operations fail."""


class MediaStorage(Protocol):
    def save(self, key: str, source: BinaryIO) -> int:
        """Save media from a binary stream and return size in bytes."""
        ...

    def open(self, key: str) -> BinaryIO:
        """Open stored media for reading. Caller must close it."""
        ...

    def delete(self, key: str) -> None:
        """Delete stored media if it exists."""
        ...
