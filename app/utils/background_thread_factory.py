import uuid
import logging

from flask import Flask
from app.utils.background_thread import BackgroundThread
from app.utils.clean_up_thread import CleanUpThread
from app.utils.process_frames_thread import ProcessFramesThread


class ThreadTypeNotImplementedError(Exception):
    pass


class ThreadNotFoundError(Exception):
    pass


class BackgroundThreadFactory:
    def __init__(self, app: Flask):
        self.threads = {}
        self.app = app
        self.logger = logging.getLogger(__name__)

    def create(self, thread_type: str, daemon: bool = True, file_path: str = None, file_id: str = None) -> BackgroundThread:
        try:
            thread_id = uuid.uuid4()

            if thread_type == "cleanup":
                thread = CleanUpThread(thread_id=thread_id, app=self.app)
            elif thread_type == "process_frames":
                thread = ProcessFramesThread(
                    thread_id=thread_id, app=self.app,
                    file_path=file_path, file_id=file_id)
            else:
                raise ThreadTypeNotImplementedError(
                    f"Thread type '{thread_type}' is not implemented.")

            if thread:
                thread.daemon = daemon
                self.threads[thread_id] = thread
                return thread
        except Exception as e:
            self.logger.info(
                f"Failed to create {thread_type} thread: {str(e)}")

    def get_thread(self, thread_id: str):
        for id, thread_object in self.threads.items():
            if thread_id == str(id):
                return thread_object
        raise ThreadNotFoundError(
            f'Thread {thread_id} not found')

    def delete(self, thread_id: str) -> None:
        try:
            thread = self.get_thread(thread_id)

            if thread and thread.is_alive():
                thread.stop()
        except ThreadNotFoundError:
            ...

        del self.threads[thread_id]
        self.logger.info(f"Thread with ID {thread_id} has been deleted.")
