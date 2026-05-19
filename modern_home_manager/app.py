from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Flask, abort, jsonify, render_template, request


app = Flask(__name__)

LAST_LOCATION: dict[str, Any] = {
    "user": "관리자 (나)",
    "place": "집",
    "time": datetime.now().strftime("%H:%M"),
    "updated": "10:24:05",
    "source": "sample",
    "accuracy": None,
    "latitude": None,
    "longitude": None,
    "note": "브라우저 위치 권한을 허용하면 GPS/WiFi/기지국 기반 좌표를 받을 수 있습니다.",
}


ROOMS: dict[str, dict[str, Any]] = {
    "living": {
        "id": "living",
        "name": "거실",
        "status": "정상",
        "image": "images/living-room-photo.png",
        "temperature": 23.4,
        "humidity": 45,
        "light": 386,
        "devices_on": 6,
        "spark": [22, 28, 24, 31, 26, 36, 25, 33, 30],
    },
    "bedroom": {
        "id": "bedroom",
        "name": "침실",
        "status": "정상",
        "image": "images/bedroom-photo.png",
        "temperature": 21.2,
        "humidity": 50,
        "light": 120,
        "devices_on": 3,
        "spark": [18, 22, 20, 24, 23, 21, 26, 25, 24],
    },
    "kitchen": {
        "id": "kitchen",
        "name": "주방",
        "status": "정상",
        "image": "images/kitchen-photo.png",
        "temperature": 24.1,
        "humidity": 47,
        "light": 320,
        "devices_on": 4,
        "spark": [25, 23, 30, 27, 34, 31, 28, 35, 32],
    },
}

SENSORS: list[dict[str, Any]] = [
    {"id": "temp-living", "icon": "thermometer", "label": "온도 (거실)", "value": "23.4°C", "room": "living", "time": "10:24:10"},
    {"id": "humidity-living", "icon": "drop", "label": "습도 (거실)", "value": "45%", "room": "living", "time": "10:24:10"},
    {"id": "dust-living", "icon": "sun", "label": "미세먼지 (거실)", "value": "12 µg/m³", "room": "living", "time": "10:24:09"},
    {"id": "light-living", "icon": "sun", "label": "조도 (거실)", "value": "386 lux", "room": "living", "time": "10:24:08"},
    {"id": "co2-living", "icon": "co2", "label": "CO₂ (거실)", "value": "540 ppm", "room": "living", "time": "10:24:08"},
]

ACTUATORS: dict[str, dict[str, Any]] = {
    "living-light": {"id": "living-light", "room": "living", "icon": "light", "name": "거실 조명", "detail": "켜짐", "active": True},
    "living-ac": {"id": "living-ac", "room": "living", "icon": "ac", "name": "거실 에어컨", "detail": "냉방 24°C", "active": True},
    "living-curtain": {"id": "living-curtain", "room": "living", "icon": "curtain", "name": "거실 커튼", "detail": "열림 60%", "active": True},
    "bedroom-light": {"id": "bedroom-light", "room": "bedroom", "icon": "light", "name": "침실 조명", "detail": "취침등", "active": True},
    "bedroom-ac": {"id": "bedroom-ac", "room": "bedroom", "icon": "ac", "name": "침실 에어컨", "detail": "수면 26°C", "active": True},
    "kitchen-fan": {"id": "kitchen-fan", "room": "kitchen", "icon": "fan", "name": "환기 팬 (주방)", "detail": "중간", "active": True},
    "kitchen-plug": {"id": "kitchen-plug", "room": "kitchen", "icon": "plug", "name": "주방 콘센트", "detail": "꺼짐", "active": False},
}

RESERVATIONS: list[dict[str, Any]] = [
    {"time": "22:00", "title": "거실 조명 끄기", "repeat": "매일", "status": "활성"},
    {"time": "07:00", "title": "거실 커튼 열기", "repeat": "매일", "status": "활성"},
    {"time": "18:30", "title": "에어컨 켜기 (24°C)", "repeat": "주중 (월-금)", "status": "활성"},
]

