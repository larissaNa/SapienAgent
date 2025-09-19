# app/routes.py
from flask import Blueprint, render_template, request, jsonify
from app.core.services import run

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
