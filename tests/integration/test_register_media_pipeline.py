

import pytest
import subprocess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agentic_video_editor.bootstrap import (
    build_register_media_use_case,
)
from agentic_video_editor.infrastructure.persistence.model import Base
from agentic_video_editor.infrastructure.persistence.sqlalchemy_media_repository import SQLAlchemyMediaRepository
from agentic_video_editor.application.ports.media_probe import MediaProbeError
@pytest.fixture 
def media_pipeline(tmp_path):
    database_path = tmp_path / "test.db"
    storage_root = tmp_path / "storage"

    engine = create_engine(
         f"sqlite+pysqlite:///{database_path}"
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)
    use_case = build_register_media_use_case(
        session_factory=session_factory,
        storage_root=storage_root,
    )


    try:
        yield (
            use_case,
            SQLAlchemyMediaRepository(session_factory),
            storage_root,
        )

    finally:
        engine.dispose()


def test_register_real_video(tmp_path, media_pipeline):
    use_case, repository, storage_root = media_pipeline
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

    asset = use_case.execute(
        source_path = video_path,
        original_filename = "sample.mp4"
    )

    stored_asset = repository.get_by_id(asset.id)
    assert stored_asset == asset

    assert asset.original_filename == "sample.mp4"
    assert asset.size_bytes == video_path.stat().st_size

    # Verify physical media persistence.
    stored_path = storage_root / asset.storage_key

    assert stored_path.is_file()
    assert stored_path.read_bytes() == video_path.read_bytes()

def test_reject_invalid_video(tmp_path, media_pipeline):
    use_case, repository, storage_root = media_pipeline

    invalid_path = tmp_path / "invalid.mp4"
    invalid_path.write_bytes(b"not a real video")

    with pytest.raises(MediaProbeError):
        use_case.execute(
            source_path=invalid_path,
            original_filename="invalid.mp4"
        )

    assert list(storage_root.rglob("source.mp4")) == []