
import os
from uuid import UUID
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Request
from pydantic import BaseModel
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from agentic_video_editor.application.ports.media_probe import MediaProbeError
from agentic_video_editor.application.use_cases.ingest_media import IngestMediaUseCases

from agentic_video_editor.application.use_cases.register_media import (
    RegisterMediaUseCase,
)
from agentic_video_editor.bootstrap import build_ingest_media_use_case, build_get_media_use_case
from agentic_video_editor.application.use_cases.get_media import GetMediaUseCase
from agentic_video_editor.infrastructure.persistence.model import Base
from agentic_video_editor.bootstrap import build_register_media_use_case
from agentic_video_editor.application.ports.media_probe import MediaProbeError
from agentic_video_editor.application.ports.media_repository import MediaRepositoryError
from agentic_video_editor.application.ports.media_storage import MediaStorageError
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app:FastAPI):
    data_dir = Path(
        os.environ.get("AVE_DATA_DIR", "data")
    ).expanduser().resolve()

    data_dir.mkdir(parents=True, exist_ok=True)

    database_path = data_dir / "media.db"
    storage_root = data_dir / "objects"

    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)


    app.state.session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    app.state.storage_root = storage_root

    try:
        yield

    finally:
        engine.dispose()

app = FastAPI(
    title="Agentic Video Editor API",
    version="0.1.0",
    lifespan=lifespan
)


class MediaProbeResponse(BaseModel):
    duration_seconds: str
    width: int
    height: int
    frame_rate: str
    video_codec: str
    has_audio: bool

class MediaRegisteredResponse(BaseModel):
    media_id: UUID
    filename: str
    size_bytes: int

class MediaGetResponse(BaseModel):
    media_id: UUID
    filename: str
    storage_key: str
    size_bytes: int

def get_register_media_use_case(
    request: Request,
) -> RegisterMediaUseCase:
    return build_register_media_use_case(
        session_factory=request.app.state.session_factory,
        storage_root=request.app.state.storage_root,
    )

def get_media_use_case(
        request: Request
) -> GetMediaUseCase:
    return build_get_media_use_case(
        session_factory=request.app.state.session_factory
    )

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/v1/media/{media_id}",response_model=MediaGetResponse)
def get_media(
    media_id: UUID, 
    use_case: Annotated[
        GetMediaUseCase,
        Depends(get_media_use_case)
    ]
) -> MediaGetResponse:
    asset = use_case.execute(
        media_id=media_id
    )
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Media Not Found"
        )

    return MediaGetResponse(
        media_id=asset.id,
        filename=asset.original_filename,
        size_bytes=asset.size_bytes,
        storage_key=asset.storage_key,
    )


    

@app.post("/api/v1/media/probe", response_model=MediaProbeResponse)
def probe_media(
    file: Annotated[UploadFile, File()],
    use_case: Annotated[IngestMediaUseCases, Depends(build_ingest_media_use_case)],
) -> MediaProbeResponse:

    with TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / "upload_media"
        total_bytes = 0

        with source_path.open("wb") as destination:
            while chunk := file.file.read(CHUNK_SIZE):
                total_bytes += len(chunk)

                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413, detail="Uploaded file is too Large"
                    )

                destination.write(chunk)
        if total_bytes == 0:
            raise HTTPException(status_code=422, detail="Uploaded file is empty")

        try:
            metadata = use_case.execute(source_path)
        except MediaProbeError as exc:
            raise HTTPException(
                status_code=422, detail="Unable to read video metadata"
            ) from exc

        return MediaProbeResponse(
            duration_seconds=str(metadata.duration_seconds),
            width=metadata.width,
            height=metadata.height,
            frame_rate=str(metadata.frame_rate),
            video_codec=metadata.video_codec,
            has_audio=metadata.has_audio,
        )



@app.post("/api/v1/media", response_model=MediaRegisteredResponse, status_code=201)
def register_media(
    file: Annotated[UploadFile, File()],
    use_case: Annotated[
        RegisterMediaUseCase,
        Depends(get_register_media_use_case),
    ],
) -> MediaRegisteredResponse:

    with TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir)/ "upload.bin"
        total_bytes = 0

        with source_path.open("wb") as destination:
            while chunk := file.file.read(CHUNK_SIZE):
                total_bytes += len(chunk)

                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Uploaded File is too Large"
                    )

                destination.write(chunk)
        if total_bytes == 0:
            raise HTTPException(
                status_code=422,
                detail="Uploaded file is empty",
            )    


        try:

            asset = use_case.execute(
                source_path=source_path,
                original_filename=file.filename or "",
            )


        except (MediaProbeError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail="Invalid media upload",
            ) from exc

        except (MediaStorageError, MediaRepositoryError) as exc:
            logger.exception("Media registration failed")

            raise HTTPException(
                status_code=500,
                detail="Unable to register media",
            ) from exc



        return MediaRegisteredResponse(
            media_id=asset.id,
            filename=asset.original_filename,
            size_bytes=asset.size_bytes,
        )