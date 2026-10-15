from uuid import uuid4

import pytest

from agentic_video_editor.domain.media_asset import MediaAsset


def test_create_valid_media_asset():
    uuid = uuid4()

    asset = MediaAsset(
        id=uuid,
        original_filename="vlog.mp4",
        storage_key=f"media/{uuid}/source.mp4",
        size_bytes=1024,
    )

    assert asset.id == uuid
    assert asset.original_filename == "vlog.mp4"
    assert asset.size_bytes == 1024


def test_reject_empty_media():
    media_id = uuid4()

    with pytest.raises(ValueError, match="size"):
        MediaAsset(
            id=media_id,
            original_filename="empty.mp4",
            storage_key=f"media/{media_id}/source.mp4",
            size_bytes=0,
        )
