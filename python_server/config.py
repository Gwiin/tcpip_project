import os

DB_CONFIG = {
    "host": os.getenv("HOME_MANAGER_DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("HOME_MANAGER_DB_PORT", "3306")),
    "user": os.getenv("HOME_MANAGER_DB_USER", "root"),
    "password": os.getenv("HOME_MANAGER_DB_PASSWORD", ""),
    "database": os.getenv("HOME_MANAGER_DB_NAME", "Home_Manager"),
}

TCP_HOST = os.getenv("HOME_MANAGER_TCP_HOST", "0.0.0.0")
TCP_PORT = int(os.getenv("HOME_MANAGER_TCP_PORT", "4242"))
