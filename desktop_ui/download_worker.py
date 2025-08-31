"""
Download Worker for Background Activity Downloads.

QThread-based worker for downloading Garmin activities in the background
with progress reporting and error handling.
"""

from pathlib import Path
import time
from typing import Dict, List, Optional

from PyQt6.QtCore import QMutex, QMutexLocker, QThread, pyqtSignal

from garmin_client.client import GarminConnectClient


class DownloadWorker(QThread):
    """Background worker for downloading Garmin activities."""

    # Enhanced signals for communication with main thread
    progress_updated = pyqtSignal(int, int, float)  # (current, total, percentage)
    activity_downloaded = pyqtSignal(int, str, bool, str)  # (activity_id, filename, success, details)
    download_completed = pyqtSignal(dict)  # final results summary
    error_occurred = pyqtSignal(str, str)  # (error_message, activity_context)
    status_updated = pyqtSignal(str, str)  # (status_message, detail_message)
    download_started = pyqtSignal(int, str)  # (activity_id, activity_name)
    rate_limit_wait = pyqtSignal(float)  # seconds remaining

    def __init__(
        self,
        client: GarminConnectClient,
        activity_ids: List[int],
        format_type: str = "fit",
        output_dir: Path = None,
        rate_limit_delay: float = 1.0,
    ):
        super().__init__()

        self.client = client
        self.activity_ids = activity_ids.copy()
        self.format_type = format_type
        self.output_dir = output_dir
        self.rate_limit_delay = rate_limit_delay

        # Thread control
        self._mutex = QMutex()
        self._should_stop = False
        self._paused = False

        # Progress tracking
        self.total_downloads = len(activity_ids)
        self.completed_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0

        # Results
        self.download_results = {}
        self.error_messages = []

    def run(self):
        """Main download execution loop."""
        try:
            self.status_updated.emit(f"Starting download of {self.total_downloads} activities...")

            for i, activity_id in enumerate(self.activity_ids):
                # Check if we should stop
                with QMutexLocker(self._mutex):
                    if self._should_stop:
                        self.status_updated.emit("Download cancelled by user")
                        break

                    # Handle pause
                    while self._paused and not self._should_stop:
                        self.status_updated.emit("Download paused...")
                        time.sleep(0.1)

                try:
                    # Enhanced status updates
                    activity_name = f"activity_{activity_id}"
                    self.download_started.emit(activity_id, activity_name)
                    self.status_updated.emit(
                        f"Downloading activity {activity_id}...",
                        f"Progress: {i+1}/{len(self.activity_ids)} ({((i+1)/len(self.activity_ids)*100):.1f}%)",
                    )

                    if downloaded_path := self.client.download_activity(activity_id, self.format_type, self.output_dir):
                        self.successful_downloads += 1
                        self.download_results[activity_id] = str(downloaded_path)
                        file_size = downloaded_path.stat().st_size if downloaded_path.exists() else 0
                        details = f"Downloaded {file_size:,} bytes" if file_size > 0 else "Downloaded successfully"
                        self.activity_downloaded.emit(activity_id, downloaded_path.name, True, details)
                    else:
                        self.failed_downloads += 1
                        self.download_results[activity_id] = None
                        self.activity_downloaded.emit(activity_id, "", False, "Download failed - no file returned")
                        self.error_messages.append(f"Failed to download activity {activity_id}")

                    self.completed_downloads += 1
                    progress_percent = (self.completed_downloads / self.total_downloads) * 100
                    self.progress_updated.emit(self.completed_downloads, self.total_downloads, progress_percent)

                except Exception as e:
                    self.failed_downloads += 1
                    self.download_results[activity_id] = None
                    error_msg = f"Error downloading activity {activity_id}: {str(e)}"
                    self.error_messages.append(error_msg)
                    self.error_occurred.emit(error_msg, f"Activity ID: {activity_id}")
                    self.activity_downloaded.emit(activity_id, "", False, f"Error: {str(e)}")

                    self.completed_downloads += 1
                    progress_percent = (self.completed_downloads / self.total_downloads) * 100
                    self.progress_updated.emit(self.completed_downloads, self.total_downloads, progress_percent)

                # Enhanced rate limiting with countdown
                if i < len(self.activity_ids) - 1 and self.rate_limit_delay > 0:
                    with QMutexLocker(self._mutex):
                        if not self._should_stop:
                            # Emit countdown updates for rate limiting
                            remaining_delay = self.rate_limit_delay
                            while remaining_delay > 0 and not self._should_stop:
                                self.rate_limit_wait.emit(remaining_delay)
                                sleep_time = min(0.1, remaining_delay)
                                time.sleep(sleep_time)
                                remaining_delay -= sleep_time

            # Emit completion signal
            results_summary = {
                "total": self.total_downloads,
                "successful": self.successful_downloads,
                "failed": self.failed_downloads,
                "results": self.download_results,
                "errors": self.error_messages,
            }

            self.download_completed.emit(results_summary)

            # Enhanced completion messages
            if self.successful_downloads > 0:
                success_rate = (self.successful_downloads / self.total_downloads) * 100
                self.status_updated.emit(
                    f"Download complete: {self.successful_downloads}/{self.total_downloads} successful",
                    f"Success rate: {success_rate:.1f}%",
                )
            else:
                self.status_updated.emit(
                    "Download failed: No activities downloaded successfully",
                    f"All {self.total_downloads} downloads failed",
                )

        except Exception as e:
            error_msg = f"Download worker error: {str(e)}"
            self.error_occurred.emit(error_msg, "Worker thread exception")
            self.status_updated.emit("Download failed due to unexpected error", f"Exception: {type(e).__name__}")

    def stop_download(self):
        """Request the download to stop with enhanced feedback."""
        with QMutexLocker(self._mutex):
            self._should_stop = True

        self.status_updated.emit(
            "Stopping download...", f"Completed: {self.completed_downloads}/{self.total_downloads}"
        )

    def pause_download(self):
        """Pause the download."""
        with QMutexLocker(self._mutex):
            self._paused = True

    def resume_download(self):
        """Resume the download."""
        with QMutexLocker(self._mutex):
            self._paused = False

    def is_paused(self) -> bool:
        """Check if download is paused."""
        with QMutexLocker(self._mutex):
            return self._paused

    def is_stopping(self) -> bool:
        """Check if download is stopping."""
        with QMutexLocker(self._mutex):
            return self._should_stop

    def get_progress(self) -> tuple:
        """Get current progress (completed, total)."""
        return self.completed_downloads, self.total_downloads

    def get_stats(self) -> Dict:
        """Get comprehensive download statistics."""
        progress_percent = (self.completed_downloads / self.total_downloads * 100) if self.total_downloads > 0 else 0
        success_rate = (
            (self.successful_downloads / self.completed_downloads * 100) if self.completed_downloads > 0 else 0
        )

        return {
            "total": self.total_downloads,
            "completed": self.completed_downloads,
            "successful": self.successful_downloads,
            "failed": self.failed_downloads,
            "remaining": self.total_downloads - self.completed_downloads,
            "progress_percent": progress_percent,
            "success_rate": success_rate,
            "is_paused": self._paused,
            "is_stopping": self._should_stop,
        }


