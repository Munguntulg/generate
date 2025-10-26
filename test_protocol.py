#!/usr/bin/env python3
"""
Протокол үүсгэх системийг тестлэх скрипт
"""

import json
import sys
from pathlib import Path

# Локал модулиудыг import хийх
sys.path.insert(0, str(Path(__file__).parent))

from app.preprocess import clean_text, extract_entities
from app.summarizer import OllamaSummarizer
from app.action_extractor import ActionItemExtractor
from app.exporter import export_enhanced_protocol
from datetime import date

# Опционал: UDPipe
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
    text.json файлаас текст уншиж протокол үүсгэх
    """
    print("\n" + "="*60)
    print("ПРОТОКОЛ ҮҮСГЭХ СИСТЕМ ТЕСТ")
    print("="*60 + "\n")
    
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
    print(f"   Эхний 100 тэмдэгт: {cleaned_text[:100]}...")
    
    # 3. Нэр, байгууллага илрүүлэх
    print("\n3️⃣  Нэр, байгууллага илрүүлж байна...")
    
    if nlp_processor:
        try:
            nlp_result = nlp_processor.process_text(cleaned_text)
            entities = nlp_processor.extract_named_entities(nlp_result)
            print(f"   ✓ UDPipe ашиглаж {len(entities)} нэр олсон")
        except Exception as e:
            print(f"   ⚠ UDPipe алдаа: {e}, rule-based ашиглана")
            entities = extract_entities(cleaned_text)
    else:
        entities = extract_entities(cleaned_text)
        print(f"   ✓ Rule-based: {len(entities)} нэр олсон")
    
    print(f"   Олсон нэрс: {', '.join(entities[:10])}")
    
    # 4. SLM ашиглан албан хэлбэрт хөрвүүлэх
    print("\n4️⃣  Ярианы хэлийг албан бичгийн хэл рүү хөрвүүлж байна...")
    print("   (Энэ хэсэг Ollama-д хамаарч удаан болж магадгүй)")
    
    try:
        summarizer = OllamaSummarizer()
        formalized_text = summarizer.formalize_text(cleaned_text)
        
        print(f"   ✓ Амжилттай хөрвүүллээ: {len(formalized_text)} тэмдэгт")
        print(f"   Үр дүнгийн эхлэл:\n   {formalized_text[:200]}...")
        
    except Exception as e:
        print(f"   ❌ Ollama алдаа: {e}")
        print("   Цэвэрлэсэн текстийг хэрэглэнэ")
        formalized_text = cleaned_text
    
    # 5. Action items гаргах
    print("\n5️⃣  Ажил үүрэг, шийдвэрүүдийг илрүүлж байна...")
    
    try:
        action_extractor = ActionItemExtractor(nlp_processor)
        actions = action_extractor.extract_actions_with_llm(cleaned_text)
        
        print(f"   ✓ {len(actions)} ажил үүрэг/шийдвэр олсон")
        
        for i, action in enumerate(actions[:5], 1):
            print(f"   {i}. {action.get('who', '?')}: {action.get('action', '')[:50]}...")
        
        if len(actions) > 5:
            print(f"   ... болон бусад {len(actions) - 5}")
        
    except Exception as e:
        print(f"   ❌ Action extraction алдаа: {e}")
        actions = []
    
    # 6. Протокол бүтэц үүсгэх
    print("\n6️⃣  Протокол бүтэц үүсгэж байна...")
    
    protocol = {
        "title": "Хурлын протокол",
        "date": str(date.today()),
        "participants": entities if entities else ["Тодорхойгүй"],
        "body": formalized_text,
        "action_items": actions,
        "entities": entities,
        "original_text_length": len(raw_text),
        "formalized_text_length": len(formalized_text)
    }
    
    print(f"   ✓ Протокол бэлэн:")
    print(f"      - Гарчиг: {protocol['title']}")
    print(f"      - Огноо: {protocol['date']}")
    print(f"      - Оролцогчид: {len(protocol['participants'])} хүн")
    print(f"      - Ажил үүрэг: {len(protocol['action_items'])} ширхэг")
    
    # 7. DOCX файл үүсгэх
    print("\n7️⃣  DOCX файл үүсгэж байна...")
    
    try:
        filename = export_enhanced_protocol(protocol)
        print(f"   ✓ Амжилттай: {filename}")
        
        # Файлын хэмжээ шалгах
        file_size = Path(filename).stat().st_size
        print(f"   Файлын хэмжээ: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
    except Exception as e:
        print(f"   ❌ DOCX үүсгэхэд алдаа: {e}")
        return
    
    # 8. Дүгнэлт
    print("\n" + "="*60)
    print("✅ ТЕСТ АМЖИЛТТАЙ ДУУСЛАА!")
    print("="*60)
    print(f"\n📄 Протокол файл: {filename}")
    print(f"📊 Статистик:")
    print(f"   - Анхны текст: {len(raw_text)} тэмдэгт")
    print(f"   - Боловсруулсан: {len(formalized_text)} тэмдэгт")
    print(f"   - Олсон нэрс: {len(entities)}")
    print(f"   - Ажил үүрэг: {len(actions)}")
    print("\n")


def test_simple_text():
    """
    Энгийн текст дээр богино тест
    """
    print("\n" + "="*60)
    print("ЭНГИЙН ТЕКСТ ТЕСТ")
    print("="*60 + "\n")
    
    test_text = """
    Анна: Би энэ долоо хоногт тайлан бэлдэх болно.
    Жон: Би шалгаж үзээд санал өгнө.
    Тогтоол: Баасан гараг бүх ажлыг дуусгах.
    """
    
    print(f"Тест текст:\n{test_text}\n")
    
    # Цэвэрлэх
    cleaned = clean_text(test_text)
    print(f"Цэвэрлэсэн: {cleaned}\n")
    
    # Нэр олох
    entities = extract_entities(test_text)
    print(f"Олсон нэрс: {entities}\n")
    
    # Action items
    try:
        action_extractor = ActionItemExtractor()
        actions = action_extractor.extract_actions_with_llm(test_text)
        print(f"Олсон action items: {len(actions)}")
        for action in actions:
            print(f"  - {action}")
    except Exception as e:
        print(f"Action extraction алдаа: {e}")


def show_usage():
    """
    Хэрэглэх заавар
    """
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           МОНГОЛ ПРОТОКОЛ ҮҮСГЭХ СИСТЕМ                       ║
╚═══════════════════════════════════════════════════════════════╝

Хэрэглэх арга:

1. JSON файлаас протокол үүсгэх:
   python test_protocol.py text.json

2. Энгийн тест ажиллуулах:
   python test_protocol.py --simple

3. API server эхлүүлэх:
   uvicorn app.main:app --reload

4. API тестлэх (server ажиллаж байхад):
   curl -X POST http://localhost:8000/generate_protocol \\
        -H "Content-Type: application/json" \\
        -d @text.json

═══════════════════════════════════════════════════════════════

Шаардлагатай зүйлс:
✓ Python 3.8+
✓ Ollama суулгасан (ollama pull mistral)
✓ mn_model.udpipe файл (опционал)
✓ requirements.txt-д байгаа сангууд

═══════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg in ['-h', '--help', 'help']:
            show_usage()
        elif arg in ['-s', '--simple']:
            test_simple_text()
        else:
            # JSON файлын зам дамжуулсан
            test_with_json_file(arg)
    else:
        # Default: text.json ашиглах
        test_with_json_file("text.json")