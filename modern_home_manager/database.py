from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator


DB_ENV_DEFAULTS = {
    "MYSQL_HOST": "127.0.0.1",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "root",
    "MYSQL_PASSWORD": "",
    "MYSQL_DB": "Home_Manager",
}

ROOM_META = {
    1: {"id": "living", "image": "images/living-room-photo.png", "color": "teal"},
    2: {"id": "bedroom", "image": "images/bedroom-photo.png", "color": "coral"},
    3: {"id": "kitchen", "image": "images/kitchen-photo.png", "color": "lime"},
    4: {"id": "study", "image": "images/bedroom-photo.png", "color": "teal"},
    5: {"id": "bathroom", "image": "images/kitchen-photo.png", "color": "coral"},
}

ROOM_ID_BY_SLUG = {meta["id"]: room_id for room_id, meta in ROOM_META.items()}

SENSOR_ICON = {
    "temperature": "thermometer",
    "humidity": "drop",
    "light": "sun",
    "motion": "user",
    "co2": "co2",
    "dust": "sun",
}

ACTIVE_STATES = {"ON", "COOLING", "HEATING", "OPEN"}

ACTUATOR_ON_STATE = {
    "light": "ON",
    "air_conditioner": "COOLING",
    "fan": "ON",
    "door_lock": "LOCKED",
    "curtain": "OPEN",
}

ACTUATOR_OFF_STATE = {
    "light": "OFF",
    "air_conditioner": "OFF",
    "fan": "OFF",
    "door_lock": "UNLOCKED",
    "curtain": "CLOSED",
}


class DatabaseUnavailable(RuntimeError):
    """Raised when MySQL is not reachable or the driver is missing."""


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def db_config() -> dict[str, Any]:
    load_env_file()
    return {
        "host": os.getenv("MYSQL_HOST", DB_ENV_DEFAULTS["MYSQL_HOST"]),
        "port": int(os.getenv("MYSQL_PORT", DB_ENV_DEFAULTS["MYSQL_PORT"])),
        "user": os.getenv("MYSQL_USER", DB_ENV_DEFAULTS["MYSQL_USER"]),
        "password": os.getenv("MYSQL_PASSWORD", DB_ENV_DEFAULTS["MYSQL_PASSWORD"]),
        "database": os.getenv("MYSQL_DB", DB_ENV_DEFAULTS["MYSQL_DB"]),
    }


def create_connection():
    try:
        import mysql.connector
    except ModuleNotFoundError as exc:
        raise DatabaseUnavailable(
            "mysql-connector-python is not installed. Run: python3 -m pip install -r modern_home_manager/requirements.txt"
        ) from exc

    try:
        return mysql.connector.connect(**db_config())
    except Exception as exc:
        raise DatabaseUnavailable(f"MySQL connection failed: {exc}") from exc


@contextmanager
def cursor(dictionary: bool = True) -> Iterator[Any]:
    conn = create_connection()
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with cursor(dictionary=True) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    with cursor(dictionary=False) as cur:
        cur.execute(query, params)


def execute_many(statements: list[tuple[str, tuple[Any, ...]]]) -> None:
    if not statements:
        return
    with cursor(dictionary=False) as cur:
        for query, params in statements:
            cur.execute(query, params)


def initialize_database() -> None:
    fetch_all("SELECT 1")


def room_slug(room_id: int) -> str:
    return ROOM_META.get(room_id, {"id": f"room-{room_id}"})["id"]


def room_int_id(room_id: str) -> int | None:
    if room_id.startswith("room-"):
        try:
            return int(room_id.removeprefix("room-"))
        except ValueError:
            return None
    return ROOM_ID_BY_SLUG.get(room_id)


def actuator_api_id(actuator_id: int) -> str:
    return f"actuator-{actuator_id}"


def actuator_int_id(actuator_id: str) -> int | None:
    try:
        return int(actuator_id.removeprefix("actuator-"))
    except ValueError:
        return None


