from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "home_manager.db"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with closing(connect(path)) as conn:
        conn.executescript(SCHEMA_SQL)
        seed_database(conn)
        conn.commit()


def seed_database(conn: sqlite3.Connection) -> None:
    rooms = [
        ("living", "거실", "정상", "images/living-room-photo.png", 1, "teal"),
        ("bedroom", "침실", "정상", "images/bedroom-photo.png", 2, "coral"),
        ("kitchen", "주방", "정상", "images/kitchen-photo.png", 3, "lime"),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO rooms
            (room_id, room_name, status_label, image_path, display_order, chart_color)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rooms,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO devices (device_id, room_id, device_name) VALUES (?, ?, ?)",
        [
            ("pico_living_room", "living", "Pico Living Room Simulator"),
            ("pico_bedroom", "bedroom", "Pico Bedroom Simulator"),
            ("pico_kitchen", "kitchen", "Pico Kitchen Simulator"),
        ],
    )

    sensors = [
        ("temp-living", "living", "temperature", "온도", "thermometer", "C"),
        ("humidity-living", "living", "humidity", "습도", "drop", "%"),
        ("dust-living", "living", "dust", "미세먼지", "sun", "ug/m3"),
        ("light-living", "living", "light", "조도", "sun", "lux"),
        ("co2-living", "living", "co2", "CO2", "co2", "ppm"),
        ("temp-bedroom", "bedroom", "temperature", "온도", "thermometer", "C"),
        ("humidity-bedroom", "bedroom", "humidity", "습도", "drop", "%"),
        ("light-bedroom", "bedroom", "light", "조도", "sun", "lux"),
        ("temp-kitchen", "kitchen", "temperature", "온도", "thermometer", "C"),
        ("humidity-kitchen", "kitchen", "humidity", "습도", "drop", "%"),
        ("light-kitchen", "kitchen", "light", "조도", "sun", "lux"),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO sensors
            (sensor_id, room_id, sensor_type, sensor_label, icon, unit)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        sensors,
    )

    actuators = [
        ("living-light", "living", "light", "거실 조명", "light", 1, "켜짐"),
        ("living-ac", "living", "ac", "거실 에어컨", "ac", 1, "냉방 24C"),
        ("living-curtain", "living", "curtain", "거실 커튼", "curtain", 1, "열림 60%"),
        ("bedroom-light", "bedroom", "light", "침실 조명", "light", 1, "취침등"),
        ("bedroom-ac", "bedroom", "ac", "침실 에어컨", "ac", 1, "수면 26C"),
        ("kitchen-fan", "kitchen", "fan", "환기 팬", "fan", 1, "중간"),
        ("kitchen-plug", "kitchen", "plug", "주방 콘센트", "plug", 0, "꺼짐"),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO actuators
            (actuator_id, room_id, actuator_type, actuator_name, icon, active, detail)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        actuators,
    )

    conn.executemany(
        """
        INSERT OR IGNORE INTO reservations
            (reservation_id, schedule_time, title, repeat_label, status_label)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, "22:00", "거실 조명 끄기", "매일", "활성"),
            (2, "07:00", "거실 커튼 열기", "매일", "활성"),
            (3, "18:30", "에어컨 켜기 (24C)", "주중", "활성"),
        ],
    )

    conn.execute(
        """
        INSERT OR IGNORE INTO locations
            (location_id, user_label, place_label, source, note, updated_at)
        VALUES (1, '관리자', '집', 'sample',
                '브라우저 위치 권한을 허용하면 GPS 기반 좌표를 저장합니다.',
                ?)
        """,
        (now_text(),),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO system_status
            (status_id, connection_label, security_label, gateway, firmware, updated_at)
        VALUES (1, '실시간 연결됨', '해제', '127.0.0.1', 'modern-db-v1', ?)
        """,
        (now_text(),),
    )

    if conn.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0] == 0:
        insert_readings(
            conn,
            {
                "temp-living": 23.4,
                "humidity-living": 45,
                "dust-living": 12,
                "light-living": 386,
                "co2-living": 540,
                "temp-bedroom": 21.2,
                "humidity-bedroom": 50,
                "light-bedroom": 120,
                "temp-kitchen": 24.1,
                "humidity-kitchen": 47,
                "light-kitchen": 320,
            },
        )
        add_event(conn, "temp", "거실 온도 센서 업데이트", "23.4C")
        add_event(conn, "ac", "거실 에어컨 설정 변경", "24C 냉방")
        add_event(conn, "light", "거실 조명 켜짐", "수동")


