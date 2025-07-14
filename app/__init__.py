from flask import Flask
from .database import init_db

def create_app():
    app = Flask(__name__)
    app.secret_key = "dev_key"

    init_db()  # Initialize DB on app start

    from .routes import main
    app.register_blueprint(main)

    return app
