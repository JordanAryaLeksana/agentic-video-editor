import subprocess
from decimal import Decimal
from fractions import Fraction

import pytest

from agentic_video_editor.application.ports.media_probe import (
    MediaProbeError,
)
from agentic_video_editor.infrastructure.media.ffprobe_adapter import (
    FFProbeMediaProbe,
)


def test_probe_valid_video(tmp_path):
    video_path = tmp_path / "sample.mp4"

    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x240:r=30",
            "-t",
            "1",
            "-c:v",
            "mpeg4",
            "-y",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )

    probe = FFProbeMediaProbe()
    metadata = probe.probe(video_path)

    assert metadata.width == 320
    assert metadata.height == 240
    assert metadata.duration_seconds > Decimal(0)
    assert metadata.frame_rate == Fraction(30, 1)
    assert metadata.has_audio is False


def test_probe_missing_file(tmp_path):
    probe = FFProbeMediaProbe()

    with pytest.raises(MediaProbeError, match="does not exist"):
        probe.probe(tmp_path / "missing.mp4")


def test_probe_corrupted_file(tmp_path):
    video_path = tmp_path / "corrupted.mp4"
    video_path.write_bytes(b"not a valid video")

    probe = FFProbeMediaProbe()

    with pytest.raises(MediaProbeError, match="FFprobe failed"):
        probe.probe(video_path)
