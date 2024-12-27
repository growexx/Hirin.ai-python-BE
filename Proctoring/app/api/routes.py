from flask import Blueprint, jsonify, request
from app.services.faceDetectionServiceFile import FaceDetectionService
from app import auth
from app.utils.config_loader import Config
import threading
import uuid

api_blueprint = Blueprint('api', __name__)

# Load credentials from the configuration
username = Config.get('Auth', 'username')
password = Config.get('Auth', 'password')

users = {username: password}
processing_tasks = {}

@auth.verify_password
def verify_password(username, password):
    return username if users.get(username) == password else None

def process_video_in_thread(video_url, task_id, folder_index, tab_switch_count, exit_full_screen):
    try:
        service = FaceDetectionService(folder_index)
        result = service.process_video(video_url, tab_switch_count, exit_full_screen)
        # Update task status and print the result
        processing_tasks[task_id] = {"status": "completed", "result": result}
        print(f"Task {task_id} completed successfully. Result: {result}")
    except Exception as e:
        # Update task status and print the error
        processing_tasks[task_id] = {"status": "failed", "error": str(e)}
        print(f"Task {task_id} failed. Error: {str(e)}")


@api_blueprint.route('/submit-data', methods=['POST'])
@auth.login_required
def submit_data():
    data = request.json
    if not data:
        return jsonify({'error': "No JSON payload provided"}), 400

    required_keys = ['metadata', 'questions', 'tab_switch_count', 'exit_full_screen']
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return jsonify({"error": f"Missing required fields: {missing_keys}"}), 400

    questions = data.get("questions")
    tab_switch_count = data.get("tab_switch_count")
    exit_full_screen = data.get("exit_full_screen")
    task_ids = []

    for index, question in enumerate(questions, start=1):
        user_video_url = question.get("user_video_url")
        if not user_video_url:
            return jsonify({"error": "user_video_url is required for each question"}), 400

        task_id = str(uuid.uuid4())
        processing_tasks[task_id] = {"status": "processing"}
        thread = threading.Thread(
            target=process_video_in_thread,
            args=(user_video_url, task_id, index, tab_switch_count, exit_full_screen)
        )
        thread.daemon = True
        thread.start()
        task_ids.append(task_id)

    return jsonify({"message": "Processing started", "task_ids": task_ids}), 202

@api_blueprint.route('/task-status/<task_id>', methods=['GET'])
@auth.login_required
def task_status(task_id):
    task_info = processing_tasks.get(task_id)
    if not task_info:
        return jsonify({"error": "Task ID not found"}), 404

    return jsonify(task_info), 200