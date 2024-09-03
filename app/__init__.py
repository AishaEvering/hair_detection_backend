import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from .logging_config import setup_logging
from .tasks import start_cleanup_task

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

    app.config['YOLO_PATH'] = './app/models/best_quantized.onnx'
    app.config['TEMP_DIR'] = './app/tmp'
    app.config['EXAMPLE_IMG_DIR'] = './app/static/image-examples'
    app.config['EXAMPLE_VIDEO_DIR'] = './app/static/video-examples'

    with app.app_context():
        # Import routes
        from . import routes
        app.register_blueprint(routes.bp)

        # Start background tasks
        start_cleanup_task()

    return app
