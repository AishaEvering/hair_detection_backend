import cv2
import os
import io
import time
from flask import current_app
import numpy as np
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from ultralytics.utils.plotting import Annotator
import logging
import threading

logger = logging.getLogger(__name__)

load_dotenv()


def img_detector(img, stream: bool = False, as_bytes: bool = True):

    if as_bytes:
        image = Image.open(BytesIO(img))
    else:
        image = img

    width = image.width
    height = image.height

    image = np.array(image)

    image = __process_img(image, stream=stream)
    image = cv2.resize(image, (width, height))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    _, img_encoded = cv2.imencode('.jpg', image)

    return io.BytesIO(img_encoded.tobytes())


def add_video_detections(videoPath, file_id):
    try:
        cap = cv2.VideoCapture(videoPath)

        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {videoPath}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            raise ValueError(f"Video file {videoPath} has no frames.")

        frame_count = 0
        boundary = 'frame'

        while True:
            success, frame = cap.read()

            if success:
                frame_count += 1

                progress = int(
                    (frame_count / total_frames) * 100)

                processed_frame = __process_img(frame, stream=True)
                processed_frame = cv2.resize(
                    processed_frame, (width, height))

                # convert processed frame to JPEG
                _, buffer = cv2.imencode('.jpg', processed_frame)
                frame_bytes = buffer.tobytes()

                data = b'--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n%s\r\n' % (
                    boundary.encode(), len(frame_bytes), frame_bytes)
                yield data, progress
            else:
                break

        # Ensure the progress reaches 100% after the loop
        if frame_count >= total_frames:
            progress = 100

        data = b'--%s--\r\n' % boundary.encode()

        yield data, progress

    except Exception as e:
        logger.error(f"An error occurred during video processing: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()


def __process_img(img, stream: bool = False):

    test_image = cv2.resize(img, (640, 640))

    model = current_app.config['YOLO_MODEL']
    results = model([test_image], stream=stream)

    for r in results:
        annotator = Annotator(test_image)
        boxes = r.boxes

        for box in boxes:
            box_coords = box.xyxy[0]
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            class_names = current_app.config['CLASS_NAMES']
            label = f'{class_names[cls]} {conf:.2f}'
            annotator.box_label(box_coords, label, color=(232, 21, 21))

    return annotator.result()
