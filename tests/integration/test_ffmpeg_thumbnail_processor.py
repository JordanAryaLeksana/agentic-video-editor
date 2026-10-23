import subprocess
from pathlib import Path

import pytest

from agentic_video_editor.infrastructure.media.ffmpeg_thumbnail_processor import (
    FFmpegThumbnailProcessor,
    ThumbnailProcessingError
)


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    video_path = tmp_path/"sample.mp4"

    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "lavfi",
            "-i", "testsrc2=size=320x240:rate=30",
            "-t", "2",
            "-c:v", "mpeg4",
            str(video_path),
        ],
        check=True,
        timeout=30,
    )

    return video_path


def test_generate_valid_thumbnail(
        sample_video: Path,
        tmp_path: Path
) -> None:
    output = tmp_path/"thumbnail.jpg"
    processor = FFmpegThumbnailProcessor()

    result = processor.generate(sample_video, output)
    assert result == output  
    assert output.is_file()
    assert output.stat().st_size > 0
    assert output.read_bytes()[:3] == b"\xff\xd8\xff"


def test_reject_invalid_video(tmp_path: Path) -> None:
    source = tmp_path / "invalid.mp4"
    source.write_text("not a real video")

    output = tmp_path / "thumbnail.jpg"
    processor = FFmpegThumbnailProcessor()

    with pytest.raises(ThumbnailProcessingError):
        processor.generate(source, output)

    assert not output.exists()


def test_reject_missing_video(tmp_path: Path) -> None:
    processor = FFmpegThumbnailProcessor()

    with pytest.raises(ThumbnailProcessingError):
        processor.generate(
            tmp_path / "missing.mp4",
            tmp_path / "thumbnail.jpg",
        )
