"""Flask app for MedAudit Backend - POST /audit endpoint."""

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request

from aiorchestrator.app.agent import build_audit_graph

app = Flask(__name__)

# Lazy-init graph so it's built once
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_audit_graph()
    return _graph


@app.route("/audit", methods=["POST"])
def audit():
    """Run medical audit for a patient. Payload: {patient_id, audit_type}."""
    data = request.get_json() or {}
    patient_id = data.get("patient_id") or ""
    audit_type = data.get("audit_type") or "general"

    if not patient_id:
        return jsonify({"status": "error", "message": "patient_id is required"}), 400

    try:
        graph = get_graph()
        result = graph.invoke({
            "patient_id": patient_id.strip(),
            "audit_type": audit_type.strip(),
        })
        return jsonify({
            "status": "success",
            "report": result.get("report", ""),
            "sources": result.get("context") or [],
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def main():
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
