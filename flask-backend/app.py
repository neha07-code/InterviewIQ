from flask import Flask
from flask_cors import CORS

from routes.auth_routes import auth_routes
from routes.interview_routes import interview_routes
from routes.payment_routes import payment_routes
from routes.user_routes import user_routes

app = Flask(__name__)

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173"
    ]
)

app.register_blueprint(
    auth_routes,
    url_prefix="/api/auth"
)

app.register_blueprint(
    interview_routes,
    url_prefix="/api/interview"
)

app.register_blueprint(
    payment_routes,
    url_prefix="/api/payment"
)

app.register_blueprint(
    user_routes,
    url_prefix="/api/user"
)


@app.route("/")
def home():
    return "Flask backend is running"


if __name__ == "__main__":
    app.run(debug=True)