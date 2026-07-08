import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def get_env_int(key: str, default: int) -> int:
    val = os.environ.get(key)
    if val is None:
        return default
    return int(val)


def get_env_float(key: str, default: float) -> float:
    val = os.environ.get(key)
    if val is None:
        return default
    return float(val)


OLLAMA_HOST = get_env("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = get_env("OLLAMA_MODEL", "qwen3:8b-q4_K_M")
OLLAMA_TEMPERATURE = get_env_float("OLLAMA_TEMPERATURE", 0.5)
API_HOST = get_env("API_HOST", "0.0.0.0")
API_PORT = int(get_env("API_PORT", "8000"))

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERSONA_BASE_PATH = get_env("PERSONA_BASE_PATH", str(_PROJECT_ROOT / "persona_base.txt"))
PERSONA_SURVEY_PATH = get_env("PERSONA_SURVEY_PATH", str(_PROJECT_ROOT / "persona_survey.yaml"))

MAX_HISTORY_TURNS = get_env_int("MAX_HISTORY_TURNS", 10)
SESSION_IDLE_TTL_SECONDS = get_env_int("SESSION_IDLE_TTL_SECONDS", 3600)
