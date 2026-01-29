"""API routes for the platform."""

from flask import Blueprint, jsonify, request

from .database import db
from .models import User, Report

api_bp = Blueprint("api", __name__)


@api_bp.route("/auth/login", methods=["POST"])
def login():
    """Authenticate a user."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    # TODO: Implement session/token management
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
        }
    })


@api_bp.route("/reports", methods=["GET"])
def get_reports():
    """Get all reports."""
    reports = Report.query.order_by(Report.date_of_finding.desc()).all()
    return jsonify([report.to_dict() for report in reports])


@api_bp.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id: int):
    """Get a specific report by ID."""
    report = Report.query.get_or_404(report_id)
    return jsonify(report.to_dict())
