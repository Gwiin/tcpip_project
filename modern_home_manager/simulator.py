from __future__ import annotations

import argparse
import random
import time
from typing import Any

try:
    from modern_home_manager.database import DEFAULT_DB_PATH, initialize_database, record_device_frame
except ModuleNotFoundError:
    from database import DEFAULT_DB_PATH, initialize_database, record_device_frame


DEVICE_PROFILES: dict[str, dict[str, Any]] = {
    "pico_living_room": {
        "temperature": (22.5, 25.8),
        "humidity": (40, 58),
        "light": (220, 520),
        "dust": (8, 25),
        "co2": (430, 720),
        "actuators": ["living-light", "living-ac", "living-curtain"],
    },
    "pico_bedroom": {
        "temperature": (20.2, 23.8),
        "humidity": (42, 60),
        "light": (40, 180),
        "actuators": ["bedroom-light", "bedroom-ac"],
    },
    "pico_kitchen": {
        "temperature": (23.0, 27.5),
        "humidity": (38, 55),
        "light": (180, 460),
        "actuators": ["kitchen-fan", "kitchen-plug"],
    },
}


def build_frame(device_id: str) -> dict[str, Any]:
    profile = DEVICE_PROFILES[device_id]
    sensors = {
        name: round(random.uniform(*bounds), 1)
        for name, bounds in profile.items()
        if name != "actuators"
    }
    actuators = {
        actuator_id: random.choice([True, False])
        for actuator_id in profile["actuators"]
        if random.random() < 0.35
    }
    return {"device_id": device_id, "sensors": sensors, "actuators": actuators}


def run_simulator(interval: float, once: bool) -> None:
    initialize_database(DEFAULT_DB_PATH)
    print(f"Simulator writing to: {DEFAULT_DB_PATH}")
    while True:
        for device_id in DEVICE_PROFILES:
            frame = build_frame(device_id)
            record_device_frame(DEFAULT_DB_PATH, frame)
            print(f"[sim] {device_id}: {frame}")
        if once:
            break
        time.sleep(interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Modern Home Manager SQLite simulator")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between frames")
    parser.add_argument("--once", action="store_true", help="write one batch and exit")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_simulator(interval=args.interval, once=args.once)
