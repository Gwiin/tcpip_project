from __future__ import annotations

try:
    from modern_home_manager.database import initialize_database
except ModuleNotFoundError:
    from database import initialize_database


def main() -> None:
    initialize_database()
    print("MySQL connection OK. Paste modern_home_manager/mysql_queries.sql first if tables are missing.")


if __name__ == "__main__":
    main()
