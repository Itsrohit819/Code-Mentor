from flask import Blueprint, render_template, request, jsonify

main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@main.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    code = data.get("code", "")
    error = data.get("error", "")

    # Dummy suggestion (to be replaced later)
    return jsonify({
        "concept": "Dynamic Programming (placeholder)",
        "suggestion": "Try checking your base case and memoization."
    })
