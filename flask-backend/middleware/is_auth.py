import os
import jwt

from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()


def is_auth(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        try:
            # Get token from cookie
            token = request.cookies.get("token")

            if not token:
                return jsonify({
                    "message": "No token found"
                }), 401

            # Verify JWT
            decoded = jwt.decode(
                token,
                os.getenv("JWT_SECRET"),
                algorithms=["HS256"]
            )

            # Get user ID from token
            user_id = decoded.get("userId")

            if not user_id:
                return jsonify({
                    "message": "Invalid token"
                }), 401

            # Store user ID for the controller
            request.user_id = user_id

            return func(*args, **kwargs)

        except jwt.ExpiredSignatureError:

            return jsonify({
                "message": "Token expired"
            }), 401

        except jwt.InvalidTokenError:

            return jsonify({
                "message": "Invalid token"
            }), 401

        except Exception as error:

            print("Authentication Error:", error)

            return jsonify({
                "message": "Authentication failed"
            }), 401

    return wrapper