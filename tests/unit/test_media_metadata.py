from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from agentic_video_editor.domain.media import MediaMetadata


def test_media_metadata_valid():
    metadata = MediaMetadata(
        source_path=Path("sample_video.mp4"),
        duration_seconds=Decimal("120.5"),
        frame_rate=Fraction(30000, 1001),
        width=1920,
        height=1080,
        video_codec="h264",
        has_audio=True,
    )
    assert metadata.source_path == Path("sample_video.mp4")
    assert metadata.duration_seconds == Decimal("120.5")
    assert metadata.frame_rate == Fraction(30000, 1001)
    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.video_codec == "h264"
    assert metadata.has_audio is True


def test_media_metadata_invalid_duration():
    with pytest.raises(ValueError, match="Duration must be non-negative."):
        MediaMetadata(
            source_path=Path("sample_video.mp4"),
            duration_seconds=Decimal(-1),
            frame_rate=Fraction(30000, 1001),
            width=1920,
            height=1080,
            video_codec="h264",
            has_audio=True,
        )