def format_time(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%H:%M:%S")
    return datetime.fromisoformat(str(value)).strftime("%H:%M:%S")


def format_sensor_value(sensor_type: str, value: float, unit: str) -> str:
    if sensor_type == "temperature":
        return f"{float(value):.1f}C"
    if sensor_type in {"humidity", "light", "co2", "dust"}:
        return f"{float(value):.0f} {unit}"
    if sensor_type == "motion":
        return "감지" if float(value) else "없음"
    return f"{value} {unit}".strip()


def latest_sensor_values(room_id: int) -> dict[str, float]:
    rows = fetch_all(
        """
        SELECT st.type_name, sr.measured_value
        FROM SENSOR s
        JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
        JOIN SENSOR_READING sr ON sr.sensor_id = s.sensor_id
        WHERE s.room_id = %s
          AND sr.reading_id = (
              SELECT sr2.reading_id
              FROM SENSOR_READING sr2
              WHERE sr2.sensor_id = s.sensor_id
              ORDER BY sr2.measured_time DESC, sr2.reading_id DESC
              LIMIT 1
          )
        """,
        (room_id,),
    )
    return {row["type_name"]: float(row["measured_value"]) for row in rows}


def latest_actuator_rows(room_id: int | None = None) -> list[dict[str, Any]]:
    where = "WHERE a.room_id = %s" if room_id is not None else ""
    params = (room_id,) if room_id is not None else ()
    return fetch_all(
        f"""
        SELECT a.actuator_id, a.room_id, a.actuator_name, at.type_name,
               COALESCE(asl.state_value, 'OFF') AS state_value,
               asl.changed_time
        FROM ACTUATOR a
        JOIN ACTUATOR_TYPE at ON a.actuator_type_id = at.actuator_type_id
        LEFT JOIN ACTUATOR_STATE_LOG asl
          ON asl.actuator_state_id = (
              SELECT asl2.actuator_state_id
              FROM ACTUATOR_STATE_LOG asl2
              WHERE asl2.actuator_id = a.actuator_id
              ORDER BY asl2.changed_time DESC, asl2.actuator_state_id DESC
              LIMIT 1
          )
        {where}
        ORDER BY a.room_id, a.actuator_id
        """,
        params,
    )


def active_device_count(room_id: int) -> int:
    return sum(1 for row in latest_actuator_rows(room_id) if row["state_value"] in ACTIVE_STATES)


def temperature_sparkline(room_id: int) -> list[float]:
    rows = fetch_all(
        """
        SELECT sr.measured_value
        FROM SENSOR_READING sr
        JOIN SENSOR s ON s.sensor_id = sr.sensor_id
        JOIN SENSOR_TYPE st ON st.sensor_type_id = s.sensor_type_id
        WHERE s.room_id = %s AND st.type_name = 'temperature'
        ORDER BY sr.measured_time DESC, sr.reading_id DESC
        LIMIT 9
        """,
        (room_id,),
    )
    values = [round(float(row["measured_value"]), 1) for row in rows]
    values.reverse()
    return values or [0]


def fetch_rooms() -> list[dict[str, Any]]:
    rows = fetch_all("SELECT room_id, room_name FROM ROOM ORDER BY room_id")
    status_rows = {
        row["room_id"]: row["status_name"]
        for row in fetch_all(
            """
            SELECT rsl.room_id, rst.status_name
            FROM ROOM_STATUS_LOG rsl
            JOIN ROOM_STATUS_TYPE rst ON rsl.status_id = rst.status_id
            WHERE rsl.room_status_log_id = (
                SELECT rsl2.room_status_log_id
                FROM ROOM_STATUS_LOG rsl2
                WHERE rsl2.room_id = rsl.room_id
                ORDER BY rsl2.changed_time DESC, rsl2.room_status_log_id DESC
                LIMIT 1
            )
            """
        )
    }
    labels = {"IN_USE": "사용중", "EMPTY": "비어있음", "CLEANING": "청소중", "RESERVED": "예약됨"}
    rooms = []
    for row in rows:
        meta = ROOM_META.get(row["room_id"], {"id": f"room-{row['room_id']}", "image": "images/living-room-photo.png", "color": "teal"})
        latest = latest_sensor_values(row["room_id"])
        rooms.append(
            {
                "id": meta["id"],
                "name": row["room_name"],
                "status": labels.get(status_rows.get(row["room_id"], "EMPTY"), "정상"),
                "image": meta["image"],
                "temperature": latest.get("temperature", 0),
                "humidity": round(latest.get("humidity", 0)),
                "light": round(latest.get("light", latest.get("motion", 0))),
                "devices_on": active_device_count(row["room_id"]),
                "spark": temperature_sparkline(row["room_id"]),
                "color": meta["color"],
            }
        )
    return rooms


def fetch_latest_sensors() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT s.sensor_id, s.room_id, s.sensor_name, st.type_name, st.unit,
               r.room_name, sr.measured_value, sr.measured_time
        FROM SENSOR s
        JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
        JOIN ROOM r ON s.room_id = r.room_id
        JOIN SENSOR_READING sr ON sr.sensor_id = s.sensor_id
        WHERE sr.reading_id = (
            SELECT sr2.reading_id
            FROM SENSOR_READING sr2
            WHERE sr2.sensor_id = s.sensor_id
            ORDER BY sr2.measured_time DESC, sr2.reading_id DESC
            LIMIT 1
        )
        ORDER BY r.room_id, s.sensor_id
        """
    )
    return [
        {
            "id": str(row["sensor_id"]),
            "icon": SENSOR_ICON.get(row["type_name"], "sun"),
            "label": f"{row['sensor_name']} ({row['room_name']})",
            "value": format_sensor_value(row["type_name"], row["measured_value"], row["unit"]),
            "room": room_slug(row["room_id"]),
            "time": format_time(row["measured_time"]),
        }
        for row in rows
    ]


def fetch_actuators(room_id: int | None = None) -> list[dict[str, Any]]:
    return [
        {
            "id": actuator_api_id(row["actuator_id"]),
            "room": room_slug(row["room_id"]),
            "icon": "ac" if row["type_name"] == "air_conditioner" else row["type_name"],
            "name": row["actuator_name"],
            "detail": row["state_value"],
            "active": row["state_value"] in ACTIVE_STATES,
        }
        for row in latest_actuator_rows(room_id)
    ]


def fetch_reservations() -> list[dict[str, str]]:
    rows = fetch_all(
        """
        SELECT rr.start_time, rr.end_time, rr.purpose, rr.reservation_status, r.room_name
        FROM ROOM_RESERVATION rr
        JOIN ROOM r ON rr.room_id = r.room_id
        ORDER BY rr.start_time
        LIMIT 5
        """
    )
    labels = {"RESERVED": "예약됨", "CANCELLED": "취소됨", "FINISHED": "완료됨"}
    return [
        {
            "time": format_time(row["start_time"]),
            "title": f"{row['room_name']} {row['purpose'] or '예약'}",
            "repeat": f"~ {format_time(row['end_time'])}",
            "status": labels.get(row["reservation_status"], row["reservation_status"]),
        }
        for row in rows
    ]


def fetch_location() -> dict[str, Any]:
    rows = fetch_all(
        """
        SELECT u.user_name, COALESCE(r.room_name, '위치 없음') AS place_label,
               m.source, m.accuracy, m.latitude, m.longitude, m.note, m.updated_at
        FROM `USER` u
        LEFT JOIN USER_LOCATION ul ON u.user_id = ul.user_id
        LEFT JOIN ROOM r ON ul.room_id = r.room_id
        LEFT JOIN MODERN_BROWSER_LOCATION m ON m.user_id = u.user_id
        ORDER BY u.user_id
        LIMIT 1
        """
    )
    if not rows:
        return {"user": "관리자", "place": "집", "time": "-", "updated": "-", "source": "none", "accuracy": None, "latitude": None, "longitude": None, "note": "사용자 데이터가 없습니다."}
    row = rows[0]
    updated = row.get("updated_at")
    return {
        "user": row["user_name"],
        "place": row["place_label"],
        "time": format_time(updated) if updated else "-",
        "updated": format_time(updated) if updated else "-",
        "source": row.get("source") or "mysql",
        "accuracy": row.get("accuracy"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "note": row.get("note") or "MySQL USER_LOCATION 기준 위치입니다.",
    }


def fetch_logs() -> list[dict[str, str]]:
    sensor_logs = fetch_all(
        """
        SELECT 'temp' AS icon, CONCAT(r.room_name, ' ', s.sensor_name, ' 업데이트') AS message,
               CONCAT(ROUND(sr.measured_value, 1), st.unit) AS value,
               sr.measured_time AS created_at
        FROM SENSOR_READING sr
        JOIN SENSOR s ON sr.sensor_id = s.sensor_id
        JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
        JOIN ROOM r ON s.room_id = r.room_id
        ORDER BY sr.measured_time DESC, sr.reading_id DESC
        LIMIT 4
        """
    )
    actuator_logs = fetch_all(
        """
        SELECT at.type_name AS icon, CONCAT(r.room_name, ' ', a.actuator_name, ' 상태 변경') AS message,
               asl.state_value AS value, asl.changed_time AS created_at
        FROM ACTUATOR_STATE_LOG asl
        JOIN ACTUATOR a ON asl.actuator_id = a.actuator_id
        JOIN ACTUATOR_TYPE at ON a.actuator_type_id = at.actuator_type_id
        JOIN ROOM r ON a.room_id = r.room_id
        ORDER BY asl.changed_time DESC, asl.actuator_state_id DESC
        LIMIT 4
        """
    )
    rows = sorted(sensor_logs + actuator_logs, key=lambda item: item["created_at"], reverse=True)[:8]
    return [
        {
            "time": format_time(row["created_at"]),
            "icon": "ac" if row["icon"] == "air_conditioner" else row["icon"],
            "message": row["message"],
            "value": str(row["value"]),
        }
        for row in rows
    ]


def fetch_status(rooms: list[dict[str, Any]], actuators: list[dict[str, Any]]) -> dict[str, Any]:
    temperatures = [room["temperature"] for room in rooms if room["temperature"]]
    humidities = [room["humidity"] for room in rooms if room["humidity"]]
    avg_temp = round(sum(temperatures) / len(temperatures), 1) if temperatures else 0
    avg_humidity = round(sum(humidities) / len(humidities)) if humidities else 0
    return {
        "connection": "MySQL 연결됨",
        "security": "해제",
        "averageTemperature": f"{avg_temp:.1f}C",
        "averageHumidity": f"{avg_humidity}%",
        "currentTime": now_text(),
        "gateway": f"{db_config()['host']}:{db_config()['port']}",
        "firmware": "modern-mysql-v1",
        "activeDevices": sum(1 for item in actuators if item["active"]),
    }


def build_dashboard_payload() -> dict[str, Any]:
    rooms = fetch_rooms()
    sensors = fetch_latest_sensors()
    actuators = fetch_actuators()
    return {
        "status": fetch_status(rooms, actuators),
        "sensors": sensors,
        "temperatures": [{"room": room["name"], "value": room["temperature"], "color": room["color"]} for room in rooms],
        "actuators": actuators,
        "reservations": fetch_reservations(),
        "location": fetch_location(),
        "logs": fetch_logs(),
        "rooms": rooms,
    }


def room_payload(room_id: str) -> dict[str, Any] | None:
    int_id = room_int_id(room_id)
    if int_id is None:
        return None
    payload = build_dashboard_payload()
    room = next((item for item in payload["rooms"] if item["id"] == room_id), None)
    if room is None:
        return None
    return {
        "room": room,
        "actuators": fetch_actuators(int_id),
        "sensors": [item for item in payload["sensors"] if item["room"] == room_id],
    }


def update_location(latitude: float, longitude: float, accuracy: float | None) -> dict[str, Any]:
    execute(
        """
        INSERT INTO MODERN_BROWSER_LOCATION
            (user_id, source, latitude, longitude, accuracy, note, updated_at)
        VALUES (1, 'browser_geolocation', %s, %s, %s, '브라우저 위치 권한으로 받은 좌표를 저장했습니다.', NOW())
        ON DUPLICATE KEY UPDATE
            source = VALUES(source),
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            accuracy = VALUES(accuracy),
            note = VALUES(note),
            updated_at = VALUES(updated_at)
        """,
        (round(latitude, 6), round(longitude, 6), round(accuracy, 1) if accuracy is not None else None),
    )
    return fetch_location()


def set_actuator_active(actuator_id: str, active: bool) -> dict[str, Any]:
    int_id = actuator_int_id(actuator_id)
    if int_id is None:
        raise KeyError(actuator_id)
    rows = fetch_all(
        """
        SELECT a.actuator_id, at.type_name
        FROM ACTUATOR a
        JOIN ACTUATOR_TYPE at ON a.actuator_type_id = at.actuator_type_id
        WHERE a.actuator_id = %s
        """,
        (int_id,),
    )
    if not rows:
        raise KeyError(actuator_id)
    state = (ACTUATOR_ON_STATE if active else ACTUATOR_OFF_STATE).get(rows[0]["type_name"], "ON" if active else "OFF")
    execute(
        "INSERT INTO ACTUATOR_STATE_LOG (actuator_id, state_value, changed_time) VALUES (%s, %s, NOW())",
        (int_id, state),
    )
    return next(item for item in fetch_actuators() if item["id"] == actuator_id)


def record_device_frame(payload: dict[str, Any]) -> None:
    device_id = payload.get("device_id")
    if not isinstance(device_id, str) or not device_id:
        raise ValueError("device_id is required")

    rows = fetch_all("SELECT room_id FROM DEVICE WHERE device_id = %s", (device_id,))
    if not rows:
        raise ValueError(f"unknown device_id: {device_id}")
    room_id = rows[0]["room_id"]

    statements: list[tuple[str, tuple[Any, ...]]] = []
    for sensor_type, value in (payload.get("sensors") or {}).items():
        sensor_rows = fetch_all(
            """
            SELECT s.sensor_id
            FROM SENSOR s
            JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
            WHERE s.room_id = %s AND st.type_name = %s
            """,
            (room_id, sensor_type),
        )
        if sensor_rows:
            statements.append(
                (
                    "INSERT INTO SENSOR_READING (sensor_id, measured_value, measured_time) VALUES (%s, %s, NOW())",
                    (sensor_rows[0]["sensor_id"], float(value)),
                )
            )

    for actuator_type, state in (payload.get("actuators") or {}).items():
        actuator_rows = fetch_all(
            """
            SELECT a.actuator_id
            FROM ACTUATOR a
            JOIN ACTUATOR_TYPE at ON a.actuator_type_id = at.actuator_type_id
            WHERE a.room_id = %s AND at.type_name = %s
            """,
            (room_id, actuator_type),
        )
        if actuator_rows:
            state_value = str(state).upper() if not isinstance(state, bool) else ("ON" if state else "OFF")
            statements.append(
                (
                    "INSERT INTO ACTUATOR_STATE_LOG (actuator_id, state_value, changed_time) VALUES (%s, %s, NOW())",
                    (actuator_rows[0]["actuator_id"], state_value),
                )
            )

    execute_many(statements)
