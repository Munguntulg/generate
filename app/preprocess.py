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
    Regex ашиглан нэр, байгууллага илрүүлэх (UDPipe байхгүй үед)
    """
    # Хүний нэр: Б.Анударь, Д.Тэмүүлэн
    person_pattern = r"[А-ЯЁҮӨ][а-яёүө]+(?:\s[А-ЯЁҮӨ][а-яёүө]+|\.?[А-ЯЁҮӨ][а-яёүө]+)"
    
    # Байгууллага: Төрийн банк, Их сургууль
    org_pattern = r"[А-ЯЁҮӨ][а-яёүө]+(?:\s[А-ЯЁҮӨ][а-яёүө]+)*(?:\s(банк|их сургууль|ххк|төв))"
    
    persons = re.findall(person_pattern, text)
    orgs = re.findall(org_pattern, text)
    
    return list(set(persons + orgs))