from flask import Blueprint, render_template, request, jsonify
from .database import log_submission
main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@main.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    code = data.get("code", "")
    error = data.get("error", "")

    # Placeholder logic for now
    concept = "Dynamic Programming (placeholder)"
    suggestion = "Try checking your base case and memoization."

    # Save to DB
    log_submission(code, error, concept, suggestion)

    return jsonify({
        "concept": concept,
        "suggestion": suggestion
    })
