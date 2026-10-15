from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID

import pytest

from agentic_video_editor.application.ports.media_repository import (
    MediaRepositoryError,
)
from agentic_video_editor.application.use_cases.register_media import (
    RegisterMediaUseCase,
)
from agentic_video_editor.domain.media import MediaMetadata
from agentic_video_editor.infrastructure.storage.local_media_storage import (
    LocalMediaStorage,
)


class FakeMediaProbe:
    def probe(self, source_path: Path) -> MediaMetadata:
        return MediaMetadata(
            source_path=source_path,
            duration_seconds=Decimal(10),
            width=1920,
            height=1080,
            frame_rate=Fraction(30, 1),
            video_codec="h264",
            has_audio=True,
        )


class FakeMediaRepository:
    def __init__(self, fail: bool = False):
        self.assets = {}
        self.fail = fail

    def save(self, asset):
        if self.fail:
            raise MediaRepositoryError("Database unavailable")

        self.assets[asset.id] = asset

    def get_by_id(self, media_id: UUID):
        return self.assets.get(media_id)


def test_register_media_successfully(tmp_path):
    video_path = tmp_path / "input.mp4"
    video_path.write_bytes(b"fake video content")

    storage = LocalMediaStorage(tmp_path / "storage")
    repository = FakeMediaRepository()

    use_case = RegisterMediaUseCase(
        media_probe=FakeMediaProbe(),
        media_storage=storage,
        media_repository=repository,
    )

    asset = use_case.execute(video_path, "vlog.mp4")

    assert asset.id in repository.assets
    assert asset.size_bytes == len(b"fake video content")

    with storage.open(asset.storage_key) as file:
        assert file.read() == b"fake video content"


def test_cleanup_when_repository_fails(tmp_path):
    video_path = tmp_path / "input.mp4"
    video_path.write_bytes(b"fake video content")

    storage = LocalMediaStorage(tmp_path / "storage")
    repository = FakeMediaRepository(fail=True)

    use_case = RegisterMediaUseCase(
        media_probe=FakeMediaProbe(),
        media_storage=storage,
        media_repository=repository,
    )

    with pytest.raises(MediaRepositoryError):
        use_case.execute(video_path, "vlog.mp4")

    assert list((tmp_path / "storage").rglob("source.mp4")) == []
