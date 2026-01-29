"""Configuration loader for the platform."""

import os
from pathlib import Path

import toml


def load_config() -> dict:
    """Load configuration from config.toml file."""
    # Look for config.toml in the platform directory
    config_paths = [
        Path(__file__).parent.parent / "config.toml",
        Path("/app/config.toml"),
        Path("config.toml"),
    ]

    config_path = None
    for path in config_paths:
        if path.exists():
            config_path = path
            break

    if config_path is None:
        raise FileNotFoundError("config.toml not found")

    config = toml.load(config_path)

    # Allow environment variable overrides
    if os.environ.get("DATABASE_HOST"):
        config["database"]["host"] = os.environ["DATABASE_HOST"]
    if os.environ.get("DATABASE_PORT"):
        config["database"]["port"] = int(os.environ["DATABASE_PORT"])
    if os.environ.get("DATABASE_NAME"):
        config["database"]["name"] = os.environ["DATABASE_NAME"]
    if os.environ.get("DATABASE_USER"):
        config["database"]["user"] = os.environ["DATABASE_USER"]
    if os.environ.get("DATABASE_PASSWORD"):
        config["database"]["password"] = os.environ["DATABASE_PASSWORD"]
    if os.environ.get("SECRET_KEY"):
        config["server"]["secret_key"] = os.environ["SECRET_KEY"]

    return config


def get_database_url(config: dict = None) -> str:
    """Get the database URL from config."""
    if config is None:
        config = load_config()

    db = config["database"]
    return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['name']}"
