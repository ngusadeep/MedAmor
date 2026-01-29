"""Flask application factory and configuration."""

from flask import Flask, jsonify
from flask_cors import CORS

from .config import get_database_url, load_config
from .database import db, init_db


def create_app(config_override: dict = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    config = load_config()
    if config_override:
        for key, value in config_override.items():
            if isinstance(value, dict) and key in config:
                config[key].update(value)
            else:
                config[key] = value

    # Configure Flask
    app.config["SECRET_KEY"] = config["server"]["secret_key"]
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url(config)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    CORS(app)
    init_db(app)

    # Register blueprints
    from .routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    # Health check endpoint
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"})

    return app


# Application instance for gunicorn
app = create_app()

if __name__ == "__main__":
    config = load_config()
    app.run(
        host=config["server"]["host"],
        port=config["server"]["port"],
        debug=config["server"]["debug"],
    )
