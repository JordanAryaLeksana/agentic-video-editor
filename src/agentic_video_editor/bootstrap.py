
from agentic_video_editor.application.use_cases.ingest_media import IngestMediaUseCases
from agentic_video_editor.infrastructure.media.ffprobe_adapter import FFProbeMediaProbe
def build_ingest_media_use_case() -> IngestMediaUseCases:
    ffprobe = FFProbeMediaProbe()
    
    return IngestMediaUseCases(
        media_probe=ffprobe
    )