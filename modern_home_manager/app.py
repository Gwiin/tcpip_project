from __future__ import annotations

import os
import secrets

from flask import Flask, abort, jsonify, render_template, request, session

try:
    from modern_home_manager.database import (
        DatabaseUnavailable,
        authenticate_user,
        build_dashboard_payload,
        create_user_account,
        initialize_database,
        record_device_frame,
        room_payload,
        set_actuator_active,
        update_location,
    )
except ModuleNotFoundError:
    from database import (  # type: ignore[no-redef]
        DatabaseUnavailable,
        authenticate_user,
        build_dashboard_payload,
        create_user_account,
        initialize_database,
        record_device_frame,
        room_payload,
        set_actuator_active,
        update_location,
    )


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("MODERN_HOME_SECRET_KEY", secrets.token_hex(32))

    def session_payload() -> dict[str, object]:
        logged_in = "user_id" in session
        return {
            "loggedIn": logged_in,
            "userId": session.get("user_id") if logged_in else None,
            "user": session.get("user_name") if logged_in else None,
            "role": session.get("role", "GUEST") if logged_in else "GUEST",
        }

    def require_login() -> None:
        if "user_id" not in session:
            abort(401, description="login required")

    def set_session_user(user: dict[str, object]) -> None:
        session.clear()
        session["user_id"] = user["user_id"]
        session["user_name"] = user["user_name"]
        session["role"] = user.get("role", "MEMBER")

    @app.get("/")
    def dashboard() -> str:
        return render_template("dashboard.html")

    @app.errorhandler(DatabaseUnavailable)
    def database_unavailable(error):
        return jsonify({"success": False, "message": str(error)}), 503

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"success": False, "message": getattr(error, "description", "login required")}), 401

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "message": getattr(error, "description", "bad request")}), 400

    @app.get("/api/session")
    def session_api():
        return jsonify(session_payload())

    @app.post("/api/session/login")
    def login_api():
        payload = request.get_json(silent=True) or {}
        username = payload.get("name") or payload.get("username")
        password = payload.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            abort(400, description="사용자명과 비밀번호를 입력해주세요.")

        user = authenticate_user(username.strip(), password)
        if user is None:
            abort(401, description="사용자명 또는 비밀번호가 올바르지 않습니다.")

        set_session_user(user)
        return jsonify({"success": True, "message": "로그인 성공", **session_payload()})

    @app.post("/api/session/register")
    def register_api():
        payload = request.get_json(silent=True) or {}
        username = payload.get("name") or payload.get("username")
        password = payload.get("password")

        if not isinstance(username, str) or not isinstance(password, str) or not username.strip() or not password:
            abort(400, description="사용자명과 비밀번호를 입력해주세요.")

        try:
            user = create_user_account(username.strip(), password)
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 409

        set_session_user(user)
        return jsonify({"success": True, "message": "회원가입이 완료되었습니다.", **session_payload()}), 201

    @app.post("/api/session/logout")
    def logout_api():
        session.clear()
        return jsonify({"success": True, **session_payload()})

    @app.get("/api/dashboard")
    def dashboard_api():
        return jsonify(build_dashboard_payload())

    @app.get("/api/rooms/<room_id>")
    def room_api(room_id: str):
        payload = room_payload(room_id)
        if payload is None:
            abort(404, description=f"Unknown room: {room_id}")
        return jsonify(payload)

    @app.post("/api/location")
    def update_location_api():
        require_login()
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
                latitude=float(latitude),
                longitude=float(longitude),
                accuracy=float(accuracy) if accuracy is not None else None,
            )
        )

    @app.post("/api/actuators/<actuator_id>/toggle")
    def toggle_actuator_api(actuator_id: str):
        require_login()
        payload = request.get_json(silent=True) or {}
        if "active" in payload and not isinstance(payload["active"], bool):
            abort(400, description="active must be a boolean")

        dashboard_payload = build_dashboard_payload()
        actuator = next(
            (item for item in dashboard_payload["actuators"] if item["id"] == actuator_id),
            None,
        )
        if actuator is None:
            abort(404, description=f"Unknown actuator: {actuator_id}")

        active = payload.get("active", not actuator["active"])
        return jsonify(set_actuator_active(actuator_id, active))

    @app.post("/api/pico/ingest")
    def pico_ingest_api():
        payload = request.get_json(silent=True) or {}
        try:
            record_device_frame(payload)
        except ValueError as exc:
            abort(400, description=str(exc))
        return jsonify({"success": True, "message": "pico frame saved"})

    @app.get("/api/health")
    def health_api():
        initialize_database()
        return jsonify({"success": True, "database": "mysql"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5173, debug=False)
