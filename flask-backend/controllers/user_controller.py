from flask import jsonify
from bson import ObjectId

from db import users_collection


def get_current_user():
    try:
        user_id = request.user_id

        # Convert string ID to MongoDB ObjectId
        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            return jsonify({
                "message": "Invalid user ID"
            }), 400

        # Find user
        user = users_collection.find_one({
            "_id": user_object_id
        })

        if not user:
            return jsonify({
                "message": "user does not found"
            }), 404

        # ObjectId is not directly JSON serializable
        user["_id"] = str(user["_id"])

        if user.get("createdAt"):
            user["createdAt"] = user["createdAt"].isoformat()

        if user.get("updatedAt"):
            user["updatedAt"] = user["updatedAt"].isoformat()

        return jsonify(user), 200

    except Exception as error:

        print("Get Current User Error:", error)

        return jsonify({
            "message": f"failed to get currentUser {error}"
        }), 500