import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


@dataclass(frozen=True)
class AppSettings:
    flask_secret_key: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_db: str
    tcp_host: str
    tcp_port: int
    flask_host: str
    flask_port: int
    flask_debug: bool


def required_env(name):
    value = os.getenv(name)
    if value is None or value == "":
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def env_int(name, default):
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"Environment variable {name} must be an integer") from exc


def env_bool(name, default):
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ConfigError(f"Environment variable {name} must be a boolean")


def load_env():
    load_dotenv()


def load_settings(load_dotenv_file=True):
    if load_dotenv_file:
        load_env()

    return AppSettings(
        flask_secret_key=required_env("FLASK_SECRET_KEY"),
        mysql_host=required_env("MYSQL_HOST"),
        mysql_port=env_int("MYSQL_PORT", 3306),
        mysql_user=required_env("MYSQL_USER"),
        mysql_password=required_env("MYSQL_PASSWORD"),
        mysql_db=required_env("MYSQL_DB"),
        tcp_host=os.getenv("HOME_MANAGER_TCP_HOST", "0.0.0.0"),
        tcp_port=env_int("HOME_MANAGER_TCP_PORT", 4242),
        flask_host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
        flask_port=env_int("FLASK_RUN_PORT", 5000),
        flask_debug=env_bool("FLASK_DEBUG", True),
    )
