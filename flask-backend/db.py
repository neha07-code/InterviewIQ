import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Get MongoDB URL from .env
MONGODB_URL = os.getenv("MONGODB_URL")

if not MONGODB_URL:
    raise ValueError("MONGODB_URL is not set in .env")

try:
    # Connect to MongoDB
    client = MongoClient(MONGODB_URL)

    # Test connection
    client.admin.command("ping")

    print("MongoDB connected successfully")

    # Database
    db = client["evalai"]

    # Collections
    users_collection = db["users"]
    interviews_collection = db["interviews"]
    payments_collection = db["payments"]

except Exception as e:
    print("MongoDB connection failed:", e)
    raise