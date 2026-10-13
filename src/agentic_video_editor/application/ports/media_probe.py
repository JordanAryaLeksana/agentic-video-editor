from pathlib import Path
from typing import Protocol


class MediaProbeError(Exception):
    """Custom exception for media probing errors."""


class MediaProbe(Protocol):
    """Protocol for media probing functionality."""

    def probe(self, source_path: Path) -> dict:
        """Probe the media file and return its metadata as a dictionary."""
        ...
