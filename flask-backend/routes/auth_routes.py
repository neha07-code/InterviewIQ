from flask import Blueprint
from controllers.auth_controller import google_auth, logout

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.route("/google", methods=["POST"])
def google():
    return google_auth()


@auth_routes.route("/logout", methods=["GET"])
def logout_user():
    return logout()