def insert_readings(conn: sqlite3.Connection, values: dict[str, float]) -> None:
    captured_at = now_text()
    conn.executemany(
        "INSERT INTO sensor_readings (sensor_id, measured_value, captured_at) VALUES (?, ?, ?)",
        [(sensor_id, value, captured_at) for sensor_id, value in values.items()],
    )


def add_event(conn: sqlite3.Connection, icon: str, message: str, value: str) -> None:
    conn.execute(
        "INSERT INTO event_logs (icon, message, value, created_at) VALUES (?, ?, ?, ?)",
        (icon, message, value, now_text()),
    )


def build_dashboard_payload(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    initialize_database(db_path)
    with closing(connect(db_path)) as conn:
        rooms = fetch_rooms(conn)
        sensors = fetch_latest_sensors(conn)
        actuators = fetch_actuators(conn)
        reservations = fetch_reservations(conn)
        location = fetch_location(conn)
        logs = fetch_logs(conn)
        status = fetch_status(conn, rooms, actuators)

    return {
        "status": status,
        "sensors": sensors,
        "temperatures": [
            {"room": room["name"], "value": room["temperature"], "color": room["color"]}
            for room in rooms
        ],
        "actuators": actuators,
        "reservations": reservations,
        "location": location,
        "logs": logs,
        "rooms": rooms,
    }


def room_payload(db_path: str | Path, room_id: str) -> dict[str, Any] | None:
    payload = build_dashboard_payload(db_path)
    room = next((item for item in payload["rooms"] if item["id"] == room_id), None)
    if room is None:
        return None
    return {
        "room": room,
        "actuators": [item for item in payload["actuators"] if item["room"] == room_id],
        "sensors": [item for item in payload["sensors"] if item["room"] == room_id],
    }


def fetch_rooms(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT room_id, room_name, status_label, image_path, chart_color
        FROM rooms
        ORDER BY display_order
        """
    ).fetchall()
    rooms = []
    for row in rows:
        latest = latest_sensor_values(conn, row["room_id"])
        rooms.append(
            {
                "id": row["room_id"],
                "name": row["room_name"],
                "status": row["status_label"],
                "image": row["image_path"],
                "temperature": latest.get("temperature", 0),
                "humidity": round(latest.get("humidity", 0)),
                "light": round(latest.get("light", 0)),
                "devices_on": active_device_count(conn, row["room_id"]),
                "spark": temperature_sparkline(conn, row["room_id"]),
                "color": row["chart_color"],
            }
        )
    return rooms


def latest_sensor_values(conn: sqlite3.Connection, room_id: str) -> dict[str, float]:
    rows = conn.execute(
        """
        SELECT s.sensor_type, sr.measured_value
        FROM sensors s
        JOIN sensor_readings sr ON sr.sensor_id = s.sensor_id
        WHERE s.room_id = ?
          AND sr.captured_at = (
              SELECT MAX(sr2.captured_at)
              FROM sensor_readings sr2
              WHERE sr2.sensor_id = s.sensor_id
          )
        """,
        (room_id,),
    ).fetchall()
    return {row["sensor_type"]: float(row["measured_value"]) for row in rows}


def active_device_count(conn: sqlite3.Connection, room_id: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM actuators WHERE room_id = ? AND active = 1",
        (room_id,),
    ).fetchone()[0]


def temperature_sparkline(conn: sqlite3.Connection, room_id: str) -> list[float]:
    rows = conn.execute(
        """
        SELECT sr.measured_value
        FROM sensor_readings sr
        JOIN sensors s ON s.sensor_id = sr.sensor_id
        WHERE s.room_id = ? AND s.sensor_type = 'temperature'
        ORDER BY sr.captured_at DESC, sr.reading_id DESC
        LIMIT 9
        """,
        (room_id,),
    ).fetchall()
    values = [round(float(row["measured_value"]), 1) for row in rows]
    values.reverse()
    return values or [0]


def fetch_latest_sensors(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT s.sensor_id, s.room_id, s.sensor_label, s.sensor_type, s.icon, s.unit,
               r.room_name, sr.measured_value, sr.captured_at
        FROM sensors s
        JOIN rooms r ON r.room_id = s.room_id
        JOIN sensor_readings sr ON sr.sensor_id = s.sensor_id
        WHERE sr.captured_at = (
            SELECT MAX(sr2.captured_at)
            FROM sensor_readings sr2
            WHERE sr2.sensor_id = s.sensor_id
        )
        ORDER BY r.display_order, s.sensor_id
        """
    ).fetchall()
    return [
        {
            "id": row["sensor_id"],
            "icon": row["icon"],
            "label": f"{row['sensor_label']} ({row['room_name']})",
            "value": format_sensor_value(row["sensor_type"], row["measured_value"], row["unit"]),
            "room": row["room_id"],
            "time": format_time(row["captured_at"]),
        }
        for row in rows
    ]


def format_sensor_value(sensor_type: str, value: float, unit: str) -> str:
    if sensor_type == "temperature":
        return f"{float(value):.1f}C"
    if sensor_type in {"humidity", "light", "co2", "dust"}:
        return f"{float(value):.0f} {unit}"
    return f"{value} {unit}".strip()


def fetch_actuators(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT actuator_id, room_id, icon, actuator_name, active, detail
        FROM actuators
        ORDER BY room_id, actuator_id
        """
    ).fetchall()
    return [
        {
            "id": row["actuator_id"],
            "room": row["room_id"],
            "icon": row["icon"],
            "name": row["actuator_name"],
            "detail": row["detail"],
            "active": bool(row["active"]),
        }
        for row in rows
    ]


def fetch_reservations(conn: sqlite3.Connection) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT schedule_time, title, repeat_label, status_label
        FROM reservations
        ORDER BY schedule_time
        """
    ).fetchall()
    return [
        {
            "time": row["schedule_time"],
            "title": row["title"],
            "repeat": row["repeat_label"],
            "status": row["status_label"],
        }
        for row in rows
    ]


def fetch_location(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM locations WHERE location_id = 1").fetchone()
    return {
        "user": row["user_label"],
        "place": row["place_label"],
        "time": format_time(row["updated_at"]),
        "updated": format_time(row["updated_at"]),
        "source": row["source"],
        "accuracy": row["accuracy"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "note": row["note"],
    }


def fetch_logs(conn: sqlite3.Connection) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT icon, message, value, created_at
        FROM event_logs
        ORDER BY created_at DESC, event_id DESC
        LIMIT 8
        """
    ).fetchall()
    return [
        {
            "time": format_time(row["created_at"]),
            "icon": row["icon"],
            "message": row["message"],
            "value": row["value"],
        }
        for row in rows
    ]


def fetch_status(
    conn: sqlite3.Connection,
    rooms: list[dict[str, Any]],
    actuators: list[dict[str, Any]],
) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM system_status WHERE status_id = 1").fetchone()
    temperatures = [room["temperature"] for room in rooms if room["temperature"]]
    humidities = [room["humidity"] for room in rooms if room["humidity"]]
    avg_temp = round(sum(temperatures) / len(temperatures), 1) if temperatures else 0
    avg_humidity = round(sum(humidities) / len(humidities)) if humidities else 0
    return {
        "connection": row["connection_label"],
        "security": row["security_label"],
        "averageTemperature": f"{avg_temp:.1f}C",
        "averageHumidity": f"{avg_humidity}%",
        "currentTime": now_text(),
        "gateway": row["gateway"],
        "firmware": row["firmware"],
        "activeDevices": sum(1 for item in actuators if item["active"]),
    }


def update_location(
    db_path: str | Path,
    latitude: float,
    longitude: float,
    accuracy: float | None,
) -> dict[str, Any]:
    initialize_database(db_path)
    updated_at = now_text()
    with closing(connect(db_path)) as conn:
        conn.execute(
            """
            UPDATE locations
            SET source = 'browser_geolocation',
                latitude = ?,
                longitude = ?,
                accuracy = ?,
                note = '브라우저 위치 권한으로 받은 좌표를 저장했습니다.',
                updated_at = ?
            WHERE location_id = 1
            """,
            (
                round(float(latitude), 6),
                round(float(longitude), 6),
                round(float(accuracy), 1) if accuracy is not None else None,
                updated_at,
            ),
        )
        add_event(conn, "user", "사용자 위치 업데이트", "브라우저 좌표")
        conn.commit()
    with closing(connect(db_path)) as conn:
        return fetch_location(conn)


def set_actuator_active(
    db_path: str | Path,
    actuator_id: str,
    active: bool,
) -> dict[str, Any]:
    initialize_database(db_path)
    with closing(connect(db_path)) as conn:
        row = conn.execute(
            "SELECT actuator_name FROM actuators WHERE actuator_id = ?",
            (actuator_id,),
        ).fetchone()
        if row is None:
            raise KeyError(actuator_id)
        detail = "켜짐" if active else "꺼짐"
        conn.execute(
            "UPDATE actuators SET active = ?, detail = ?, updated_at = ? WHERE actuator_id = ?",
            (1 if active else 0, detail, now_text(), actuator_id),
        )
        add_event(conn, "light", f"{row['actuator_name']} 상태 변경", detail)
        conn.commit()
    payload = build_dashboard_payload(db_path)
    return next(item for item in payload["actuators"] if item["id"] == actuator_id)


def record_device_frame(db_path: str | Path, payload: dict[str, Any]) -> None:
    initialize_database(db_path)
    device_id = payload.get("device_id")
    if not isinstance(device_id, str) or not device_id:
        raise ValueError("device_id is required")

    with closing(connect(db_path)) as conn:
        room = conn.execute(
            "SELECT room_id FROM devices WHERE device_id = ?",
            (device_id,),
        ).fetchone()
        if room is None:
            raise ValueError(f"unknown device_id: {device_id}")

        sensor_values = {}
        for sensor_type, value in (payload.get("sensors") or {}).items():
            sensor = conn.execute(
                "SELECT sensor_id FROM sensors WHERE room_id = ? AND sensor_type = ?",
                (room["room_id"], sensor_type),
            ).fetchone()
            if sensor is not None:
                sensor_values[sensor["sensor_id"]] = float(value)
        if sensor_values:
            insert_readings(conn, sensor_values)

        for actuator_id, active in (payload.get("actuators") or {}).items():
            exists = conn.execute(
                "SELECT actuator_name FROM actuators WHERE actuator_id = ?",
                (actuator_id,),
            ).fetchone()
            if exists is None:
                continue
            detail = "켜짐" if bool(active) else "꺼짐"
            conn.execute(
                "UPDATE actuators SET active = ?, detail = ?, updated_at = ? WHERE actuator_id = ?",
                (1 if bool(active) else 0, detail, now_text(), actuator_id),
            )

        add_event(conn, "temp", f"{device_id} 시뮬레이션 수신", "저장됨")
        conn.commit()


def format_time(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%H:%M:%S")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rooms (
    room_id TEXT PRIMARY KEY,
    room_name TEXT NOT NULL,
    status_label TEXT NOT NULL,
    image_path TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    chart_color TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sensors (
    sensor_id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL REFERENCES rooms(room_id),
    sensor_type TEXT NOT NULL,
    sensor_label TEXT NOT NULL,
    icon TEXT NOT NULL,
    unit TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL REFERENCES sensors(sensor_id),
    measured_value REAL NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actuators (
    actuator_id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL REFERENCES rooms(room_id),
    actuator_type TEXT NOT NULL,
    actuator_name TEXT NOT NULL,
    icon TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    detail TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id INTEGER PRIMARY KEY,
    schedule_time TEXT NOT NULL,
    title TEXT NOT NULL,
    repeat_label TEXT NOT NULL,
    status_label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
    location_id INTEGER PRIMARY KEY,
    user_label TEXT NOT NULL,
    place_label TEXT NOT NULL,
    source TEXT NOT NULL,
    accuracy REAL,
    latitude REAL,
    longitude REAL,
    note TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_status (
    status_id INTEGER PRIMARY KEY,
    connection_label TEXT NOT NULL,
    security_label TEXT NOT NULL,
    gateway TEXT NOT NULL,
    firmware TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL REFERENCES rooms(room_id),
    device_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_logs (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    icon TEXT NOT NULL,
    message TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""
