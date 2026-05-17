"""
Pico 2 W에서 들어오는 TCP 데이터를 받아 MySQL에 저장하는 서버.

통신 방식:
- Pico는 JSON 문자열 한 줄을 전송한다.
- 서버는 한 줄씩 읽어 JSON으로 변환한다.
- device_id를 기준으로 실제 sensor_id / actuator_id를 찾는다.
- 센서값과 액추에이터 상태를 각각 로그 테이블에 저장한다.
"""

import json
import socketserver
from datetime import datetime

from config import TCP_HOST, TCP_PORT
from db import execute_many


# 각 Pico가 담당하는 센서 이름을 DB의 sensor_id와 연결한다.
# 예:
# "pico_living_room" 장치가 보낸 "temperature" 값은 SENSOR 테이블의 sensor_id=1에 저장된다.
DEVICE_SENSOR_MAP = {
    "pico_living_room": {"temperature": 1, "humidity": 2, "light": 3},
    "pico_bedroom": {"temperature": 4, "humidity": 5},
    "pico_kitchen": {"temperature": 6, "motion": 7},
}

# 각 Pico가 담당하는 액추에이터 이름을 DB의 actuator_id와 연결한다.
DEVICE_ACTUATOR_MAP = {
    "pico_living_room": {"light": 1, "air_conditioner": 2, "curtain": 3},
    "pico_bedroom": {"light": 4, "air_conditioner": 5},
    "pico_kitchen": {"light": 6, "fan": 7},
}


class PicoRequestHandler(socketserver.StreamRequestHandler):
    """
    하나의 TCP 클라이언트 연결을 처리하는 클래스.

    실제 Pico 한 대가 연결되면 이 핸들러가 그 연결을 맡는다.
    """

    def handle(self):
        """클라이언트가 연결되어 있는 동안 한 줄씩 계속 읽는다."""
        peer = f"{self.client_address[0]}:{self.client_address[1]}"
        print(f"[TCP] connected: {peer}")

        while True:
            # Pico는 JSON 뒤에 개행 문자(\n)를 붙여 보내므로 readline()으로 한 메시지씩 읽을 수 있다.
            raw = self.rfile.readline()
            if not raw:
                break

            try:
                payload = json.loads(raw.decode("utf-8"))
                self.save_payload(payload)
                self.wfile.write(b'{"status":"ok"}\n')
            except Exception as exc:
                print(f"[TCP] invalid payload from {peer}: {exc}")
                self.wfile.write(b'{"status":"error"}\n')

        print(f"[TCP] disconnected: {peer}")

    def save_payload(self, payload):
        """
        Pico가 보낸 JSON 데이터를 DB 저장용 INSERT 문으로 바꾼다.

        payload 예시:
        {
            "device_id": "pico_living_room",
            "sensors": {"temperature": 24.3, "humidity": 48.2},
            "actuators": {"light": "ON"}
        }
        """
        device_id = payload["device_id"]

        # 등록되지 않은 장치가 보내는 데이터는 저장하지 않는다.
        if device_id not in DEVICE_SENSOR_MAP:
            raise ValueError(f"unknown device_id: {device_id}")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        statements = []

        # 센서 데이터는 SENSOR_READING 로그 테이블에 저장한다.
        for sensor_type, value in payload.get("sensors", {}).items():
            sensor_id = DEVICE_SENSOR_MAP[device_id].get(sensor_type)
            if sensor_id is None:
                continue

            statements.append(
                (
                    "INSERT INTO SENSOR_READING (sensor_id, measured_value, measured_time) VALUES (%s, %s, %s)",
                    (sensor_id, value, now),
                )
            )

        # 액추에이터 상태는 ACTUATOR_STATE_LOG 로그 테이블에 저장한다.
        for actuator_type, state in payload.get("actuators", {}).items():
            actuator_id = DEVICE_ACTUATOR_MAP[device_id].get(actuator_type)
            if actuator_id is None:
                continue

            statements.append(
                (
                    "INSERT INTO ACTUATOR_STATE_LOG (actuator_id, state_value, changed_time) VALUES (%s, %s, %s)",
                    (actuator_id, state, now),
                )
            )

        # 센서와 액추에이터 값을 한 번의 DB 연결 안에서 함께 저장한다.
        if statements:
            execute_many(statements)
            print(f"[TCP] saved {device_id}: {payload}")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    여러 Pico가 동시에 연결되어도 처리할 수 있는 TCP 서버.

    ThreadingMixIn 덕분에 각 연결을 별도 스레드에서 처리한다.
    """

    allow_reuse_address = True


if __name__ == "__main__":
    with ThreadedTCPServer((TCP_HOST, TCP_PORT), PicoRequestHandler) as server:
        print(f"[TCP] listening on {TCP_HOST}:{TCP_PORT}")
        server.serve_forever()
