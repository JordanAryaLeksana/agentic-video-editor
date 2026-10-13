from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MediaMetadata:
    """Metadata for a media file."""

    source_path: Path
    duration_seconds: Decimal
    width: int
    height: int
    frame_rate: Fraction
    video_codec: str
    has_audio: bool

    def __post_init__(self):
        if self.duration_seconds < 0:
            raise ValueError("Duration must be non-negative.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width and height must be positive integers.")
        if self.frame_rate <= 0:
            raise ValueError("Frame rate must be a positive value.")
