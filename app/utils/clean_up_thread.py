from app.utils.background_thread import BackgroundThread
import logging
import os
import time
from threading import Timer
from flask import Flask, current_app


class CleanUpThread(BackgroundThread):
    def __init__(self, thread_id: str, app: Flask, interval: int = 3600, age_in_seconds: int = 3600):
        super().__init__(thread_id, app)
        self.logger = logging.getLogger(__name__)
        self.interval = interval
        self.age_in_seconds = age_in_seconds
        self.app = app

        with self.app.app_context():
            self.temp_dir = current_app.config['TEMP_DIR']

    def startup(self) -> None:
        self.logger.info('Starting cleanup task scheduler...')
        self.cleaner = Timer(self.interval, self.clean_old_files).start()

    def shutdown(self) -> None:
        self.logger.info('Stopping cleanup task scheduler...')
        self.cleaner.cancel()

    def handle(self) -> None:
        ...

    def clean_old_files(self):
        with self.app.app_context():
            now = time.time()
            for file_path in os.listdir(self.temp_dir):
                full_path = os.path.join(self.temp_dir, file_path)
                if os.path.getmtime(full_path) < now - self.age_in_seconds:
                    try:
                        os.remove(full_path)
                        self.logger.info(f"Deleted file: {full_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete {full_path}: {e}")
