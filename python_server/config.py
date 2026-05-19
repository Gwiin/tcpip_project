import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "163.152.213.111"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DB", "Home_Manager"),
}

TCP_HOST = os.getenv("HOME_MANAGER_TCP_HOST", "0.0.0.0")
TCP_PORT = int(os.getenv("HOME_MANAGER_TCP_PORT", "4242"))
