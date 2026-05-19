"""
실제 Pico 2 W 없이 전체 시스템을 시험해보기 위한 시뮬레이터.

이 파일은 PC 안에서 Pico 3대를 흉내 낸다.
- 거실 Pico
- 침실 Pico
- 주방 Pico

각 Pico는 5초마다 TCP 서버로 임의의 데이터를 보낸다.
"""

import json
import os
import random
import socket
import threading
import time

from config import env_int, load_env


load_env()
HOST = os.getenv("SIMULATOR_TCP_HOST", "127.0.0.1")
PORT = env_int("SIMULATOR_TCP_PORT", 4242)
SEND_INTERVAL_SECONDS = env_int("SIMULATOR_SEND_INTERVAL_SECONDS", 5)


def send_loop(device_id, builder):
    """하나의 가상 Pico가 반복적으로 데이터를 보내는 루프."""
    with socket.create_connection((HOST, PORT)) as sock:
        while True:
            payload = builder()
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))

            response = sock.recv(1024).decode("utf-8").strip()
            print(device_id, response)

            time.sleep(SEND_INTERVAL_SECONDS)


def living_room_payload():
    """거실 Pico가 보낼 임의 데이터."""
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
            "curtain": random.choice(["OPEN", "CLOSED"]),
        },
    }


def bedroom_payload():
    """침실 Pico가 보낼 임의 데이터."""
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
    """주방 Pico가 보낼 임의 데이터."""
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

    while True:
        time.sleep(1)
