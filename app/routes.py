import os
import queue
from tempfile import NamedTemporaryFile
from PIL import Image
import logging
from dotenv import load_dotenv
from flask import current_app, Blueprint, request, send_file, jsonify, Response
from .utils.detector import img_detector

load_dotenv()

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

MAX_WAIT_TIME = 10


@bp.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@bp.errorhandler(405)
def resource_not_found(e):
    return jsonify(error=str(e)), 405


@bp.errorhandler(401)
def custom_401(error):
    return Response("API Key required.", 401)


@bp.route("/ping")
def hello_world():
    return "<h1 style='color:green'>Hello World! Are we live?</h1>"


@bp.route("/api/process_image", methods=['POST'])
def process_image():

    if 'image' not in request.files:
        return "No file part in the request.", 400

    file = request.files['image']

    if file.filename == '' or not file.filename.lower().split(".")[-1] in ("jpg", "jpeg", "png", "webp"):
        return "Unsupported file format. Only JPG, JPEG, PNG, WEBP are supported.", 415

    try:
        img_io = img_detector(file.read())
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return "Error processing image", 500


@bp.route("/api/process_example_image", methods=['GET', 'POST'])
def process_example_image():

    file_id = request.args.get('file_id')

    if not file_id:
        return jsonify({'error': 'No file_id provided'}), 400

    file_path = os.path.join(current_app.config['EXAMPLE_IMG_DIR'], file_id)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        image = Image.open(file_path)
        img_io = img_detector(image, as_bytes=False)
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return "Error processing image", 500


@bp.route('/api/process_frame', methods=['POST'])
def process_frame():
    if 'frame' not in request.files:
        return jsonify({"error": "No frame file provided"}), 400

    try:
        frame_file = request.files['frame']
        img_io = img_detector(frame_file.read(), stream=True)

        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False
        )
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        return "Error processing frame", 500


def save_to_temp(file) -> str:
    temp = NamedTemporaryFile(
        delete=False, suffix=".mp4", dir=current_app.config['TEMP_DIR'])

    try:
        contents = file.read()
        with temp as f:
            temp_file_name = f.name
            f.write(contents)
            f.flush()
            os.fsync(f.fileno())
        return temp_file_name
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise Exception("Error uploading the file.")
    finally:
        file.close()


@bp.route('/api/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video part in the request."}), 400

    file = request.files['video']

    if file.filename == '' or not file.content_type == 'video/mp4':
        return jsonify({"error": "File is not an MP4 video"}), 400

    if file:
        try:
            tempFilePath = save_to_temp(file)

            if tempFilePath is None or not os.path.exists(tempFilePath):
                logger.error(f"Temporary file not found after writing.")
                return jsonify({"error": "Temporary file not found after writing."}), 500

            file_id = os.path.basename(tempFilePath)

            backgroundThreadFactory = current_app.config['BACKGROUND_THREAD_FACTORY']
            thread = backgroundThreadFactory.create(
                thread_type="process_frames", file_path=tempFilePath, file_id=file_id)
            thread.start()

            return jsonify({'id': str(thread.thread_id)})
        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            return jsonify({"error": "Error uploading video"}), 500


def generate_frames(thread, backgroundThreadFactory):
    frame_queue = thread.get_frame_queue()

    while True:
        try:
            frame_data = frame_queue.get(timeout=2)

            if frame_data == "DONE":
                backgroundThreadFactory.delete(thread.thread_id)
                break
            else:
                yield frame_data
        except queue.Empty:
            print("No frame retrieved within the timeout period.")
            continue


@bp.route('/api/stream_frames', methods=['GET'])
def stream_input_frames():
    thread_id = request.args.get('id')

    if not thread_id:
        return jsonify({'error': 'No id provided'}), 400

    try:
        backgroundThreadFactory = current_app.config['BACKGROUND_THREAD_FACTORY']
        thread = backgroundThreadFactory.get_thread(thread_id)

        if thread is None:
            return jsonify({'error': 'Thread not found'}), 404

        file_path = thread.file_path

        delect_src = False if thread.file_id.startswith('hair') else True

        return Response(generate_frames(thread, backgroundThreadFactory), mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(file_path) and delect_src:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Failed to delete source video file: {e}")


@bp.route('/api/process_video_example', methods=['GET'])
def process_video_example():
    file_id = request.args.get('id')

    if not file_id:
        return jsonify({'error': 'No file_id provided'}), 400

    file_path = os.path.join(current_app.config['EXAMPLE_VIDEO_DIR'], file_id)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        backgroundThreadFactory = current_app.config['BACKGROUND_THREAD_FACTORY']
        thread = backgroundThreadFactory.create(
            thread_type="process_frames", file_path=file_path, file_id=file_id)
        thread.start()

        return jsonify({'id': str(thread.thread_id)})
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        return jsonify({"error": "Error uploading video"}), 500


@bp.route('/api/got_frames', methods=['GET'])
def got_frames():
    thread_id = request.args.get('id')

    if not thread_id:
        return jsonify({'error': 'No id provided'}), 400

    got_frames = False

    try:
        backgroundThreadFactory = current_app.config['BACKGROUND_THREAD_FACTORY']
        thread = backgroundThreadFactory.get_thread(thread_id)

        if thread:
            # Return whether frames exist in the queue
            frame_queue = thread.get_frame_queue()
            got_frames = frame_queue.qsize() > 0

        else:
            return jsonify({'error': 'Thread not found'}), 404

        return jsonify({'got_frames': got_frames})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/stream_frames_progress', methods=['GET'])
def get_progress():
    id = request.args.get('id')

    if not id:
        return jsonify({'error': 'No id provided'}), 400

    try:
        backgroundThreadFactory = current_app.config['BACKGROUND_THREAD_FACTORY']
        thread = backgroundThreadFactory.get_thread(id)

        if thread:
            return jsonify({'progress': thread.progress}), 200

        return jsonify({'progress': 0}), 200
    except Exception as e:
        return jsonify({'progress': 0}), 200
        # logger.error(f"Error fetching progress: {str(e)}")
        # return jsonify({'error': 'Internal Server Error'}), 500
