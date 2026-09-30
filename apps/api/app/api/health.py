from flask import jsonify

from app.api import api_v1

@api_v1.get("/health")
def health_check():
    """Return a simple response that confirms the API is running"""

    return jsonify(
        {
            "status": "ok",
            "service": "shipyard-api",
        }
    ), 200