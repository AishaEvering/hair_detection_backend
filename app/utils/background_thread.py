from abc import abstractmethod, ABC
import threading
import logging

from flask import Flask


class BackgroundThread(threading.Thread, ABC):
    def __init__(self, thread_id: str, app: Flask):
        super().__init__()
        self.thread_id = thread_id
        self.__stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)

    def stop(self) -> None:
        self.__stop_event.set()

    def _stopped(self) -> bool:
        return self.__stop_event.is_set()

    @abstractmethod
    def startup(self) -> None:
        """
        Method that is called before the thread starts.
        Initialize all necessary resources here.
        :return:None
        """
        raise NotImplementedError()

    @abstractmethod
    def shutdown(self) -> None:
        """
        Method that is callled shortly after stop() method was called.
        Use it to clean up all resources before thread stops.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def handle(self) -> None:
        """
        Method that should contain business logic of the thread.
        Will be executed in the loop until stop() method is called.
        Must not block for a long time.
        :return: None
        """
        raise NotImplementedError()

    def run(self) -> None:
        """
        This method will be executed in a separate thread
        when start() method is called.
        :return: None
        """
        try:
            self.startup()
            while not self._stopped():
                try:
                    self.handle()
                except Exception as e:
                    self.logger.info(f'Exception in thread: {e}')
        except Exception as e:
            self.logger.info(f'Failed to startup: {e}')
        finally:
            self.shutdown()