LOGS: list[dict[str, Any]] = [
    {"time": "10:24:10", "icon": "temp", "message": "거실 온도 센서 업데이트", "value": "23.4°C"},
    {"time": "10:24:08", "icon": "ac", "message": "거실 에어컨 설정 변경", "value": "24°C (냉방)"},
    {"time": "10:24:05", "icon": "light", "message": "거실 조명 켜짐", "value": "수동"},
    {"time": "10:23:58", "icon": "curtain", "message": "침실 창문 센서 닫힘 → 열림", "value": "정상"},
    {"time": "10:23:45", "icon": "user", "message": "사용자 관리자 로그인", "value": "웹"},
]


def build_dashboard_payload() -> dict[str, Any]:
    rooms = list(ROOMS.values())
    active_count = sum(1 for item in ACTUATORS.values() if item["active"])
    avg_temp = round(sum(room["temperature"] for room in rooms) / len(rooms), 1)
    avg_humidity = round(sum(room["humidity"] for room in rooms) / len(rooms))

    return {
        "status": {
            "connection": "실시간 연결됨",
            "security": "해제",
            "averageTemperature": f"{avg_temp}°C",
            "averageHumidity": f"{avg_humidity}%",
            "currentTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "gateway": "192.168.1.10",
            "firmware": "v1.2.3",
            "activeDevices": active_count,
        },
        "sensors": SENSORS,
        "temperatures": [
            {"room": "거실", "value": ROOMS["living"]["temperature"], "color": "teal"},
            {"room": "침실", "value": ROOMS["bedroom"]["temperature"], "color": "coral"},
            {"room": "주방", "value": ROOMS["kitchen"]["temperature"], "color": "teal"},
            {"room": "욕실", "value": 20.3, "color": "lime"},
        ],
        "actuators": list(ACTUATORS.values()),
        "reservations": RESERVATIONS,
        "location": LAST_LOCATION,
        "logs": LOGS,
        "rooms": rooms,
    }


@app.get("/")
def dashboard() -> str:
    return render_template("dashboard.html")


@app.get("/api/dashboard")
def dashboard_api():
    return jsonify(build_dashboard_payload())


@app.get("/api/rooms/<room_id>")
def room_api(room_id: str):
    room = ROOMS.get(room_id)
    if room is None:
        abort(404, description=f"Unknown room: {room_id}")

    return jsonify(
        {
            "room": room,
            "actuators": [item for item in ACTUATORS.values() if item["room"] == room_id],
            "sensors": [item for item in SENSORS if item["room"] == room_id],
        }
    )


@app.post("/api/location")
def update_location_api():
    payload = request.get_json(silent=True) or {}
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    accuracy = payload.get("accuracy")

    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        abort(400, description="latitude and longitude are required numbers")

    LAST_LOCATION.update(
        {
            "place": "브라우저 위치 확인됨",
            "time": datetime.now().strftime("%H:%M"),
            "updated": datetime.now().strftime("%H:%M:%S"),
            "source": "browser_geolocation",
            "accuracy": round(float(accuracy), 1) if isinstance(accuracy, (int, float)) else None,
            "latitude": round(float(latitude), 6),
            "longitude": round(float(longitude), 6),
            "note": "이 좌표는 브라우저 위치 권한 기반입니다. WiFi SSID/BSSID는 브라우저에서 직접 읽을 수 없습니다.",
        }
    )
    return jsonify(LAST_LOCATION)


@app.post("/api/actuators/<actuator_id>/toggle")
def toggle_actuator_api(actuator_id: str):
    actuator = ACTUATORS.get(actuator_id)
    if actuator is None:
        abort(404, description=f"Unknown actuator: {actuator_id}")

    payload = request.get_json(silent=True) or {}
    if "active" in payload and not isinstance(payload["active"], bool):
        abort(400, description="active must be a boolean")

    actuator["active"] = payload.get("active", not actuator["active"])
    actuator["detail"] = "켜짐" if actuator["active"] else "꺼짐"
    return jsonify(actuator)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5173, debug=False)
