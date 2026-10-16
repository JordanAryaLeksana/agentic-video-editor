
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from agentic_video_editor.application.use_cases.ingest_media import (
    IngestMediaUseCases,
)
from agentic_video_editor.application.use_cases.register_media import (
    RegisterMediaUseCase,
)
from agentic_video_editor.infrastructure.media.ffprobe_adapter import (
    FFProbeMediaProbe,
)
from agentic_video_editor.infrastructure.persistence.sqlalchemy_media_repository import (
    SQLAlchemyMediaRepository,
)
from agentic_video_editor.infrastructure.storage.local_media_storage import (
    LocalMediaStorage,
)


def build_ingest_media_use_case() -> IngestMediaUseCases:
    ffprobe = FFProbeMediaProbe()

    return IngestMediaUseCases(media_probe=ffprobe)


def build_register_media_use_case(
    session_factory: sessionmaker[Session],
    storage_root: Path,
) -> RegisterMediaUseCase:
    media_probe = FFProbeMediaProbe()

    media_storage = LocalMediaStorage(
        root=storage_root,
    )

    media_repository = SQLAlchemyMediaRepository(
        session_factory=session_factory,
    )

    return RegisterMediaUseCase(
        media_probe=media_probe,
        media_storage=media_storage,
        media_repository=media_repository,
    )
