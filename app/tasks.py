import os
import time
import logging
from threading import Timer
from flask import current_app

logger = logging.getLogger(__name__)


def clean_old_files(directory, age_in_seconds):
    now = time.time()
    for file_path in os.listdir(directory):
        full_path = os.path.join(directory, file_path)
        if os.path.getmtime(full_path) < now - age_in_seconds:
            os.remove(full_path)


def schedule_cleanup():
    # clean up runs every hour
    Timer(3600, schedule_cleanup).start()

    temp_dir = current_app.config['TEMP_DIR']

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    clean_old_files(temp_dir, 3600)


def start_cleanup_task():
    logger.info('Starting cleanup task scheduler...')
    schedule_cleanup()
