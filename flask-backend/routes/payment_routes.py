from flask import Blueprint

from middleware.is_auth import is_auth
from controllers.payment_controller import create_order, verify_payment


payment_routes = Blueprint("payment_routes", __name__)


@payment_routes.route("/order", methods=["POST"])
@is_auth
def order():
    return create_order()


@payment_routes.route("/verify", methods=["POST"])
@is_auth
def verify():
    return verify_payment()