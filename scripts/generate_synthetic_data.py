#!/usr/bin/env python3
"""
Зохиомол өгөгдөл үүсгэх скрипт - САЙЖРУУЛСАН
Одоогийн generate_synthetic_data.py-г орлох

Ашиглалт:
    python scripts/generate_synthetic_data.py --count 1000 --output data/raw/expanded_dataset.json
"""

import json
import random
import argparse
from pathlib import Path
from datetime import datetime

# ===========================================
# TEMPLATES & COMPONENTS
# ===========================================

TEMPLATES = {
    "action_simple": [
        "{name}: Би {action} {time} {filler}",
        "{name}: {time} {action} хэрэгтэй {filler}",
        "{name}: Миний санал бол {action} {filler}",
    ],
    "action_complex": [
        "{name}: {time} {action} бол {reason} {filler}",
        "{name}: Хэрэв {condition} бол {action} {time} {filler}",
        "{name}: {action} {time}, тэгээд {extra_action} {filler}",
    ],
    "decision": [
        "Тогтоол: {time} {action}",
        "Шийдвэр: {action} {time}",
        "Хурлын дүгнэлт: {action}",
        "ТОГТСОН: {time} {action}аар тогтов",
    ],
    "discussion": [
        "{name}: {opinion} гэж бодож байна {filler}",
        "{name}: Энэ асуудлын талаар {opinion} {filler}",
    ]
}

# Үндсэн нэрс
NAMES = [
    "Анна", "Жон", "Бат", "Саруул", "Нара", 
    "Болд", "Цэцэг", "Дорж", "Оюунаа", "Эрдэнэ"
]

# Нэмэлт нэрс
ADDITIONAL_NAMES = [
    "Мөнх", "Өлзий", "Гантуяа", "Энхжин", "Баярмаа",
    "Тамир", "Цогт", "Алтан", "Сувд", "Даваа",
    "Ууганбаяр", "Мөнхзул", "Идэр", "Сэргэлэн", "Туул"
]

# Үндсэн үйлүүд
ACTIONS = [
    "төслийг дуусгах",
    "тайлан бэлдэх",
    "хурал зохион байгуулах",
    "өгөгдөл цуглуулах",
    "график үүсгэх",
    "шалгалт хийх",
    "баримт бичиг бэлдэх",
    "илтгэл тавих",
    "хяналт тавих",
    "дүгнэлт гаргах",
]

# Нэмэлт үйлүүд
ADDITIONAL_ACTIONS = [
    "судалгаа явуулах",
    "хуралдаан зохион байгуулах", 
    "санал авах",
    "төсөл боловсруулах",
    "үнэлгээ хийх",
    "шинэчлэлт хийх",
    "хамтран ажиллах",
    "зөвлөгөө өгөх",
    "мэдээлэл нэгтгэх",
    "үр дүн дүгнэх"
]

# Үндсэн огноо
TIMES = [
    "даваа гарагт",
    "мягмар гарагт",
    "ирэх долоо хоногт",
    "маргааш",
    "сарын эцэст",
    "ирэх сард",
    "энэ жилийн эцэст",
]

# Нэмэлт огноо
ADDITIONAL_TIMES = [
    "пүрэв гарагт",
    "баасан гарагт",
    "лхагва гарагт",
    "энэ сарын эцэст",
    "дараа сард",
    "хоёр долоо хоногийн дараа",
    "гурван өдрийн дараа",
    "дараа жил"
]

# Хэллэг үгс
FILLERS = ["шүү дээ", "л байх даа", "байхаа", "даа шүү", ""]

# Санал/бодол
OPINIONS = [
    "сайн санал",
    "зөв шийдэл",
    "чухал асуудал",
    "анхаарах шаардлагатай",
]

# Нөхцөл
CONDITIONS = [
    "цаг гарвал",
    "нөөц байвал",
    "боломж олдвол",
    "багийнхан зөвшөөрвөл"
]

# Шалтгаан
REASONS = [
    "яаралтай байгаа тул",
    "чухал учраас",
    "шаардлагатай тул",
]

# ===========================================
# ФОРМАЛИЗАЦИЯ ФУНКЦҮҮД
# ===========================================

def formalize_name(name: str) -> str:
    """Анна → А.Анна"""
    return f"{name[0]}.{name}"

