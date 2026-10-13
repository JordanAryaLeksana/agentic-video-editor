from pathlib import Path
from agentic_video_editor.application.ports.media_probe import MediaProbe
from agentic_video_editor.domain.media import MediaMetadata


class IngestMediaUseCases:
    def __init__(self, media_probe: MediaProbe):
        self._media_probe = media_probe

    def execute(self, source_path: Path) -> MediaMetadata:
        return self._media_probe.probe(source_path)
