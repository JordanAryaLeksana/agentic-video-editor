from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Annotated
from agentic_video_editor.application.use_cases.ingest_media import IngestMediaUseCases
from agentic_video_editor.bootstrap import build_ingest_media_use_case
from agentic_video_editor.application.ports.media_probe import MediaProbeError

app = FastAPI(
    title="Agentic Video Editor API",
    version="0.1.0",
)


class MediaProbeResponse(BaseModel):
    duration_seconds: str
    width: int
    height: int
    frame_rate: str
    video_codec: str
    has_audio: bool


MAX_UPLOAD_BYTES = 100 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
