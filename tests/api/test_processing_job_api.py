
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from agentic_video_editor.api.main import app
from agentic_video_editor.infrastructure.persistence.model import (
    MediaAssetRecord,
    ProcessingJobRecord,
)


@pytest.fixture
def job_api_client(tmp_path, monkeypatch):
    # Isolate this test from the development database.
    monkeypatch.setenv(
        "AVE_DATA_DIR",
        str(tmp_path / "data"),
    )

    # Entering TestClient starts FastAPI lifespan.
    with TestClient(app) as client:
        media_id = uuid4()

        # Prepare an existing media record.
        session_factory = client.app.state.session_factory

        with session_factory.begin() as session:
            session.add(
                MediaAssetRecord(
                    id=str(media_id),
                    original_filename="vlog.mp4",
                    storage_key=f"media/{media_id}/source.mp4",
                    size_bytes=1024,
                )
            )

        yield client, media_id


def test_create_processing_job_success(job_api_client):
    client, media_id = job_api_client

    response = client.post(
        f"/api/v1/media/{media_id}/jobs",
        json={"job_type": "generate_thumbnail"},
    )

    # Verify HTTP response.
    assert response.status_code == 201

    payload = response.json()

    assert payload["media_id"] == str(media_id)
    assert payload["job_type"] == "generate_thumbnail"
    assert payload["status"] == "pending"
    assert payload["attempts"] == 0
    assert payload["max_attempts"] == 3

    # Verify SQLite persistence.
    session_factory = client.app.state.session_factory

    with session_factory() as session:
        record = session.get(
            ProcessingJobRecord,
            payload["job_id"],
        )

        assert record is not None
        assert record.media_id == str(media_id)
        assert record.status == "pending"


def test_create_job_media_not_found(job_api_client):
    client, _ = job_api_client

    response = client.post(
        f"/api/v1/media/{uuid4()}/jobs",
        json={"job_type": "generate_thumbnail"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Media Not Found"


def test_create_job_invalid_uuid(job_api_client):
    client, _ = job_api_client

    response = client.post(
        "/api/v1/media/not-a-uuid/jobs",
        json={"job_type": "generate_thumbnail"},
    )

    assert response.status_code == 422


def test_create_job_invalid_job_type(job_api_client):
    client, media_id = job_api_client

    response = client.post(
        f"/api/v1/media/{media_id}/jobs",
        json={"job_type": "unsupported_job"},
    )

    assert response.status_code == 422
