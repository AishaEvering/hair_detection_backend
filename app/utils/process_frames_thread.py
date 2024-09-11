import queue

from flask import Flask
from app.utils.background_thread import BackgroundThread
import logging
from .detector import add_video_detections


class ProcessFramesThread(BackgroundThread):
    def __init__(self, thread_id: str, app: Flask, file_path: str, file_id: str):
        super().__init__(thread_id, app)
        self.logger = logging.getLogger(__name__)
        self.file_path = file_path
        self.file_id = file_id
        self.frame_queue = queue.Queue()
        self.app = app
        self.thread_id = thread_id
        self.progress = 0

    def startup(self) -> None:
        self.logger.info(
            f'Starting processing frames for file {self.file_id} thread id {self.thread_id}...')

    def shutdown(self) -> None:
        self.logger.info(
            f'Stopping processing frames for file {self.file_id}...')

    def get_frame_queue(self) -> queue.Queue:
        return self.frame_queue

    def get_id(self) -> str:
        return self.thread_id

    def handle(self) -> None:
        with self.app.app_context():
            for data, progress in add_video_detections(self.file_path, file_id=self.thread_id):
                self.progress = progress

                if data == b'--frame--\r\n':
                    self.frame_queue.put('DONE')
                    self.stop()
                    self.logger.info(
                        f"Processing complete for {self.file_id}.")
                    break
                else:
                    self.frame_queue.put(data)
