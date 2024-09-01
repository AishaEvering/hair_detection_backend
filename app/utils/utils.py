import logging
from flask import current_app
from ultralytics import YOLO
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile

load_dotenv()

logger = logging.getLogger(__name__)


def get_class_names():
    return ["afro", "bantu knots", "bob", "braids",
            "cornrows", "fade", "locs", "long", "sisterlocs", "twa"]


def load_model():
    model_path: str = current_app.config["YOLO_PATH"]
    # Load a model
    return YOLO(model_path, task="detect")


def save_to_temp(file) -> str:
    temp = NamedTemporaryFile(
        delete=False, suffix=".mp4", dir=current_app.config['TEMP_DIR'])

    try:
        contents = file.read()
        with temp as f:
            f.write(contents)  # saving input to temp file
            return temp.name
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise Exception("Error uploading the file.")
    finally:
        file.close()
