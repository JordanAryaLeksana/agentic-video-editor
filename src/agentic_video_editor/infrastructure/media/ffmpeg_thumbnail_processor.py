import math
import subprocess
import os
from pathlib import Path
from uuid import uuid4


class ThumbnailProcessingError(Exception):
    pass

class FFmpegThumbnailProcessor:
    def __init__(self, executable:str = "ffmpeg", timeout_second: int = 60 ) -> None:
        self.executable = executable
        self.timeout_second = timeout_second


    def generate(
        self,
        source_path: Path, 
        output_path: Path,
        timestamp_seconds: float = 0.5,
    ) -> Path:
        if not source_path.is_file():
            raise ThumbnailProcessingError(
                "Source video does not exist"
            )

        if (
            not math.isfinite(timestamp_seconds)
            or timestamp_seconds < 0
        ):
            raise ValueError("Invalid thumbnail timestamp")

        if output_path.suffix.lower() not in {".jpg" , ".jpeg"}:
            raise ValueError("Thumbnail output must be jpg")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = output_path.with_name(
            f".{uuid4().hex}.jpg"
        )

        command= [
            self.executable,
            "-hide_banner",
            "-loglevel", "error",
            "-nostdin",
            "-i", str(source_path),
            "-ss", str(timestamp_seconds),
            "-frames:v", "1",
            "-q:v", "2",
            "-f", "image2",
            "-update", "1",
            str(temp_path),
        ]

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout_second
            )

            if (
                not temp_path.is_file()
                or temp_path.stat().st_size == 0
            ):
                raise ThumbnailProcessingError(
                    "FFmpeg produced to thumbnail"
                )

            os.replace(temp_path, output_path)
            return output_path
        except subprocess.CalledProcessError as exc:
            raise ThumbnailProcessingError(
                f"FFmpeg failed: {exc.stderr}"
            ) from exc

        except subprocess.TimeoutExpired as exc:
            raise ThumbnailProcessingError(
                "Thumbnail processing timed out"
            ) from exc

        except FileNotFoundError as exc:
            raise ThumbnailProcessingError(
                "FFmpeg executable was not found"
            ) from exc

        finally:
            temp_path.unlink(missing_ok=True)