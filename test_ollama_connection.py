#!/usr/bin/env python3
"""
Ollama SLM ажиллаж байгаа эсэхийг шалгах
"""

import sys

print("="*60)
print("OLLAMA SLM ХОЛБОЛТ ШАЛГАХ")
print("="*60 + "\n")

# 1. Ollama суулгасан эсэх
print("1️⃣  Ollama санг шалгаж байна...")
try:
    from ollama import chat
    print("   ✅ Ollama сан суулгасан байна\n")
except ImportError as e:
    print(f"   ❌ Ollama сан байхгүй!")
    print(f"   Суулгах: pip install ollama\n")
    sys.exit(1)

# 2. Ollama server ажиллаж байгаа эсэх
print("2️⃣  Ollama server холбогдож байна...")
try:
    # Энгийн тест хүсэлт
    response = chat(
        model='mistral',
        messages=[
            {'role': 'user', 'content': 'Сайн уу?'}
        ],
        options={'num_predict': 10}
    )
    print("   ✅ Ollama server ажиллаж байна")
    print(f"   Хариулт: {response['message']['content'][:50]}...\n")
    
except Exception as e:
    print(f"   ❌ Ollama server холбогдохгүй байна!")
    print(f"   Алдаа: {e}")
    print(f"\n   ШИЙДЭЛ:")
    print(f"   1. Terminal дээр Ollama эхлүүл: ollama serve")
    print(f"   2. Өөр terminal дээр: ollama pull mistral")
    print(f"   3. Дахин туршина уу\n")
    sys.exit(1)

# 3. Монгол хэл дээр тест
print("3️⃣  Монгол хэлний тест хийж байна...")

test_mongolian = """
Анна: Би энэ ажлыг даваа гарагт хийх болно шүү дээ.
Жон: За тэгээд би шалгаж үзье.
"""

print(f"   Анхны текст:\n   {test_mongolian.strip()}\n")

try:
    response = chat(
        model='mistral',
        messages=[
            {
                'role': 'system', 
                'content': 'Та Монгол хэлний ярианы хэлийг албан бичгийн хэлбэр рүү хөрвүүлдэг. Хэллэг үгс (шүү дээ, за, тэгээд) арилгах, албан ёсны хэлбэр болгох.'
            },
            {
                'role': 'user',
                'content': f'Энэ текстийг албан ёсны протокол болго:\n\n{test_mongolian}\n\nЗөвхөн албан ёсны хувилбарыг буцаа, нэмэлт тайлбар бичихгүй.'
            }
        ],
        options={
            'temperature': 0.2,
            'num_predict': 200
        }
    )
    
    result = response['message']['content'].strip()
    print(f"   ✅ SLM хувиргалт амжилттай!")
    print(f"   Үр дүн:\n   {result}\n")
    
    # Quality шалгах
    informal_words = ['шүү дээ', 'за', 'тэгээд', 'болно']
    found_informal = [w for w in informal_words if w in result.lower()]
    
    if found_informal:
        print(f"   ⚠️  Анхааруулга: Хэллэг үгс үлдсэн байна: {found_informal}")
    else:
        print(f"   ✅ Хэллэг үгс амжилттай арилгасан")
    
except Exception as e:
    print(f"   ❌ Монгол хэлний тест амжилтгүй")
    print(f"   Алдаа: {e}\n")
    sys.exit(1)

# 4. Дүгнэлт
print("\n" + "="*60)
print("✅ БҮГД АМЖИЛТТАЙ!")
print("="*60)
print("\nSLM (Ollama + Mistral) ажиллаж байна.")
print("Таны үндсэн кодыг ажиллуулж болно.\n")