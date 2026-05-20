from __future__ import annotations

import argparse
import random
import time
from typing import Any

try:
    from modern_home_manager.database import initialize_database, record_device_frame
except ModuleNotFoundError:
    from database import initialize_database, record_device_frame


DEVICE_PROFILES: dict[str, dict[str, Any]] = {
    "pico_living_room": {
        "sensors": {
            "temperature": (20.0, 29.0),
            "humidity": (35.0, 70.0),
            "light": (100.0, 700.0),
        },
        "actuators": {
            "light": ["ON", "OFF"],
            "air_conditioner": ["OFF", "COOLING", "HEATING"],
            "curtain": ["OPEN", "CLOSED"],
        },
    },
    "pico_bedroom": {
        "sensors": {
            "temperature": (19.0, 27.0),
            "humidity": (35.0, 65.0),
        },
        "actuators": {
            "light": ["ON", "OFF"],
            "air_conditioner": ["OFF", "COOLING", "HEATING"],
        },
    },
    "pico_kitchen": {
        "sensors": {
            "temperature": (21.0, 31.0),
            "motion": (0, 1),
        },
        "actuators": {
            "light": ["ON", "OFF"],
            "fan": ["ON", "OFF"],
        },
    },
}


def random_sensor_value(bounds: tuple[float, float]) -> float:
    if bounds == (0, 1):
        return float(random.choice([0, 1]))
    return round(random.uniform(*bounds), 1)


def build_frame(device_id: str) -> dict[str, Any]:
    profile = DEVICE_PROFILES[device_id]
    return {
        "device_id": device_id,
        "sensors": {
            sensor_type: random_sensor_value(bounds)
            for sensor_type, bounds in profile["sensors"].items()
        },
        "actuators": {
            actuator_type: random.choice(states)
            for actuator_type, states in profile["actuators"].items()
        },
    }


def run_simulator(interval: float, once: bool) -> None:
    initialize_database()
    print("Simulator writing Pico frames to MySQL")
    while True:
        for device_id in DEVICE_PROFILES:
            frame = build_frame(device_id)
            record_device_frame(frame)
            print(f"[sim] {device_id}: {frame}")
        if once:
            break
        time.sleep(interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Modern Home Manager MySQL Pico simulator")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between frames")
    parser.add_argument("--once", action="store_true", help="write one batch and exit")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_simulator(interval=args.interval, once=args.once)
