from datetime import datetime


def create_user(name, email):
    if not name:
        raise ValueError("Name is required")

    if not email:
        raise ValueError("Email is required")

    return {
        "name": name,
        "email": email,
        "credits": 200,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }