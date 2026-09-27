import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def gen_token(user_id):

    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }

    token = jwt.encode(
        payload,
        os.getenv("JWT_SECRET"),
        algorithm="HS256"
    )

    return token