import re
from typing import List

def clean_text(text: str) -> str:
    """
    Хэллэг үгсийг арилгах: аа, ээ, өө, тэгээд гэх мэт
    """
    fillers = ["аа", "ээ", "өө", "юу", "гээд", "тэгээд", "за", "тэгэхээр"]
    pattern = r"\b(" + "|".join(fillers) + r")\b"
    text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Давхар хоосон зай арилгах
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_entities(text: str) -> List[str]:
    """
    САЙЖРУУЛСАН Regex - илүү олон pattern
    """
    entities = set()
    
    # 1. "Нэр:" формат (Хамгийн найдвартай)
    # Жишээ: Анна:, Жон:, Бат:
    colon_pattern = r'\b([А-ЯЁҮӨ][а-яёүө]{1,15})\s*:'
    names_with_colon = re.findall(colon_pattern, text)
    entities.update(names_with_colon)
    
    # 2. Овогтой нэр (Б.Анна, Д.Тэмүүлэн)
    initial_name = r'\b[А-ЯЁҮӨ]\.[А-ЯЁҮӨ][а-яёүө]+'
    entities.update(re.findall(initial_name, text))
    
    # 3. Бүтэн нэр (Доржийн Батаа)
    full_name = r'\b[А-ЯЁҮӨ][а-яёүө]+(?:ийн|ын)\s+[А-ЯЁҮӨ][а-яёүө]+'
    entities.update(re.findall(full_name, text))
    
    # 4. Байгууллага
    org_keywords = [
        'банк', 'их сургууль', 'ххк', 'төв', 'газар', 
        'яам', 'компани', 'корпораци', 'холбоо', 'нийгэмлэг'
    ]
    
    for keyword in org_keywords:
        # Том үсэгтэй эхлэх + keyword
        pattern = r'[А-ЯЁҮӨ][а-яёүө]+(?:\s+[А-ЯЁҮӨ][а-яёүө]+)*\s+' + keyword
        orgs = re.findall(pattern, text, re.IGNORECASE)
        entities.update(orgs)
    
    # 5. Газар нэр (Улаанбаатар, Дархан-Уул)
    place_suffixes = ['хот', 'аймаг', 'сум', 'дүүрэг']
    for suffix in place_suffixes:
        pattern = r'[А-ЯЁҮӨ][а-яёүө]+(?:[-\s][А-ЯЁҮӨ][а-яёүө]+)?\s+' + suffix
        places = re.findall(pattern, text, re.IGNORECASE)
        entities.update(places)
    
    # 6. "Тогтоол", "Шийдвэр" хасах (хүний нэр биш)
    false_positives = {'Тогтоол', 'Шийдвэр', 'Санал', 'Дүгнэлт', 'Хэлэлцсэн'}
    entities = entities - false_positives
    
    # 7. Хэт богино арилгах (1-2 үсэг)
    entities = {e for e in entities if len(e) > 2}
    
    return sorted(list(entities))