"""API routes for the platform."""

from flask import Blueprint, jsonify, request

from .database import db
from .models import User

api_bp = Blueprint("api", __name__)


@api_bp.route("/users", methods=["GET"])
def get_users():
    """Get all users."""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@api_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """Get a specific user by ID."""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@api_bp.route("/users", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["username", "email", "password"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Check for existing user
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 409
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 409

    user = User(
        username=data["username"],
        email=data["email"],
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        is_admin=data.get("is_admin", False),
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@api_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    """Update a user."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "username" in data and data["username"] != user.username:
        if User.query.filter_by(username=data["username"]).first():
            return jsonify({"error": "Username already exists"}), 409
        user.username = data["username"]

    if "email" in data and data["email"] != user.email:
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409
        user.email = data["email"]

    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "is_admin" in data:
        user.is_admin = data["is_admin"]
    if "password" in data:
        user.set_password(data["password"])

    db.session.commit()

    return jsonify(user.to_dict())


@api_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return "", 204
