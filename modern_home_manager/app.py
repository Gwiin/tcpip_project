from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request

try:
    from modern_home_manager.database import (
        DEFAULT_DB_PATH,
        build_dashboard_payload,
        initialize_database,
        room_payload,
        set_actuator_active,
        update_location,
    )
except ModuleNotFoundError:
    from database import (  # type: ignore[no-redef]
        DEFAULT_DB_PATH,
        build_dashboard_payload,
        initialize_database,
        room_payload,
        set_actuator_active,
        update_location,
    )


def create_app(db_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    database_path = Path(db_path or os.environ.get("MODERN_HOME_DB", DEFAULT_DB_PATH))
    initialize_database(database_path)
    app.config["DATABASE_PATH"] = database_path

    @app.get("/")
    def dashboard() -> str:
        return render_template("dashboard.html")

    @app.get("/api/dashboard")
    def dashboard_api():
        return jsonify(build_dashboard_payload(app.config["DATABASE_PATH"]))

    @app.get("/api/rooms/<room_id>")
    def room_api(room_id: str):
        payload = room_payload(app.config["DATABASE_PATH"], room_id)
        if payload is None:
            abort(404, description=f"Unknown room: {room_id}")
        return jsonify(payload)

    @app.post("/api/location")
    def update_location_api():
        payload = request.get_json(silent=True) or {}
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")
        accuracy = payload.get("accuracy")

        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            abort(400, description="latitude and longitude are required numbers")
        if accuracy is not None and not isinstance(accuracy, (int, float)):
            abort(400, description="accuracy must be a number when provided")

        return jsonify(
            update_location(
                app.config["DATABASE_PATH"],
                latitude=float(latitude),
                longitude=float(longitude),
                accuracy=float(accuracy) if accuracy is not None else None,
            )
        )

    @app.post("/api/actuators/<actuator_id>/toggle")
    def toggle_actuator_api(actuator_id: str):
        payload = request.get_json(silent=True) or {}
        if "active" in payload and not isinstance(payload["active"], bool):
            abort(400, description="active must be a boolean")

        dashboard_payload = build_dashboard_payload(app.config["DATABASE_PATH"])
        actuator = next(
            (item for item in dashboard_payload["actuators"] if item["id"] == actuator_id),
            None,
        )
        if actuator is None:
            abort(404, description=f"Unknown actuator: {actuator_id}")

        active = payload.get("active", not actuator["active"])
        return jsonify(set_actuator_active(app.config["DATABASE_PATH"], actuator_id, active))

    @app.post("/api/reset")
    def reset_database_api():
        database_path.unlink(missing_ok=True)
        initialize_database(database_path)
        return jsonify({"success": True, "message": "database reset"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5173, debug=False)
