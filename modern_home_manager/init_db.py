from __future__ import annotations

try:
    from modern_home_manager.database import DEFAULT_DB_PATH, initialize_database
except ModuleNotFoundError:
    from database import DEFAULT_DB_PATH, initialize_database


def main() -> None:
    initialize_database(DEFAULT_DB_PATH)
    print(f"Initialized database: {DEFAULT_DB_PATH}")


if __name__ == "__main__":
    main()