def formalize_action(action: str) -> str:
    """
    Үйл үгийг албан хэл болгох
    
    Дүрэм:
    - хийх → гүйцэтгэх
    - дуусгах → дуусгах болов
    - бэлдэх → бэлтгэнэ
    - зохион байгуулах → зохион байгуулна
    """
    mapping = {
        "хийх": "гүйцэтгэх",
        "дуусгах": "дуусгах болов",
        "бэлдэх": "бэлтгэнэ",
        "зохион байгуулах": "зохион байгуулна",
        "цуглуулах": "цуглуулна",
        "үүсгэх": "үүсгэнэ",
        "тавих": "тавих болов",
        "гаргах": "гаргана",
        "явуулах": "явуулна",
        "авах": "авна",
        "боловсруулах": "боловсруулна",
        "нэгтгэх": "нэгтгэнэ",
    }
    
    for key, val in mapping.items():
        if key in action:
            return action.replace(key, val)
    
    return action

def generate_output(input_text: str, template_type: str, components: dict) -> str:
    """
    Input-аас output үүсгэх
    
    Args:
        input_text: Анхны ярианы текст
        template_type: Template төрөл
        components: Компонентууд (name, action, time, гэх мэт)
    """
    name = components.get('name')
    action = components.get('action')
    time = components.get('time')
    filler = components.get('filler', '')
    
    if template_type.startswith("action"):
        formal_name = formalize_name(name)
        formal_action = formalize_action(action)
        
        # Хэллэг үгс арилгах
        formal_action = formal_action.replace(filler, "").strip()
        
        if time:
            output = f"{formal_name} {formal_action} {time}."
        else:
            output = f"{formal_name} {formal_action}."
    
    elif template_type == "decision":
        # ТОГТСОН/ШИЙДСЭН болгох
        output = input_text.replace("Тогтоол:", "ТОГТСОН:")
        output = output.replace("Шийдвэр:", "ШИЙДСЭН:")
        
        # Хэллэг үгс арилгах
        for f in FILLERS:
            if f:  # Хоосон биш бол
                output = output.replace(f, "")
        
        output = output.strip()
        if not output.endswith("."):
            output += "."
    
    elif template_type == "discussion":
        formal_name = formalize_name(name)
        
        # ":" дараах хэсгийг авах
        if ":" in input_text:
            opinion_part = input_text.split(":", 1)[1].strip()
        else:
            opinion_part = input_text
        
        # Хэллэг үгс арилгах
        for f in FILLERS:
            if f:
                opinion_part = opinion_part.replace(f, "")
        
        output = f"{formal_name} {opinion_part.strip()}."
    
    else:
        # Default
        output = input_text.strip()
        if not output.endswith("."):
            output += "."
    
    return output

# ===========================================
# SAMPLE ҮҮСГЭХ
# ===========================================

def generate_sample(idx: int, all_names: list, all_actions: list, all_times: list) -> dict:
    """
    Нэг жишээ үүсгэх
    
    Args:
        idx: Sample ID
        all_names: Бүх нэрсийн жагсаалт
        all_actions: Бүх үйлүүдийн жагсаалт
        all_times: Бүх огноонуудын жагсаалт
    
    Returns:
        Sample dict (id, input, output, metadata)
    """
    
    # Template сонгох
    template_type = random.choice(list(TEMPLATES.keys()))
    template = random.choice(TEMPLATES[template_type])
    
    # Components сонгох
    name = random.choice(all_names) if "{name}" in template else None
    action = random.choice(all_actions) if "{action}" in template else None
    extra_action = random.choice(all_actions) if "{extra_action}" in template else None
    time = random.choice(all_times) if "{time}" in template else None
    filler = random.choice(FILLERS) if "{filler}" in template else ""
    opinion = random.choice(OPINIONS) if "{opinion}" in template else None
    condition = random.choice(CONDITIONS) if "{condition}" in template else None
    reason = random.choice(REASONS) if "{reason}" in template else None
    
    # Input үүсгэх
    input_text = template.format(
        name=name or "",
        action=action or "",
        extra_action=extra_action or "",
        time=time or "",
        filler=filler,
        opinion=opinion or "",
        condition=condition or "",
        reason=reason or ""
    ).strip()
    
    # Output үүсгэх
    components = {
        'name': name,
        'action': action,
        'time': time,
        'filler': filler
    }
    output_text = generate_output(input_text, template_type, components)
    
    # Metadata
    metadata = {
        "template_type": template_type,
        "has_dates": time is not None,
        "has_fillers": filler != "",
        "synthetic": True,
        "quality": "medium"
    }
    
    if name:
        metadata["participants"] = [name]
    
    return {
        "id": f"synthetic_{idx:04d}",
        "input": input_text,
        "output": output_text,
        "metadata": metadata
    }

