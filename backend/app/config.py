import os
from pathlib import Path
import yaml
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class AppConfig(BaseModel):
    app_name: str = "FahamCeramah"
    app_version: str = "1.0.0"
    database_path: str = str(BASE_DIR / "data" / "database" / "fahamceramah.db")
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    default_model: str = "gemini-3.5-flash"
    fallback_model: str = "gemini-3.1-flash-lite"

def load_config() -> AppConfig:
    config_file = BASE_DIR / "config" / "application.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return AppConfig(**data)
    return AppConfig()

config = load_config()
