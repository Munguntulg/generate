#!/usr/bin/env python3
"""
Зохиомол өгөгдөл үүсгэх скрипт
Mac Terminal: python3 scripts/generate_synthetic_data.py --count 100
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

NAMES = [
    "Анна", "Жон", "Бат", "Саруул", "Нара", 
    "Болд", "Цэцэг", "Дорж", "Оюунаа", "Эрдэнэ"
]

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

TIMES = [
    "даваа гарагт",
    "мягмар гарагт",
    "ирэх долоо хоногт",
    "маргааш",
    "сарын эцэст",
    "ирэх сард",
    "энэ жилийн эцэст",
]

FILLERS = ["шүү дээ", "л байх даа", "байхаа", "даа шүү", ""]

OPINIONS = [
    "сайн санал",
    "зөв шийдэл",
    "чухал асуудал",
    "анхаарах шаардлагатай",
]

CONDITIONS = [
    "цаг гарвал",
    "нөөц байвал",
    "боломж олдвол",
]

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

def formalize_action(action: str, filler: str) -> str:
    """Үйл үгийг албан хэл болгох"""
    # "хийх" → "гүйцэтгэх", "дуусгах" → "дуусгах болов"
    mapping = {
        "хийх": "гүйцэтгэх",
        "дуусгах": "дуусгах болов",
        "бэлдэх": "бэлтгэнэ",
        "зохион байгуулах": "зохион байгуулна",
        "цуглуулах": "цуглуулна",
        "үүсгэх": "үүсгэнэ",
        "тавих": "тавих болов",
        "гаргах": "гаргана",
    }
    
    for key, val in mapping.items():
        if key in action:
            action = action.replace(key, val)
    
    # Хэллэг үгс арилгах
    action = action.replace(filler, "").strip()
    
    return action

def generate_output(input_text: str, template_type: str, name: str = None, action: str = None, time: str = None) -> str:
    """Input-аас output үүсгэх"""
    
    if template_type.startswith("action"):
        formal_name = formalize_name(name)
        formal_action = formalize_action(action, "")
        
        if time:
            output = f"{formal_name} {formal_action} {time}."
        else:
            output = f"{formal_name} {formal_action}."
    
    elif template_type == "decision":
        output = input_text.replace("Тогтоол:", "ТОГТСОН:")
        output = output.replace("Шийдвэр:", "ШИЙДСЭН:")
        # Хэллэг үгс арилгах
        for filler in FILLERS:
            output = output.replace(filler, "")
        output = output.strip()
        if not output.endswith("."):
            output += "."
    
    elif template_type == "discussion":
        formal_name = formalize_name(name)
        opinion = input_text.split(":")[1].strip()
        # Хэллэг үгс арилгах
        for filler in FILLERS:
            opinion = opinion.replace(filler, "")
        output = f"{formal_name} {opinion.strip()}."
    
    else:
        output = input_text
    
    return output

# ===========================================
# SAMPLE ҮҮСГЭХ
# ===========================================

def generate_sample(idx: int) -> dict:
    """Нэг жишээ үүсгэх"""
    
    # Template сонгох
    template_type = random.choice(list(TEMPLATES.keys()))
    template = random.choice(TEMPLATES[template_type])
    
    # Components сонгох
    name = random.choice(NAMES) if "{name}" in template else None
    action = random.choice(ACTIONS) if "{action}" in template else None
    time = random.choice(TIMES) if "{time}" in template else None
    filler = random.choice(FILLERS) if "{filler}" in template else ""
    opinion = random.choice(OPINIONS) if "{opinion}" in template else None
    condition = random.choice(CONDITIONS) if "{condition}" in template else None
    reason = random.choice(REASONS) if "{reason}" in template else None
    
    # Input үүсгэх
    input_text = template.format(
        name=name or "",
        action=action or "",
        time=time or "",
        filler=filler,
        opinion=opinion or "",
        condition=condition or "",
        reason=reason or ""
    ).strip()
    
    # Output үүсгэх
    output_text = generate_output(input_text, template_type, name, action, time)
    
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

def generate_dataset(count: int, output_path: str):
    """Олон жишээ үүсгэх"""
    
    print(f"\n{'='*60}")
    print(f"ЗОХИОМОЛ ӨГӨГДӨЛ ҮҮСГЭХ")
    print(f"{'='*60}\n")
    
    samples = []
    
    print(f"Үүсгэж байна: {count} жишээ...")
    
    for i in range(count):
        sample = generate_sample(i)
        samples.append(sample)
        
        # Progress
        if (i + 1) % 10 == 0:
            print(f"  ✓ {i + 1}/{count}")
    
    # Хадгалах
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"samples": samples}, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ АМЖИЛТТАЙ!")
    print(f"{'='*60}")
    print(f"\nҮр дүн:")
    print(f"  📁 Файл: {output_path}")
    print(f"  📊 Жишээ: {len(samples)}")
    print(f"  💾 Хэмжээ: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Жишээ харуулах
    print(f"\nЖишээ 1:")
    print(f"  Input:  {samples[0]['input']}")
    print(f"  Output: {samples[0]['output']}")
    
    print(f"\nЖишээ 2:")
    print(f"  Input:  {samples[1]['input']}")
    print(f"  Output: {samples[1]['output']}")
    
    print(f"\nДараагийн алхам:")
    print(f"  python scripts/check_dataset_quality.py {output_path}")
    print()

# ===========================================
# MAIN
# ===========================================

def main():
    parser = argparse.ArgumentParser(
        description="Зохиомол өгөгдөл үүсгэх скрипт"
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
    
    args = parser.parse_args()
    
    generate_dataset(args.count, args.output)

if __name__ == "__main__":
    main()