# ===========================================
# BATCH ҮҮСГЭХ
# ===========================================

def generate_dataset(count: int, output_path: str, use_existing: bool = False):
    """
    Олон жишээ үүсгэх
    
    Args:
        count: Хэдэн жишээ үүсгэх
        output_path: Хадгалах файлын зам
        use_existing: Одоогийн өгөгдөлтэй нэгтгэх эсэх
    """
    
    print(f"\n{'='*60}")
    print(f"ЗОХИОМОЛ ӨГӨГДӨЛ ҮҮСГЭХ")
    print(f"{'='*60}\n")
    
    existing_samples = []
    
    # Одоогийн өгөгдөл байгаа эсэхийг шалгах
    if use_existing and Path(output_path).exists():
        print(f"Одоогийн өгөгдөл олдсон: {output_path}")
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        existing_samples = data.get('samples', [])
        print(f"  ✓ {len(existing_samples)} жишээ байна\n")
    
    # Бүх нэрс, үйл, огноо нэгтгэх
    all_names = list(set(NAMES + ADDITIONAL_NAMES))
    all_actions = list(set(ACTIONS + ADDITIONAL_ACTIONS))
    all_times = list(set(TIMES + ADDITIONAL_TIMES))
    
    print(f"Компонентууд:")
    print(f"  👤 Нэрс: {len(all_names)}")
    print(f"  ⚡ Үйлүүд: {len(all_actions)}")
    print(f"  📅 Огноо: {len(all_times)}\n")
    
    # Шинэ жишээ үүсгэх
    print(f"Үүсгэж байна: {count} жишээ...")
    
    samples = []
    start_idx = len(existing_samples)
    
    for i in range(count):
        sample = generate_sample(
            start_idx + i,
            all_names,
            all_actions,
            all_times
        )
        samples.append(sample)
        
        # Progress
        if (i + 1) % 100 == 0:
            print(f"  ✓ {i + 1}/{count}")
    
    # Нэгтгэх
    all_samples = existing_samples + samples if use_existing else samples
    
    # Хадгалах
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"samples": all_samples}, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ АМЖИЛТТАЙ!")
    print(f"{'='*60}")
    print(f"\nҮр дүн:")
    print(f"  📁 Файл: {output_path}")
    print(f"  📊 Нийт жишээ: {len(all_samples)}")
    
    if use_existing and existing_samples:
        print(f"  ➕ Нэмсэн: {len(samples)}")
        print(f"  📋 Өмнөх: {len(existing_samples)}")
    
    print(f"  💾 Хэмжээ: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Статистик
    with_dates = sum(1 for s in all_samples if s['metadata'].get('has_dates'))
    with_fillers = sum(1 for s in all_samples if s['metadata'].get('has_fillers'))
    
    print(f"\nСтатистик:")
    print(f"  📅 Огноотой: {with_dates} ({with_dates/len(all_samples)*100:.1f}%)")
    print(f"  🔤 Filler-тэй: {with_fillers} ({with_fillers/len(all_samples)*100:.1f}%)")
    
    # Жишээнүүд харуулах
    print(f"\nЖишээ 1:")
    print(f"  Input:  {samples[0]['input']}")
    print(f"  Output: {samples[0]['output']}")
    
    if len(samples) > 1:
        print(f"\nЖишээ 2:")
        print(f"  Input:  {samples[1]['input']}")
        print(f"  Output: {samples[1]['output']}")
    
    print(f"\nДараагийн алхам:")
    print(f"  python scripts/split_dataset.py")
    print()

# ===========================================
# MAIN
# ===========================================

def main():
    parser = argparse.ArgumentParser(
        description="Зохиомол өгөгдөл үүсгэх скрипт - САЙЖРУУЛСАН"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Хэдэн жишээ үүсгэх (default: 100)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/synthetic_dataset.json",
        help="Output файлын зам (default: data/raw/synthetic_dataset.json)"
    )
    
    parser.add_argument(
        "--append",
        action="store_true",
        help="Одоогийн өгөгдөлтэй нэгтгэх эсэх (default: False)"
    )
    
    args = parser.parse_args()
    
    generate_dataset(
        count=args.count,
        output_path=args.output,
        use_existing=args.append
    )

if __name__ == "__main__":
    main()