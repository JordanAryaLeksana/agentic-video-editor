from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agentic_video_editor.api.main import app
from agentic_video_editor.application.ports.media_probe import (
    MediaProbeError,
)
from agentic_video_editor.application.use_cases.ingest_media import (
    IngestMediaUseCases,
)
from agentic_video_editor.bootstrap import build_ingest_media_use_case
from agentic_video_editor.domain.media import MediaMetadata


class FakeMediaProbe:
    def __init__(self) -> None:
        self.calls = 0
        self.uploaded_bytes = b""

    def probe(self, source_path: Path) -> MediaMetadata:
        self.calls += 1
        self.uploaded_bytes = source_path.read_bytes()

        if self.uploaded_bytes == b"invalid video":
            raise MediaProbeError("Invalid media")

        return MediaMetadata(
            source_path=source_path,
            duration_seconds=Decimal("10.5"),
            width=1920,
            height=1080,
            frame_rate=Fraction(30, 1),
            video_codec="h264",
            has_audio=True,
        )


@pytest.fixture
def client_and_probe():
    fake_probe = FakeMediaProbe()

    def override_use_case():
        return IngestMediaUseCases(media_probe=fake_probe)

    app.dependency_overrides[build_ingest_media_use_case] = override_use_case

    try:
        with TestClient(app) as client:
            yield client, fake_probe
    finally:
        app.dependency_overrides.pop(build_ingest_media_use_case, None)


def test_probe_valid_upload(client_and_probe):
    client, fake_probe = client_and_probe

    response = client.post(
        "/api/v1/media/probe",
        files={
            "file": (
                "sample.mp4",
                b"fake video content",
                "video/mp4",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["width"] == 1920
    assert data["height"] == 1080
    assert data["frame_rate"] == "30"
    assert data["video_codec"] == "h264"

    assert fake_probe.calls == 1
    assert fake_probe.uploaded_bytes == b"fake video content"


def test_probe_empty_upload(client_and_probe):
    client, fake_probe = client_and_probe

    response = client.post(
        "/api/v1/media/probe",
        files={"file": ("empty.mp4", b"", "video/mp4")},
    )

    assert response.status_code == 422
    assert fake_probe.calls == 0


def test_probe_invalid_video(client_and_probe):
    client, fake_probe = client_and_probe

    response = client.post(
        "/api/v1/media/probe",
        files={
            "file": (
                "invalid.mp4",
                b"invalid video",
                "video/mp4",
            )
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == ("Unable to read video metadata")
    assert fake_probe.calls == 1


def test_probe_upload_too_large(
    client_and_probe,
    monkeypatch,
):
    client, fake_probe = client_and_probe

    monkeypatch.setattr(
        "agentic_video_editor.api.main.MAX_UPLOAD_BYTES",
        4,
    )

    response = client.post(
        "/api/v1/media/probe",
        files={"file": ("large.mp4", b"12345", "video/mp4")},
    )

    assert response.status_code == 413
    assert fake_probe.calls == 0
