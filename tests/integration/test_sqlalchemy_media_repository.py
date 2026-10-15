from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_video_editor.application.ports.media_repository import MediaRepositoryError
from agentic_video_editor.domain.media_asset import MediaAsset
from agentic_video_editor.infrastructure.persistence.model import Base
from agentic_video_editor.infrastructure.persistence.sqlalchemy_media_repository import (
    SQLAlchemyMediaRepository,
)


@pytest.fixture()
def repository(tmp_path: Path):
    database_path = tmp_path / "test.db"

    engine = create_engine(f"sqlite+pysqlite:///{database_path}")

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)

    try:
        yield SQLAlchemyMediaRepository(session_factory)
    finally:
        engine.dispose()


def test_save_and_get_media_asset(repository):
    media_id = uuid4()

    asset = MediaAsset(
        id=media_id,
        original_filename="vlog.mp4",
        storage_key=f"media/{media_id}/source.mp4",
        size_bytes=1024,
    )

    repository.save(asset)

    stored = repository.get_by_id(media_id)

    assert stored == asset


def test_get_nonexistence_media_asset(repository):
    result = repository.get_by_id(uuid4())

    assert result is None


def test_reject_media_duplicate_asset(repository):

    media_id = uuid4()

    asset = MediaAsset(
        id=media_id,
        original_filename="vlog.mp4",
        storage_key=f"media/{media_id}/source.mp4",
        size_bytes=1024,
    )

    repository.save(asset)

    with pytest.raises(MediaRepositoryError):
        repository.save(asset)

    assert repository.get_by_id(media_id) == asset
