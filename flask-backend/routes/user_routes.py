from flask import Blueprint

from middleware.is_auth import is_auth
from controllers.user_controller import get_current_user


user_routes = Blueprint("user_routes", __name__)


@user_routes.route("/current-user", methods=["GET"])
@is_auth
def current_user():
    return get_current_user()