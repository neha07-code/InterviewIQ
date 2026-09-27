from flask import request, jsonify, make_response
from bson import ObjectId

from db import users_collection
from models.user_model import create_user
from config.token import gen_token


def google_auth():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")

        if not name or not email:
            return jsonify({
                "message": "Name and email are required"
            }), 400

        # Find existing user
        user = users_collection.find_one({
            "email": email
        })

        # Create new user if not found
        if not user:
            user_data = create_user(
                name=name,
                email=email
            )

            result = users_collection.insert_one(user_data)

            user = users_collection.find_one({
                "_id": result.inserted_id
            })

        # Generate JWT token
        token = gen_token(str(user["_id"]))

        # Convert MongoDB ObjectId to string before JSON response
        user_response = {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "credits": user.get("credits", 200)
        }

        # Create response
        response = make_response(
            jsonify(user_response),
            200
        )

        # Set token cookie
        response.set_cookie(
            "token",
            token,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
            max_age=7 * 24 * 60 * 60
        )

        return response

    except Exception as error:
        print("Google auth error:", error)

        return jsonify({
            "message": f"Google auth error {error}"
        }), 500


def logout():
    try:
        response = make_response(
            jsonify({
                "message": "Logout successfully"
            }),
            200
        )

        # Clear token cookie
        response.set_cookie(
            "token",
            "",
            expires=0,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/"
        )

        return response

    except Exception as error:
        return jsonify({
            "message": f"Logout error {error}"
        }), 500