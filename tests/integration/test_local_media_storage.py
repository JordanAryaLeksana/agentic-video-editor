from io import BytesIO

import pytest

from agentic_video_editor.application.ports.media_storage import (
    MediaStorageError,
)
from agentic_video_editor.infrastructure.storage.local_media_storage import (
    LocalMediaStorage,
)


def test_save_and_read_media(tmp_path):
    storage = LocalMediaStorage(tmp_path / "media")
    key = "videos/test/source.mp4"
    content = b"sample video bytes"

    size = storage.save(key, BytesIO(content))

    assert size == len(content)
    with storage.open(key) as stored_file:
        assert stored_file.read() == content


def test_delete_media(tmp_path):
    storage = LocalMediaStorage(tmp_path / "media")
    key = "videos/test/source.mp4"

    storage.save(key, BytesIO(b"video"))
    storage.delete(key)

    with pytest.raises(MediaStorageError):
        storage.open(key)


def test_reject_path_traversal(tmp_path):
    storage = LocalMediaStorage(tmp_path / "media")

    with pytest.raises(MediaStorageError):
        storage.save(
            "../outside.mp4",
            BytesIO(b"video"),
        )


def test_reject_empty_media(tmp_path):
    storage = LocalMediaStorage(tmp_path / "media")

    with pytest.raises(MediaStorageError, match="empty"):
        storage.save(
            "videos/test/source.mp4",
            BytesIO(b""),
        )


def test_reject_duplicate_storage_key(tmp_path):
    storage = LocalMediaStorage(tmp_path / "media")
    key = "videos/test/source.mp4"

    storage.save(key, BytesIO(b"original"))

    with pytest.raises(MediaStorageError, match="already exists"):
        storage.save(key, BytesIO(b"replacement"))

    with storage.open(key) as stored_file:
        assert stored_file.read() == b"original"
