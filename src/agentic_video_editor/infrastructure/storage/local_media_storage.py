import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from agentic_video_editor.application.ports.media_storage import MediaStorageError

CHUNK_SIZE = 1024 * 1024


class LocalMediaStorage:
    def __init__(self, root: Path):
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve_key(self, key: str):

        parts = key.split("/")

        if (
            not key
            or "\\" in key
            or "\x00" in key
            or any(part in ("", ".", "..") for part in parts)
        ):
            raise MediaStorageError("Invalid Storage key")

        path = self._root.joinpath(*parts)

        if not path.resolve().is_relative_to(self._root):
            raise MediaStorageError("Storage key escapes root")

        return path

    def save(self, key: str, source: BinaryIO) -> int:
        destination = self._resolve_key(key)

        destination.parent.mkdir(parents=True, exist_ok=True)

        destination = self._resolve_key(key)

        temp_path = None
        total_bytes = 0

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".upload-",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

                while chunk := source.read(CHUNK_SIZE):
                    temp_file.write(chunk)
                    total_bytes += len(chunk)

                temp_file.flush()
                os.fsync(temp_file.fileno())

            if total_bytes == 0:
                raise MediaStorageError("Cannot Save an empty media file")

            os.link(temp_path, destination)

            return total_bytes

        except FileExistsError as exc:
            raise MediaStorageError(f"Storage key already exists: {key}") from exc

        except OSError as exc:
            raise MediaStorageError(f"unable to save media:{key}") from exc

        finally:
            if temp_file is not None:
                temp_path.unlink(missing_ok=True)

    def open(self, key: str) -> BinaryIO:
        path = self._resolve_key(key)

        try:
            return path.open("rb")
        except OSError as exc:
            raise MediaStorageError(f"unable to open media: {key}") from exc

    def delete(self, key: str) -> None:
        path = self._resolve_key(key)

        try:
            return path.unlink(missing_ok=True)
        except OSError as exc:
            raise MediaStorageError(f"unable to delete media: {key}") from exc
    def path_for_processing(self, key: str) -> Path:
        path = self._resolve_key(key)

        if not path.is_file():
            raise MediaStorageError(
                f"Media file does not exist: {key}"
            )

        return path
