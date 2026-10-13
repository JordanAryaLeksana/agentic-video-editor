import json
import subprocess
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

from agentic_video_editor.application.ports.media_probe import MediaProbeError
from agentic_video_editor.domain.media import MediaMetadata


class FFProbeMediaProbe:
    def __init__(
        self, executable: str = "ffprobe", timeout_seconds: float = 30
    ) -> None:
        self._executable = executable
        self._timeout_seconds = timeout_seconds

    def probe(self, source_path: Path):
        if not source_path.is_file():
            raise MediaProbeError(f"Media file does not exist: {source_path}")
        command = [
            self._executable,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate",
            "-of",
            "json",
            str(source_path),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=self._timeout_seconds,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ) as exc:
            raise MediaProbeError(f"FFprobe failed for {source_path}: {exc}") from exc

        try:
            data = json.loads(result.stdout)
            streams = data.get("streams", [])

            video = next(
                (stream for stream in streams if stream.get("codec_type") == "video"),
                None,
            )

            if video is None:
                raise MediaProbeError("No video stream found in media files()")

            rate = video.get("avg_frame_rate")

            if not rate or rate == "0/0":
                rate = video.get("r_frame_rate")

            return MediaMetadata(
                source_path=source_path,
                duration_seconds=Decimal(data["format"]["duration"]),
                width=int(video["width"]),
                height=int(video["height"]),
                frame_rate=Fraction(rate),
                video_codec=video["codec_name"],
                has_audio=any(
                    stream.get("codec_type") == "audio" for stream in streams
                ),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            ZeroDivisionError,
            InvalidOperation,
            json.JSONDecodeError,
        ) as exc:
            raise MediaProbeError(f"invalid media metadata: {exc}") from exc
