import re
from typing import List

def clean_text(text: str) -> str:
    """
    Ярианы хэллэгүүдийг арилгаж, илүү цэгцтэй хэлбэрт оруулна.
    """
    # Ярианы хэллэгүүдийг арилгах
    fillers = ["аа", "ээ", "өө", "юу", "гээд", "тэгээд", "за", "тэгэхээр"]
    pattern = r"\b(" + "|".join(fillers) + r")\b"
    text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Давхар хоосон зайг арилгах
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_entities(text: str) -> List[str]:
    """
    Монгол нэр, байгууллагын нэрийг regex ашиглан энгийн байдлаар илрүүлнэ.
    Жишээ нь 'Б.Анударь', 'Д.Тэмүүлэн', 'Төрийн банк' гэх мэт.
    """
    # Хүний нэрийн хэв маяг (Б.Нэр / Нэр Овог)
    person_pattern = r"[А-ЯЁҮӨ][а-яёүө]+(?:\s[А-ЯЁҮӨ][а-яёүө]+|\.?[А-ЯЁҮӨ][а-яёүө]+)"
    
    # Байгууллагын нэр (Банк, ХХК, Их сургууль гэх мэт)
    org_pattern = r"[А-ЯЁҮӨ][а-яёүө]+(?:\s[А-ЯЁҮӨ][а-яёүө]+)*(?:\s(банк|их сургууль|ххк|төв|газрын|компанийн))"

    persons = re.findall(person_pattern, text)
    orgs = re.findall(org_pattern, text)

    entities = list(set(persons + orgs))
    return entities
