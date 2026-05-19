import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from db import fetch_all

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")

LATEST_SENSOR_SQL = """
SELECT r.room_id, r.room_name, s.sensor_name, st.type_name, sr.measured_value, st.unit, sr.measured_time
FROM SENSOR_READING sr
JOIN SENSOR s ON sr.sensor_id = s.sensor_id
JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
JOIN ROOM r ON s.room_id = r.room_id
WHERE sr.measured_time = (
    SELECT MAX(sr2.measured_time)
    FROM SENSOR_READING sr2
    WHERE sr2.sensor_id = sr.sensor_id
)
ORDER BY r.room_id, s.sensor_id
"""

AVG_TEMP_SQL = """
SELECT r.room_name, ROUND(AVG(sr.measured_value), 2) AS avg_temperature
FROM SENSOR_READING sr
JOIN SENSOR s ON sr.sensor_id = s.sensor_id
JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
JOIN ROOM r ON s.room_id = r.room_id
WHERE st.type_name = 'temperature'
GROUP BY r.room_id, r.room_name
ORDER BY r.room_id
"""

ACTIVE_ACTUATOR_SQL = """
SELECT r.room_name, a.actuator_name, at.type_name, asl.state_value, asl.changed_time
FROM ACTUATOR_STATE_LOG asl
JOIN ACTUATOR a ON asl.actuator_id = a.actuator_id
JOIN ACTUATOR_TYPE at ON a.actuator_type_id = at.actuator_type_id
JOIN ROOM r ON a.room_id = r.room_id
WHERE asl.changed_time = (
    SELECT MAX(asl2.changed_time)
    FROM ACTUATOR_STATE_LOG asl2
    WHERE asl2.actuator_id = asl.actuator_id
)
AND asl.state_value IN ('ON', 'COOLING', 'HEATING', 'OPEN')
ORDER BY r.room_id, a.actuator_id
"""

ROOM_STATUS_SQL = """
SELECT r.room_name, rst.status_name, rsl.changed_time
FROM ROOM_STATUS_LOG rsl
JOIN ROOM r ON rsl.room_id = r.room_id
JOIN ROOM_STATUS_TYPE rst ON rsl.status_id = rst.status_id
WHERE rsl.changed_time = (
    SELECT MAX(rsl2.changed_time)
    FROM ROOM_STATUS_LOG rsl2
    WHERE rsl2.room_id = rsl.room_id
)
ORDER BY r.room_id
"""

USER_LOCATION_SQL = """
SELECT u.user_name, COALESCE(r.room_name, '위치 없음') AS current_location
FROM USER_LOCATION ul
JOIN `USER` u ON ul.user_id = u.user_id
LEFT JOIN ROOM r ON ul.room_id = r.room_id
ORDER BY u.user_id
"""

RESERVATION_SQL = """
SELECT rr.reservation_id, u.user_name, r.room_name, rr.start_time, rr.end_time, rr.purpose, rr.reservation_status
FROM ROOM_RESERVATION rr
JOIN `USER` u ON rr.user_id = u.user_id
JOIN ROOM r ON rr.room_id = r.room_id
ORDER BY rr.start_time
"""

RECENT_READING_SQL = """
SELECT r.room_name, s.sensor_name, sr.measured_value, st.unit, sr.measured_time
FROM SENSOR_READING sr
JOIN SENSOR s ON sr.sensor_id = s.sensor_id
JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
JOIN ROOM r ON s.room_id = r.room_id
ORDER BY sr.measured_time DESC, sr.reading_id DESC
LIMIT 10
"""

RECENT_ACTUATOR_SQL = """
SELECT r.room_name, a.actuator_name, asl.state_value, asl.changed_time
FROM ACTUATOR_STATE_LOG asl
JOIN ACTUATOR a ON asl.actuator_id = a.actuator_id
JOIN ROOM r ON a.room_id = r.room_id
ORDER BY asl.changed_time DESC, asl.actuator_state_id DESC
LIMIT 10
"""

@app.route("/")
def dashboard():
    return render_template(
        "index.html",
        latest_sensors=fetch_all(LATEST_SENSOR_SQL),
        avg_temperatures=fetch_all(AVG_TEMP_SQL),
        active_actuators=fetch_all(ACTIVE_ACTUATOR_SQL),
        room_statuses=fetch_all(ROOM_STATUS_SQL),
        user_locations=fetch_all(USER_LOCATION_SQL),
        reservations=fetch_all(RESERVATION_SQL),
        recent_readings=fetch_all(RECENT_READING_SQL),
        recent_actuators=fetch_all(RECENT_ACTUATOR_SQL),
    )

@app.route("/room/<int:room_id>")
def room_detail(room_id):
    room = fetch_all("SELECT room_id, room_name FROM ROOM WHERE room_id = %s", (room_id,))
    sensors = fetch_all(
        """
        SELECT s.sensor_name, st.type_name, sr.measured_value, st.unit, sr.measured_time
        FROM SENSOR_READING sr
        JOIN SENSOR s ON sr.sensor_id = s.sensor_id
        JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
        WHERE s.room_id = %s
        AND sr.measured_time = (
            SELECT MAX(sr2.measured_time) FROM SENSOR_READING sr2 WHERE sr2.sensor_id = sr.sensor_id
        )
        ORDER BY s.sensor_id
        """,
        (room_id,),
    )
    actuators = fetch_all(
        """
        SELECT a.actuator_name, at.type_name, asl.state_value, asl.changed_time
        FROM ACTUATOR_STATE_LOG asl
        JOIN ACTUATOR a ON asl.actuator_id = a.actuator_id
        JOIN ACTUATOR_TYPE at ON a.actuator_type_id = at.actuator_type_id
        WHERE a.room_id = %s
        AND asl.changed_time = (
            SELECT MAX(asl2.changed_time) FROM ACTUATOR_STATE_LOG asl2 WHERE asl2.actuator_id = asl.actuator_id
        )
        ORDER BY a.actuator_id
        """,
        (room_id,),
    )
    return render_template("room.html", room=room[0], sensors=sensors, actuators=actuators)

@app.route("/api/room/<int:room_id>/temperature-history")
def temperature_history(room_id):
    rows = fetch_all(
        """
        SELECT DATE_FORMAT(sr.measured_time, '%%H:%%i:%%s') AS label, sr.measured_value AS value
        FROM SENSOR_READING sr
        JOIN SENSOR s ON sr.sensor_id = s.sensor_id
        JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
        WHERE s.room_id = %s AND st.type_name = 'temperature'
        ORDER BY sr.measured_time DESC
        LIMIT 20
        """,
        (room_id,),
    )
    rows.reverse()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
