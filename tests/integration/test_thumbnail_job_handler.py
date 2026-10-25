
import shutil
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentic_video_editor.domain.media_asset import MediaAsset
from agentic_video_editor.domain.processing_artifact import ArtifactType
from agentic_video_editor.domain.processing_job import (
    JobStatus,
    JobType,
    ProcessingJob,
)
from agentic_video_editor.infrastructure.media.ffmpeg_thumbnail_processor import (
    FFmpegThumbnailProcessor,
)
from agentic_video_editor.infrastructure.media.thumbnail_job_handler import (
    ThumbnailJobHandler,
)
from agentic_video_editor.infrastructure.persistence.model import (
    Base,
    ProcessingJobRecord,
)
from agentic_video_editor.infrastructure.persistence.sqlite import (
    configure_sqlite_foreign_keys,
)
from agentic_video_editor.infrastructure.persistence.sqlalchemy_media_repository import (
    SQLAlchemyMediaRepository,
)
from agentic_video_editor.infrastructure.persistence.sqlalchemy_processing_artifact_repository import (
    SQLAlchemyProcessingArtifactRepository,
)
from agentic_video_editor.infrastructure.storage.local_media_storage import (
    LocalMediaStorage,
)


def test_real_thumbnail_handler(tmp_path):
    if shutil.which("ffmpeg") is None:
        pytest.skip("FFmpeg is not installed")

    # 1. Create a real sample video
    source_path = tmp_path / "sample.mp4"

    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-nostdin",
            "-f", "lavfi",
            "-i", "color=c=blue:s=320x240:r=25",
            "-t", "2",
            "-c:v", "mpeg4",
            "-y", str(source_path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )

    # 2. Create isolated SQLite database
    engine = create_engine(
        f"sqlite+pysqlite:///{tmp_path / 'test.db'}"
    )
    configure_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    storage = LocalMediaStorage(tmp_path / "objects")
    media_repository = SQLAlchemyMediaRepository(session_factory)
    artifact_repository = SQLAlchemyProcessingArtifactRepository(
        session_factory
    )

    # 3. Register real video
    media_id = uuid4()
    storage_key = f"media/{media_id}/source.mp4"

    with source_path.open("rb") as source:
        size_bytes = storage.save(storage_key, source)

    media = MediaAsset(
        id=media_id,
        original_filename="sample.mp4",
        storage_key=storage_key,
        size_bytes=size_bytes,
    )

    media_repository.save(media)

    # 4. Create running job
    job = ProcessingJob(
        id=uuid4(),
        media_id=media_id,
        job_type=JobType.GENERATE_THUMBNAIL,
        status=JobStatus.RUNNING,
        attempts=1,
    )

    with session_factory.begin() as session:
        session.add(
            ProcessingJobRecord(
                id=str(job.id),
                media_id=str(job.media_id),
                job_type=job.job_type.value,
                status=job.status.value,
                attempts=job.attempts,
                max_attempts=job.max_attempts,
            )
        )

    # 5. Run the real handler
    handler = ThumbnailJobHandler(
        media_repository=media_repository,
        storage=storage,
        processor=FFmpegThumbnailProcessor(),
        artifacts=artifact_repository,
    )

    handler.handle(job)

    # 6. Verify artifact persistence
    artifact = artifact_repository.get_by_job_and_type(
        job.id,
        ArtifactType.THUMBNAIL,
    )

    assert artifact is not None
    assert artifact.job_id == job.id
    assert artifact.size_bytes > 0

    with storage.open(artifact.storage_key) as thumbnail:
        assert thumbnail.read(2) == b"\xff\xd8"

    # Handler must not complete the job itself
    with session_factory.begin() as session:
        record = session.get(ProcessingJobRecord, str(job.id))
        assert record is not None
        assert record.status == JobStatus.RUNNING.value

    engine.dispose()
