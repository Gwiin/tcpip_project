import os

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "163.152.213.111")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", "3306"))
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "Home_Manager")

TCP_HOST = os.getenv("HOME_MANAGER_TCP_HOST", "0.0.0.0")
TCP_PORT = int(os.getenv("HOME_MANAGER_TCP_PORT", "4242"))


def get_connection():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        port=app.config["MYSQL_PORT"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DB"],
    )


def fetch_all(query, params=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def execute(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()


def execute_many(statements):
    conn = get_connection()
    cur = conn.cursor()
    for query, params in statements:
        cur.execute(query, params)
    conn.commit()
    cur.close()
    conn.close()


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
SELECT u.user_name, COALESCE(r.room_name, '\uc704\uce58 \uc5c6\uc74c') AS current_location
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


def is_logged_in():
    return "user_id" in session


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/register_page")
def register_page():
    return render_template("register.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    password = data.get("password")

    if not name or not password:
        return jsonify({"success": False, "message": "사용자명과 비밀번호를 입력해주세요."}), 400

    rows = fetch_all(
        "SELECT user_id, user_name, pw FROM `USER` WHERE user_name = %s",
        (name,),
    )

    if not rows or not check_password_hash(rows[0]["pw"], password):
        return jsonify({"success": False, "message": "사용자명 또는 비밀번호가 올바르지 않습니다."}), 401

    session["user_id"] = rows[0]["user_id"]
    session["user_name"] = rows[0]["user_name"]
    return jsonify({"success": True, "message": "로그인 성공", "user_id": rows[0]["user_id"]})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    password = data.get("password")

    if not name or not password:
        return jsonify({"success": False, "message": "사용자명과 비밀번호를 입력해주세요."}), 400

    existing_user = fetch_all(
        "SELECT user_id FROM `USER` WHERE user_name = %s",
        (name,),
    )

    if existing_user:
        return jsonify({"success": False, "message": "이미 존재하는 사용자명입니다."}), 409

    try:
        execute(
            """
            INSERT INTO `USER` (user_id, role_id, user_name, pw)
            SELECT COALESCE(MAX(user_id), 0) + 1, %s, %s, %s
            FROM `USER`
            """,
            (3, name, generate_password_hash(password)),
        )
    except Exception as exc:
        return jsonify({"success": False, "message": f"회원가입 중 오류가 발생했습니다: {exc}"}), 500

    return jsonify({"success": True, "message": "회원가입이 완료되었습니다."})

@app.route("/dashboard")
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
    app.run(debug=True, port=5000, host="127.0.0.1")
