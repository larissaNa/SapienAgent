# app/routes.py
from flask import Blueprint, render_template, request, jsonify
from app.core.services import run
from app.core.shared_state import get_scheduler_results, clear_scheduler_results

routes_bp = Blueprint("routes_bp", __name__)  # nome e import_name

@routes_bp.route("/")
def home():
    return render_template("index.html")

@routes_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message")
    if not user_input:
        return jsonify({"error": "mensagem ausente"}), 400
    result = run(user_input)
    return jsonify({"responses": result})


@routes_bp.route("/scheduler/results", methods=["GET"]) 
def scheduler_results():
    results = get_scheduler_results()
    if results:
        clear_scheduler_results()
    return jsonify({"results": results})
