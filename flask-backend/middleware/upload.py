from flask import request, jsonify
from functools import wraps
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "public"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def upload_file(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        file = request.files.get("resume")

        if not file:
            return jsonify({
                "message": "No file uploaded"
            }), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                "message": "File size must be less than 5 MB"
            }), 400

        # Create filename similar to Date.now() + originalname
        filename = f"{int(__import__('time').time() * 1000)}-{secure_filename(file.filename)}"

        file_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(file_path)

        # Make filename/path available to controller
        request.uploaded_file = file_path
        request.uploaded_filename = filename

        return func(*args, **kwargs)

    return wrapper