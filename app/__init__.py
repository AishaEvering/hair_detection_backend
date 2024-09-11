import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from ultralytics import YOLO
from app.utils.background_thread_factory import BackgroundThreadFactory
from .logging_config import setup_logging


load_dotenv()


def create_app():
    origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5000",
        "https://www.aishaeportfolio.com"
    ]

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    CORS(app, origins=origins)

    # Set up logging
    logger = setup_logging()
    logger.info('Flask application is starting up...')

    app.config['EXAMPLE_IMG_DIR'] = './app/static/image-examples'
    app.config['EXAMPLE_VIDEO_DIR'] = './app/static/video-examples'
    app.config['CLASS_NAMES'] = ["afro", "bantu knots", "bob", "braids",
                                 "cornrows", "fade", "locs", "long", "sisterlocs", "twa"]

    app.config['YOLO_MODEL'] = YOLO(
        './app/models/best_quantized.onnx', task="detect")

    temp_dir = './app/tmp'
    app.config['TEMP_DIR'] = temp_dir

    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
    except Exception as e:
        logger.error(f"Failed to create temp directory: {str(e)}")

    with app.app_context():
        # Import routes
        from . import routes
        app.register_blueprint(routes.bp)

        backgroundThreadFactory = BackgroundThreadFactory(app)
        app.config['BACKGROUND_THREAD_FACTORY'] = backgroundThreadFactory

        # Start background tasks
        try:
            backgroundThreadFactory.create('cleanup').start()
        except Exception as e:
            logger.error(f"Failed to start cleanup thread: {str(e)}")

    return app
