#!/usr/bin/env python3
"""
Протокол үүсгэх системийг тестлэх скрипт (SLM-ONLY режим)
"""

import json
import sys
from pathlib import Path

# Локал модулиудыг import хийх
sys.path.insert(0, str(Path(__file__).parent))

from app.preprocess import clean_text, extract_entities
from app.exporter import export_enhanced_protocol
from datetime import date

# SLM-only imports
try:
    from app.summarizer import SLMOnlySummarizer
    from app.action_extractor import SLMOnlyActionExtractor
    SLM_AVAILABLE = True
except ImportError as e:
    print(f"❌ SLM модулиуд import хийгдсэнгүй: {e}")
    SLM_AVAILABLE = False

# UDPipe (optional)
try:
    from app.nlp_processor import MongolianNLPProcessor
    nlp_processor = MongolianNLPProcessor("mn_model.udpipe")
    print("✓ UDPipe модель ачаалагдлаа")
except Exception as e:
    print(f"⚠ UDPipe ачаалагдсангүй: {e}")
    print("  Rule-based extraction ашиглана")
    nlp_processor = None


def test_with_json_file(json_path: str = "text.json"):
    """
    text.json файлаас текст уншиж протокол үүсгэх (SLM-ONLY)
    """
    print("\n" + "="*60)
    print("ПРОТОКОЛ ҮҮСГЭХ СИСТЕМ ТЕСТ (SLM-ONLY)")
    print("="*60 + "\n")
    
    # SLM шалгах
    if not SLM_AVAILABLE:
        print("❌ SLM модулиуд байхгүй!")
        print("\nШаардлагатай файлууд үүсгэх:")
        print("  1. app/summarizer.py")
        print("  2. app/action_extractor.py")
        return
    
    # 1. JSON файл уншах
    print("1️⃣  JSON файл уншиж байна...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        raw_text = data.get('text', '')
        
        if not raw_text:
            print("❌ Текст хоосон байна!")
            return
        
        print(f"   ✓ Анхны текст: {len(raw_text)} тэмдэгт")
        print(f"   Эхний 100 тэмдэгт: {raw_text[:100]}...")
        
    except FileNotFoundError:
        print(f"❌ {json_path} файл олдсонгүй!")
        return
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing алдаа: {e}")
        return
    
    # 2. Текст цэвэрлэх
    print("\n2️⃣  Текст цэвэрлэж байна...")
    cleaned_text = clean_text(raw_text)
    print(f"   ✓ Цэвэрлэсэн текст: {len(cleaned_text)} тэмдэгт")
    
    # 3. Нэр илрүүлэх
    print("\n3️⃣  Нэр, байгууллага илрүүлж байна...")
    if nlp_processor:
        try:
            nlp_result = nlp_processor.process_text(cleaned_text)
            entities = nlp_processor.extract_named_entities(nlp_result)
            print(f"   ✓ UDPipe: {len(entities)} нэр олсон")
        except Exception as e:
            print(f"   ⚠ UDPipe алдаа: {e}, rule-based ашиглана")
            entities = extract_entities(cleaned_text)
    else:
        entities = extract_entities(cleaned_text)
        print(f"   ✓ Rule-based: {len(entities)} нэр олсон")
    
    if entities:
        print(f"   Олсон нэрс: {', '.join(entities[:10])}")
    else:
        print(f"   ⚠️  Нэр олдсонгүй")
    
    # 4. SLM эхлүүлэх
    print("\n4️⃣  SLM систем эхлүүлж байна...")
    try:
        summarizer = SLMOnlySummarizer(model="qwen2.5:7b")
        action_extractor = SLMOnlyActionExtractor(nlp_processor)
        print("   ✅ SLM бэлэн")
    except RuntimeError as e:
        print(f"\n❌ SLM ЭХЛҮҮЛЭХ АЛДАА:")
        print(f"{e}")
        print("\n❌ ТЕСТ ЗОГССОН - SLM ажиллахгүй байна")
        return
    
    # 5. Албан хэл болгох
    print("\n5️⃣  Ярианы хэлийг албан протокол болгож байна...")
    print("   (SLM ашиглаж байгаа тул удаан болж магадгүй)")
    
    try:
        formalized_text = summarizer.formalize_text(cleaned_text)
        
        print(f"   ✅ Амжилттай: {len(formalized_text)} тэмдэгт")
        print(f"   Үр дүнгийн эхлэл:\n")
        print("   " + "-"*56)
        for line in formalized_text[:300].split('\n')[:5]:
            print(f"   {line}")
        print("   " + "-"*56)
        
    except RuntimeError as e:
        print(f"\n❌ АЛБАН ХЭЛ БОЛГОХ АЛДАА:")
        print(f"{e}")
        print("\n❌ ТЕСТ ЗОГССОН")
        return
    
    # 6. Action items гаргах
    print("\n6️⃣  Ажил үүрэг, шийдвэрүүдийг илрүүлж байна...")
    
    try:
        actions = action_extractor.extract_actions_with_llm(cleaned_text)
        
        print(f"   ✅ {len(actions)} ажил үүрэг/шийдвэр олсон\n")
        
        for i, action in enumerate(actions[:5], 1):
            print(f"   {i}. {action.get('who', '?')}: {action.get('action', '')[:50]}...")
            print(f"      Хугацаа: {action.get('due', 'Тодорхойгүй')}")
        
        if len(actions) > 5:
            print(f"   ... болон бусад {len(actions) - 5}")
        
    except RuntimeError as e:
        print(f"\n❌ АЖИЛ ҮҮРЭГ ИЛРҮҮЛЭХ АЛДАА:")
        print(f"{e}")
        print("\n❌ ТЕСТ ЗОГССОН")
        return
    
    # 7. Протокол бүтэц үүсгэх
    print("\n7️⃣  Протокол бүтэц үүсгэж байна...")
    
    protocol = {
        "title": "Хурлын протокол",
        "date": str(date.today()),
        "participants": entities if entities else ["Тодорхойгүй"],
        "body": formalized_text,
        "action_items": actions,
        "entities": entities,
        "metadata": {
            "original_text_length": len(raw_text),
            "formalized_text_length": len(formalized_text),
            "mode": "SLM-only",
            "model": "qwen2.5:7b"
        }
    }
    
    print(f"   ✓ Протокол бэлэн:")
    print(f"      - Гарчиг: {protocol['title']}")
    print(f"      - Огноо: {protocol['date']}")
    print(f"      - Оролцогчид: {len(protocol['participants'])} хүн")
    print(f"      - Ажил үүрэг: {len(protocol['action_items'])} ширхэг")
    print(f"      - Режим: SLM-only (Fallback байхгүй)")
    
    # 8. DOCX файл үүсгэх
    print("\n8️⃣  DOCX файл үүсгэж байна...")
    
    try:
        filename = export_enhanced_protocol(protocol)
        print(f"   ✓ Амжилттай: {filename}")
        
        # Файлын хэмжээ
        file_size = Path(filename).stat().st_size
        print(f"   Файлын хэмжээ: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
    except Exception as e:
        print(f"   ❌ DOCX үүсгэхэд алдаа: {e}")
        return
    
    # 9. Дүгнэлт
    print("\n" + "="*60)
    print("✅ ТЕСТ АМЖИЛТТАЙ ДУУСЛАА!")
    print("="*60)
    print(f"\n📄 Протокол файл: {filename}")
    print(f"\n📊 Статистик:")
    print(f"   - Режим: SLM-only (qwen2.5:7b)")
    print(f"   - Анхны текст: {len(raw_text)} тэмдэгт")
    print(f"   - Боловсруулсан: {len(formalized_text)} тэмдэгт")
    print(f"   - Хураангуйлалт: {(1 - len(formalized_text)/len(raw_text))*100:.1f}%")
    print(f"   - Олсон нэрс: {len(entities)}")
    print(f"   - Ажил үүрэг: {len(actions)}")
    print(f"\n💡 Санамж: SLM fallback байхгүй - алдаа гарвал шууд зогсоно\n")


def show_usage():
    """
    Хэрэглэх заавар
    """
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     МОНГОЛ ПРОТОКОЛ ҮҮСГЭХ СИСТЕМ (SLM-ONLY РЕЖИМ)            ║
╚═══════════════════════════════════════════════════════════════╝

Хэрэглэх арга:

1. JSON файлаас протокол үүсгэх:
   python test_protocol.py text.json

2. API server эхлүүлэх:
   uvicorn app.main:app --reload

3. API тестлэх:
   curl -X POST http://localhost:8000/generate_protocol \\
        -H "Content-Type: application/json" \\
        -d @text.json

4. SLM төлөв шалгах:
   curl http://localhost:8000/health

═══════════════════════════════════════════════════════════════

⚠️  ЧУХАЛ: SLM-ONLY режим
   - Fallback БАЙХГҮЙ
   - SLM ажиллахгүй бол ЗОГСОНО
   - Rule-based backup БАЙХГҮЙ

Шаардлагатай:
   ✓ Python 3.8+
   ✓ Ollama суулгасан + ажиллаж байгаа
   ✓ qwen2.5:7b model татсан
   ✓ requirements.txt-ийн сангууд

SLM бэлдэх:
   1. ollama serve
   2. ollama pull qwen2.5:7b
   3. python test_protocol.py

═══════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg in ['-h', '--help', 'help']:
            show_usage()
        else:
            # JSON файлын зам дамжуулсан
            test_with_json_file(arg)
    else:
        # Default: text.json ашиглах
        test_with_json_file("text.json")