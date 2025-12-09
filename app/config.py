"""
Системийн тохиргоо - FINE-TUNED MODEL ашиглах
"""

import os
from pathlib import Path

# Үндсэн директор
BASE_DIR = Path(__file__).parent.parent

# ============================================
# SLM ТОХИРГОО - FINE-TUNED MODEL
# ============================================

# АНХНЫ: qwen2.5:7b
# FINE-TUNED: mongolian-protocol (таны fine-tune хийсэн model)
USE_FINETUNED = os.getenv("USE_FINETUNED", "true").lower() == "true"

if USE_FINETUNED:
    SLM_MODEL = "mongolian-protocol"
    print("✅ Fine-tuned model ашиглаж байна: mongolian-protocol")
else:
    SLM_MODEL = os.getenv("SLM_MODEL", "qwen2.5:7b")
    print(f"⚠️  Base model ашиглаж байна: {SLM_MODEL}")

# Fine-tuned model-д ИЛҮҮ БАГ temperature хэрэгтэй
# Учир нь model аль хэдийн fine-tune хийгдсэн
SLM_TEMPERATURE = float(os.getenv("SLM_TEMPERATURE", "0.05" if USE_FINETUNED else "0.1"))
SLM_MAX_TOKENS = int(os.getenv("SLM_MAX_TOKENS", "2000"))
SLM_TOP_P = float(os.getenv("SLM_TOP_P", "0.9"))
SLM_REPEAT_PENALTY = float(os.getenv("SLM_REPEAT_PENALTY", "1.1"))

# ============================================
# PROMPT ТОХИРГОО
# ============================================

# Fine-tuned model-д БОГИНО prompt хэрэгтэй
# Учир нь model-д аль хэдийн дүрэм сургасан
USE_SIMPLIFIED_PROMPTS = USE_FINETUNED

# ============================================
# БУСАД ТОХИРГОО
# ============================================

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
            "is_finetuned": USE_FINETUNED,
            "temperature": SLM_TEMPERATURE,
            "max_tokens": SLM_MAX_TOKENS,
            "top_p": SLM_TOP_P,
            "repeat_penalty": SLM_REPEAT_PENALTY,
            "simplified_prompts": USE_SIMPLIFIED_PROMPTS,
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
                # Fine-tuned model бол тэмдэглэх
                if key == "model" and values.get("is_finetuned"):
                    print(f"  {key}: {value} ⭐ (Fine-tuned)")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {values}")
    
    print("="*60 + "\n")


# Fine-tuned prompt templates
SIMPLIFIED_SYSTEM_PROMPT = """Ярианы хэлийг албан хэл болго.

Дүрэм:
1. Агуулга өөрчлөхгүй
2. Хэллэг үгс арилга
3. Үйл үг албан хэл болго"""

SIMPLIFIED_USER_PROMPT = """Энэ текстийг албан протокол болго:

{text}

Зөвхөн албан хувилбар:"""

# Original (verbose) prompts
VERBOSE_SYSTEM_PROMPT = """Та протоколоос ярианы хэлийг албан хэл болгодог мэргэжилтэн.

🎯 ХАМГИЙН ЧУХАЛ: АГУУЛГА ӨӨРЧЛӨХГҮЙ
- Нэр → нэр (яг хуулах)
- Огноо → огноо (яг хуулах)
- Ажил → ажил (яг хуулах)

📝 ЯРИАНЫ МАЯГ → АЛБАН МАЯГ:
1. Хэллэг үгс АРИЛГА (шүү дээ, л байх даа)
2. Үйл үг албан хэл болго (хийх → гүйцэтгэх)
3. Зөв бичгийн дүрэм дагах

⚠️ ХОРИОТОЙ:
- Нэр солихгүй
- Огноо өөрчлөхгүй
- Утгагүй үг БАЙХГҮЙ
- Англи хэл БАЙХГҮЙ

Зөвхөн JSON array буцаа."""

VERBOSE_USER_PROMPT = """Энэ ярианы бичлэгийг албан протокол болго. АГУУЛГА ӨӨРЧЛӨХГҮЙ.

ЯРИАНЫ БИЧЛЭГ:
{text}

ЗӨВХӨН албан маяг бич. Агуулга бүрэн хадгал."""


def get_prompts(use_simplified: bool = None):
    """
    Prompt templates авах
    
    Args:
        use_simplified: Simplified prompts ашиглах уу?
                       None бол USE_SIMPLIFIED_PROMPTS ашиглана
    """
    if use_simplified is None:
        use_simplified = USE_SIMPLIFIED_PROMPTS
    
    if use_simplified:
        return SIMPLIFIED_SYSTEM_PROMPT, SIMPLIFIED_USER_PROMPT
    else:
        return VERBOSE_SYSTEM_PROMPT, VERBOSE_USER_PROMPT