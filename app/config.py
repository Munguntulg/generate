"""
Системийн тохиргоо - Environment variables удирдах
"""

import os
from pathlib import Path

# Үндсэн директор
BASE_DIR = Path(__file__).parent.parent

# SLM тохиргоо
SLM_MODEL = os.getenv("SLM_MODEL", "qwen2.5:7b")
SLM_TEMPERATURE = float(os.getenv("SLM_TEMPERATURE", "0.1"))
SLM_MAX_TOKENS = int(os.getenv("SLM_MAX_TOKENS", "2000"))
SLM_TOP_P = float(os.getenv("SLM_TOP_P", "0.8"))
SLM_REPEAT_PENALTY = float(os.getenv("SLM_REPEAT_PENALTY", "1.1"))

# UDPipe
UDPIPE_MODEL_PATH = os.getenv("UDPIPE_MODEL", "mn_model.udpipe")

# Output
OUTPUT_DIR = os.getenv("OUTPUT_DIR", str(BASE_DIR))

# API тохиргоо
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"

# Debug
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Текст боловсруулалт
MAX_CHUNK_LENGTH = int(os.getenv("MAX_CHUNK_LENGTH", "1500"))

# Quality thresholds
MIN_TEXT_RATIO = float(os.getenv("MIN_TEXT_RATIO", "0.15"))
MAX_TEXT_RATIO = float(os.getenv("MAX_TEXT_RATIO", "8.0"))
MAX_ENGLISH_RATIO = float(os.getenv("MAX_ENGLISH_RATIO", "0.3"))


def get_config_dict() -> dict:
    """
    Бүх тохиргоог dictionary-ээр буцаах
    """
    return {
        "slm": {
            "model": SLM_MODEL,
            "temperature": SLM_TEMPERATURE,
            "max_tokens": SLM_MAX_TOKENS,
            "top_p": SLM_TOP_P,
            "repeat_penalty": SLM_REPEAT_PENALTY,
        },
        "udpipe": {
            "model_path": UDPIPE_MODEL_PATH,
        },
        "api": {
            "host": API_HOST,
            "port": API_PORT,
            "reload": API_RELOAD,
        },
        "processing": {
            "max_chunk_length": MAX_CHUNK_LENGTH,
            "min_ratio": MIN_TEXT_RATIO,
            "max_ratio": MAX_TEXT_RATIO,
            "max_english_ratio": MAX_ENGLISH_RATIO,
        },
        "output_dir": OUTPUT_DIR,
        "debug": DEBUG,
    }


def print_config():
    """
    Тохиргоог хэвлэх
    """
    config = get_config_dict()
    
    print("\n" + "="*60)
    print("СИСТЕМИЙН ТОХИРГОО")
    print("="*60)
    
    for section, values in config.items():
        print(f"\n[{section.upper()}]")
        if isinstance(values, dict):
            for key, value in values.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {values}")
    
    print("="*60 + "\n")