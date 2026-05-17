"""
실제 Pico 2 W 없이도 전체 시스템을 시험해보기 위한 시뮬레이터.

이 파일은 PC 안에서 Pico 3대를 흉내 낸다.
- 거실 Pico
- 안방 Pico
- 주방 Pico

각 가짜 Pico는 5초마다 TCP 서버로 랜덤 더미 데이터를 보낸다.
"""

import json
import random
import socket
import threading
import time


# 로컬 PC에서 실행 중인 TCP 서버로 접속한다.
# 실제 Pico를 사용할 때는 C 코드의 TEST_TCP_SERVER_IP가 PC의 IP 주소를 가리키게 된다.
HOST = "127.0.0.1"
PORT = 4242
SEND_INTERVAL_SECONDS = 5


def send_loop(device_id, builder):
    """
    하나의 가짜 Pico가 반복적으로 데이터를 보내는 루프.

    builder 함수는 각 방에 맞는 더미 payload를 생성한다.
    """
    with socket.create_connection((HOST, PORT)) as sock:
        while True:
            payload = builder()

            # 실제 Pico 코드와 동일하게 JSON 한 줄 형식으로 전송한다.
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))

            # 서버가 정상 수신했는지 확인하기 위해 간단한 응답을 읽는다.
            response = sock.recv(1024).decode("utf-8").strip()
            print(device_id, response)

            time.sleep(SEND_INTERVAL_SECONDS)


def living_room_payload():
    """거실 Pico가 보낼 더미 데이터."""
    return {
        "device_id": "pico_living_room",
        "sensors": {
            "temperature": round(random.uniform(20, 29), 1),
            "humidity": round(random.uniform(35, 70), 1),
            "light": round(random.uniform(100, 700), 1),
        },
        "actuators": {
            "light": random.choice(["ON", "OFF"]),
            "air_conditioner": random.choice(["OFF", "COOLING", "HEATING"]),
            "curtain": random.choice(["OPEN", "CLOSE"]),
        },
    }


def bedroom_payload():
    """안방 Pico가 보낼 더미 데이터."""
    return {
        "device_id": "pico_bedroom",
        "sensors": {
            "temperature": round(random.uniform(19, 27), 1),
            "humidity": round(random.uniform(35, 65), 1),
        },
        "actuators": {
            "light": random.choice(["ON", "OFF"]),
            "air_conditioner": random.choice(["OFF", "COOLING", "HEATING"]),
        },
    }


def kitchen_payload():
    """주방 Pico가 보낼 더미 데이터."""
    return {
        "device_id": "pico_kitchen",
        "sensors": {
            "temperature": round(random.uniform(21, 31), 1),
            "motion": random.choice([0, 1]),
        },
        "actuators": {
            "light": random.choice(["ON", "OFF"]),
            "fan": random.choice(["ON", "OFF"]),
        },
    }


if __name__ == "__main__":
    # 실제 Pico 3대처럼 각각 별도의 스레드에서 동시에 동작시킨다.
    jobs = [
        ("pico_living_room", living_room_payload),
        ("pico_bedroom", bedroom_payload),
        ("pico_kitchen", kitchen_payload),
    ]

    for device_id, builder in jobs:
        threading.Thread(
            target=send_loop,
            args=(device_id, builder),
            daemon=True,
        ).start()

    # 메인 스레드가 끝나면 daemon 스레드도 같이 종료되므로 계속 살아 있게 유지한다.
    while True:
        time.sleep(1)
