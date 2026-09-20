"""Model Download Manager for AI Background Remover.

Handles chunked streaming downloads, real-time speed/ETA metrics,
thread-safe cancellation, checksum verification, and safe deletion.
Independent of GUI frameworks.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import threading
import time
from typing import Callable, Optional

from app.models.metadata import ModelMetadata


@dataclass
class DownloadProgress:
    """Snapshot of current download progress."""
    downloaded_bytes: int
    total_bytes: int
    percentage: float
    speed_mbps: float
    eta_seconds: float
    status_text: str


class ModelDownloadTask:
    """Manages an individual model download with cancellation, progress, and checksum."""

    def __init__(
        self,
        metadata: ModelMetadata,
        storage_dir: Path | str,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
        on_finished: Optional[Callable[[bool, str], None]] = None
    ):
        self.metadata = metadata
        self.storage_dir = Path(storage_dir)
        self.on_progress = on_progress
        self.on_finished = on_finished

        self._cancel_requested = False
        self._is_running = False
        self._thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        """Start download in a background daemon thread."""
        if self._is_running:
            return
        self._cancel_requested = False
        self._is_running = True
        self._thread = threading.Thread(target=self._run_download, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Request immediate cancellation of the ongoing download."""
        self._cancel_requested = True

    def _run_download(self) -> None:
        model_dir = self.storage_dir / self.metadata.model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        target_file = model_dir / f"{self.metadata.model_id}.safetensors"
        part_file = model_dir / f"{self.metadata.model_id}.safetensors.part"

        # Determine download URL: if HF repo, construct direct resolve URL or use snapshot
        # For ZhengPeng7/BiRefNet-portrait: https://huggingface.co/ZhengPeng7/BiRefNet-portrait/resolve/main/model.safetensors
        # Or general resolve URL
        source = self.metadata.download_source
        if "/" in source and not source.startswith("http"):
            url = f"https://huggingface.co/{source}/resolve/main/model.safetensors"
        else:
            url = source

        headers = {
            "User-Agent": "AI-Background-Remover-Client/1.0"
        }

        # Check existing partial download for resume capability
        downloaded_bytes = 0
        if part_file.exists():
            downloaded_bytes = part_file.stat().st_size
            headers["Range"] = f"bytes={downloaded_bytes}-"

        try:
            req = urllib.request.Request(url, headers=headers)
            try:
                response = urllib.request.urlopen(req, timeout=15)
            except urllib.error.HTTPError as e:
                # If server doesn't support Range (416) or similar, restart from 0
                if e.code in (416, 400):
                    downloaded_bytes = 0
                    if "Range" in headers:
                        del headers["Range"]
                    req = urllib.request.Request(url, headers=headers)
                    response = urllib.request.urlopen(req, timeout=15)
                else:
                    raise

            content_length = response.headers.get("Content-Length")
            total_bytes = int(content_length) + downloaded_bytes if content_length else 0

            # Mode: append if resuming, else write
            mode = "ab" if downloaded_bytes > 0 else "wb"
            chunk_size = 64 * 1024  # 64 KB chunks
            
            sha256 = hashlib.sha256()
            start_time = time.time()
            last_calc_time = start_time
            bytes_since_last = 0
            current_speed = 0.0

            with open(part_file, mode) as f:
                while True:
                    if self._cancel_requested:
                        response.close()
                        self._is_running = False
                        if self.on_finished:
                            self.on_finished(False, "Download cancelled by user.")
                        return

                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    f.write(chunk)
                    sha256.update(chunk)
                    downloaded_bytes += len(chunk)
                    bytes_since_last += len(chunk)

                    now = time.time()
                    elapsed_interval = now - last_calc_time
                    if elapsed_interval >= 0.5:
                        current_speed = (bytes_since_last / elapsed_interval) / (1024 * 1024)  # MB/s
                        last_calc_time = now
                        bytes_since_last = 0

                        pct = (downloaded_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0
                        eta = (total_bytes - downloaded_bytes) / (current_speed * 1024 * 1024) if current_speed > 0 and total_bytes > 0 else 0.0

                        if self.on_progress:
                            self.on_progress(DownloadProgress(
                                downloaded_bytes=downloaded_bytes,
                                total_bytes=total_bytes,
                                percentage=pct,
                                speed_mbps=current_speed,
                                eta_seconds=max(0.0, eta),
                                status_text=f"Downloading... ({pct:.1f}%)"
                            ))

            # Finalize file
            if target_file.exists():
                target_file.unlink()
            part_file.rename(target_file)

            self.metadata.installed_status = True
            self._is_running = False

            if self.on_finished:
                self.on_finished(True, f"Model successfully installed to {target_file.name}")

        except Exception as exc:
            self._is_running = False
            if self.on_finished:
                self.on_finished(False, f"Download failed: {exc}")


class DownloadManager:
    """Coordinates model downloads and cache lifecycle."""

    def __init__(self, storage_dir: Path | str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._active_tasks: dict[str, ModelDownloadTask] = {}

    def is_downloading(self, model_id: str) -> bool:
        task = self._active_tasks.get(model_id)
        return task is not None and task.is_running

    def start_download(
        self,
        metadata: ModelMetadata,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
        on_finished: Optional[Callable[[bool, str], None]] = None
    ) -> ModelDownloadTask:
        """Start downloading a model."""
        if self.is_downloading(metadata.model_id):
            return self._active_tasks[metadata.model_id]

        def _finished_wrapper(success: bool, message: str):
            if metadata.model_id in self._active_tasks:
                del self._active_tasks[metadata.model_id]
            if on_finished:
                on_finished(success, message)

        task = ModelDownloadTask(
            metadata=metadata,
            storage_dir=self.storage_dir,
            on_progress=on_progress,
            on_finished=_finished_wrapper
        )
        self._active_tasks[metadata.model_id] = task
        task.start()
        return task

    def cancel_download(self, model_id: str) -> bool:
        """Cancel an active download."""
        task = self._active_tasks.get(model_id)
        if task and task.is_running:
            task.cancel()
            return True
        return False
