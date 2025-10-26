"""
Mongolian Protocol Generator

Ярианы хэлбэрийн текстийг албан протокол болгон хөрвүүлэх систем.
"""

__version__ = "1.0.0"
__author__ = "Protocol Generator Team"

# Модулиудыг экспорт хийх
from .preprocess import clean_text, extract_entities
from .exporter import export_protocol, export_enhanced_protocol

try:
    from .nlp_processor import MongolianNLPProcessor
except ImportError:
    MongolianNLPProcessor = None

try:
    from .summarizer import OllamaSummarizer
except ImportError:
    OllamaSummarizer = None

try:
    from .action_extractor import ActionItemExtractor
except ImportError:
    ActionItemExtractor = None

__all__ = [
    "clean_text",
    "extract_entities",
    "export_protocol",
    "export_enhanced_protocol",
    "MongolianNLPProcessor",
    "OllamaSummarizer",
    "ActionItemExtractor",
]