from flask import Blueprint
from middleware.is_auth import is_auth
from middleware.upload import upload_file

from controllers.interview_controller import (
    analyze_resume,
    generate_question,
    submit_answer,
    finish_interview,
    get_my_interviews,
    get_interview_report
)

interview_routes = Blueprint("interview_routes", __name__)


@interview_routes.route("/resume", methods=["POST"])
@is_auth
@upload_file
def resume():
    return analyze_resume()


@interview_routes.route("/generate-questions", methods=["POST"])
@is_auth
def generate_questions():
    return generate_question()


@interview_routes.route("/submit-answer", methods=["POST"])
@is_auth
def submit_answer_route():
    return submit_answer()


@interview_routes.route("/finish", methods=["POST"])
@is_auth
def finish():
    return finish_interview()


@interview_routes.route("/get-interview", methods=["GET"])
@is_auth
def get_interviews():
    return get_my_interviews()


@interview_routes.route("/report/<id>", methods=["GET"])
@is_auth
def report(id):
    return get_interview_report(id)