class BulkDownloadManager:
    """Manager for handling multiple download workers and queuing."""

    def __init__(self, client: GarminConnectClient):
        self.client = client
        self.active_workers = []
        self.download_queue = []
        self.max_concurrent_workers = 1  # Conservative default

    def queue_download(
        self, activity_ids: List[int], format_type: str = "fit", output_dir: Path = None, rate_limit_delay: float = 1.0
    ) -> DownloadWorker:
        """Queue a new download job."""
        worker = DownloadWorker(self.client, activity_ids, format_type, output_dir, rate_limit_delay)

        self.download_queue.append(worker)
        return worker

    def start_next_download(self) -> Optional[DownloadWorker]:
        """Start the next download in the queue if possible."""
        if len(self.active_workers) < self.max_concurrent_workers and self.download_queue:
            worker = self.download_queue.pop(0)
            self.active_workers.append(worker)

            # Connect cleanup signal
            worker.finished.connect(lambda: self.cleanup_worker(worker))

            worker.start()
            return worker

        return None

    def cleanup_worker(self, worker: DownloadWorker):
        """Clean up completed worker."""
        if worker in self.active_workers:
            self.active_workers.remove(worker)

        # Start next download if available
        self.start_next_download()

    def stop_all_downloads(self):
        """Stop all active downloads."""
        for worker in self.active_workers:
            worker.stop_download()

    def get_active_count(self) -> int:
        """Get number of active downloads."""
        return len(self.active_workers)

    def get_queued_count(self) -> int:
        """Get number of queued downloads."""
        return len(self.download_queue)

    def set_max_concurrent(self, max_workers: int):
        """Set maximum concurrent downloads."""
        self.max_concurrent_workers = max(1, min(max_workers, 10))


# Example usage and testing
if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QProgressBar, QPushButton, QVBoxLayout, QWidget

    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Download Worker Test")
            self.setFixedSize(400, 200)

            widget = QWidget()
            self.setCentralWidget(widget)
            layout = QVBoxLayout(widget)

            self.progress_bar = QProgressBar()
            layout.addWidget(self.progress_bar)

            self.status_label = QLabel("Ready")
            layout.addWidget(self.status_label)

            self.download_button = QPushButton("Start Download")
            self.download_button.clicked.connect(self.start_download)
            layout.addWidget(self.download_button)

            self.stop_button = QPushButton("Stop Download")
            self.stop_button.clicked.connect(self.stop_download)
            self.stop_button.setEnabled(False)
            layout.addWidget(self.stop_button)

            self.worker = None

        def start_download(self):
            # Mock client for testing
            from unittest.mock import Mock

            mock_client = Mock()
            mock_client.download_activity.return_value = Path("/test/activity.fit")

            # Test with mock activity IDs
            self.worker = DownloadWorker(mock_client, [12345, 12346, 12347], "fit", rate_limit_delay=0.5)

            # Connect signals
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.status_updated.connect(self.update_status)
            self.worker.download_completed.connect(self.download_finished)

            # Update UI
            self.download_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            self.worker.start()

        def stop_download(self):
            if self.worker:
                self.worker.stop_download()

        def update_progress(self, current, total):
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

        def update_status(self, message):
            self.status_label.setText(message)

        def download_finished(self, results):
            self.download_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText(f"Finished: {results['successful']}/{results['total']} successful")

    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
