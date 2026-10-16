import subprocess
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from agentic_video_editor.api.main import app
from agentic_video_editor.infrastructure.persistence.sqlalchemy_media_repository import MediaAssetRecord

def test_upload_persist_media(tmp_path, monkeypatch):

    data_dir = tmp_path / "data"
    monkeypatch.setenv("AVE_DATA_DIR", str(data_dir))

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

    with TestClient(app) as client:
        with video_path.open("rb") as source:
            response = client.post(
                "/api/v1/media/", files={"file": ("sample.mp4", source, "video/mp4")}
            )

    assert response.status_code == 201

    payload = response.json()

    assert payload["filename"] == "sample.mp4"
    assert payload["size_bytes"] == video_path.stat().st_size


    engine = create_engine(
        f"sqlite+pysqlite:///{data_dir / 'media.db'}"
    )


    try:
        with Session(engine) as session:
            record = session.get(
                MediaAssetRecord,
                payload['media_id']
            )

        assert record is not None
        assert record.original_filename == "sample.mp4"

        stored_path = data_dir / "objects" / record.storage_key


        assert stored_path.is_file()

        assert stored_path.read_bytes() == video_path.read_bytes()
    finally:
        engine.dispose()

def test_get_media_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("AVE_DATA_DIR", str(tmp_path / "data"))

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/media/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Media Not Found"


