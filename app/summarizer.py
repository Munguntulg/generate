#!/usr/bin/env python3
"""
SLM Summarizer - Сайжруулсан prompt болон validation
"""

import re
from typing import Dict, Optional

try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class SLMOnlySummarizer:
    """
    Сайжруулсан prompt, нарийвчилсан validation
    """
    
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.max_chunk_length = 1500
        
        if not OLLAMA_AVAILABLE:
            raise RuntimeError(
                "❌ Ollama суулгаагүй байна!\n"
                "   Суулгах: pip install ollama"
            )
        
        self._verify_model()
        print(f"✅ SLM бэлэн: {self.model}")
    
    def _verify_model(self):
        """Model байгаа эсэхийг шалгах"""
        try:
            response = chat(
                model=self.model,
                messages=[{'role': 'user', 'content': 'test'}],
                options={'num_predict': 5}
            )
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'not found' in error_msg or '404' in error_msg:
                raise RuntimeError(
                    f"❌ Model '{self.model}' олдсонгүй!\n"
                    f"   Татах: ollama pull {self.model}"
                )
            else:
                raise RuntimeError(
                    f"❌ Ollama server ажиллахгүй байна!\n"
                    f"   Эхлүүлэх: ollama serve"
                )
    
    def formalize_text(self, text: str, debug: bool = True) -> str:
        """
        SLM ашиглан албан хэл болгох (САЙЖРУУЛСАН)
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("❌ SLM ажиллахгүй байна")
        
        if len(text) > self.max_chunk_length:
            return self._process_long_text(text)
        
        # САЙЖРУУЛСАН PROMPT
        system_prompt = """Та Монгол улсын албан ёсны протокол бичдэг мэргэжилтэн.

🎯 ТАНЫ ҮҮРЭГ: Ярианы бичлэгийг АЛБАН ЁСНЫ ПРОТОКОЛ болгох

📋 ЗААВАЛ ДАГАХ 5 ДҮРЭМ:

1️⃣ ХЭЛЛЭГ ҮГСИЙГ БҮРЭН АРИЛГА:
   ❌ Хэрэглэхгүй: аа, ээ, өө, шүү, дээ, л байх, байхаа, за, тэгээд, гээд
   ✅ Тэднийг бүрэн УСТГА

2️⃣ ЯРИАНЫ МАЯГИЙГ АЛБАН ХЭЛ БОЛГО:
   ❌ "Би хийнэ шүү дээ" 
   ✅ "[Нэр] хариуцан гүйцэтгэнэ"
   
   ❌ "хэллээ"
   ✅ "дэвшүүлэв" эсвэл "илэрхийлэв"
   
   ❌ "болно"
   ✅ "болох" эсвэл "болов"

3️⃣ НЭР, ОГНОО, ТОО - ЯАЖ БАЙ ХАДГАЛ:
   Анна → А.Анна эсвэл Анна (өөрчлөхгүй)
   даваа гараг → даваа гараг (өөрчлөхгүй)

4️⃣ ТОДОРХОЙ ӨГҮҮЛБЭР:
   ❌ "За тэгээд бид үргэлжлүүлье"
   ✅ "Хэлэлцүүлгийг үргэлжлүүлэв"

5️⃣ ЗӨВХӨН МОНГОЛ ХЭЛ:
   Англи хэл рүү ОРЧУУЛАХГҮЙ
   Нэмэлт тайлбар БИЧИХГҮЙ

🔍 ӨМНӨХ АЛДААНУУДААС СУРАХ:
- "шүү дээ", "л байх даа" → БҮРЭН устгах
- Англи үг хэрэглэхгүй
- Агуулгыг өөрчлөхгүй

📝 ЖИШЭЭ ӨМНӨ → ДАРАА:

Өмнө: "Анна: Би энэ ажлыг даваа гарагт хийх болно шүү дээ."
Дараа: "А.Анна даваа гарагт ажлыг хариуцан гүйцэтгэх болов."

Өмнө: "За тэгээд бид үргэлжлүүлье шүү."
Дараа: "Хэлэлцүүлгийг үргэлжлүүлэв."

Өмнө: "Тогтоол: Ирэх долоо хоногт дуусгах."
Дараа: "ТОГТСОН: Ирэх долоо хоногт ажлыг дуусгахаар тогтов."

⚠️ АНХААР:
- Зөвхөн протокол бич
- Тайлбар бичихгүй
- "Based on..." гэх мэт англи хэл БАЙХГҮЙ"""

        user_prompt = f"""Энэ хурлын ярианы бичлэгийг АЛБАН ЁСНЫ ПРОТОКОЛ болго.

АНХНЫ БИЧЛЭГ:
{text}

ЧУХАЛ: Зөвхөн албан ёсны протокол бич. Нэмэлт тайлбар, англи үг БАЙХГҮЙ."""

        try:
            if debug:
                print(f"\n   📤 SLM рүү хүсэлт илгээж байна...")
                print(f"   Модель: {self.model}")
                print(f"   Анхны урт: {len(text)} тэмдэгт")
            
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,   # Маш тогтвортой
                    "top_p": 0.8,
                    "num_predict": 2000,
                    "repeat_penalty": 1.1,  # Давталт багасгах
                }
            )
            
            result = response["message"]["content"].strip()
            
            if debug:
                print(f"\n   📥 SLM ХАРИУЛТ ИРЛЭЭ:")
                print(f"   " + "="*56)
                preview = result[:400] if len(result) > 400 else result
                for line in preview.split('\n'):
                    print(f"   {line}")
                if len(result) > 400:
                    print(f"   ... (нийт {len(result)} тэмдэгт)")
                print(f"   " + "="*56)
            
            # НАРИЙВЧИЛСАН ШАЛГАЛТ
            is_valid, errors = self._validate_result(text, result)
            
            if not is_valid:
                print(f"\n   ❌ QUALITY CHECK АМЖИЛТГҮЙ:")
                for error in errors:
                    print(f"      • {error}")
                
                # Retry логик (1 удаа л)
                print(f"\n   🔄 Дахин оролдож байна (temperature өөрчлөх)...")
                return self._retry_with_adjusted_params(text, system_prompt, user_prompt)
            
            print(f"   ✅ Quality check АМЖИЛТТАЙ")
            return self._post_process(result)
            
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            else:
                raise RuntimeError(
                    f"❌ SLM алдаа гарлаа!\n"
                    f"   Model: {self.model}\n"
                    f"   Алдаа: {str(e)}"
                )
    
    def _validate_result(self, original: str, result: str) -> tuple[bool, list]:
        """
        НАРИЙВЧИЛСАН VALIDATION - алдааны жагсаалт буцаана
        
        Returns:
            (is_valid: bool, errors: list[str])
        """
        errors = []
        
        # 1. Хоосон эсэх
        if len(result.strip()) < 10:
            errors.append(f"Хэт богино: {len(result)} тэмдэгт")
            return False, errors
        
        # 2. Харьцаа (илүү уян хатан)
        ratio = len(result) / len(original) if len(original) > 0 else 0
        if ratio < 0.15:
            errors.append(f"Хэт богино (харьцаа {ratio:.2f})")
        elif ratio > 8.0:
            errors.append(f"Хэт урт (харьцаа {ratio:.2f})")
        
        # 3. Англи хэл
        # Монгол үсэг vs Англи үсэг
        cyrillic_chars = len(re.findall(r'[А-Яа-яЁёӨөҮү]', result))
        english_chars = len(re.findall(r'[A-Za-z]', result))
        
        # Англи үсэг хэтэрхий их эсэх (Монголоос илүү)
        if english_chars > cyrillic_chars * 0.3:
            errors.append(
                f"Англи хэл их байна (Англи: {english_chars}, Монгол: {cyrillic_chars})"
            )
        
        # 4. КРИТИК хэллэг үгс (Үндсэн асуудал)
        critical_fillers = {
            'шүү дээ': 'ярианы хэллэг',
            'л байх даа': 'ярианы хэллэг',
            'байхаа': 'ярианы хэллэг',
            'биз дээ': 'ярианы хэллэг',
            'аа дээ': 'ярианы хэллэг',
            'шүү аа': 'ярианы хэллэг'
        }
        
        found = []
        for filler, description in critical_fillers.items():
            if filler in result.lower():
                found.append(f'"{filler}" ({description})')
        
        if found:
            errors.append(f"Хэллэг үгс үлдсэн: {', '.join(found)}")
        
        # 5. Ярианы маяг үлдсэн эсэх
        informal_patterns = [
            r'\bби\s+хийнэ\b',  # "би хийнэ" үлдсэн
            r'\bта\s+хийнэ\b',
            r'\bболно\s+шүү\b',
        ]
        
        found_patterns = []
        for pattern in informal_patterns:
            if re.search(pattern, result, re.IGNORECASE):
                found_patterns.append(pattern)
        
        if found_patterns:
            errors.append(f"Ярианы маяг үлдсэн: {len(found_patterns)} байршил")
        
        # Дүгнэлт
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _retry_with_adjusted_params(
        self, 
        text: str, 
        system_prompt: str, 
        user_prompt: str
    ) -> str:
        """
        Параметр өөрчилж дахин оролдох
        """
        try:
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt + "\n\nАНХААРУУЛГА: Хэллэг үгс (шүү дээ, л байх даа) БҮРЭН АРИЛГА!"}
                ],
                options={
                    "temperature": 0.05,  # Бага болгох
                    "top_p": 0.7,
                    "num_predict": 2000,
                    "repeat_penalty": 1.2,
                }
            )
            
            result = response["message"]["content"].strip()
            
            is_valid, errors = self._validate_result(text, result)
            
            if not is_valid:
                print(f"   ❌ Retry ч амжилтгүй:")
                for error in errors:
                    print(f"      • {error}")
                
                raise RuntimeError(
                    f"❌ SLM 2 удаа оролдсон боловч чанаргүй үр дүн!\n"
                    f"   Алдаанууд: {'; '.join(errors)}"
                )
            
            print(f"   ✅ Retry амжилттай!")
            return self._post_process(result)
            
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Retry алдаа: {str(e)}")
    
    def _post_process(self, text: str) -> str:
        """
        Эцсийн цэвэрлэлт
        """
        # Үлдсэн хэллэг үгс (давхар цэвэрлэлт)
        fillers = [
            'шүү дээ', 'л байх даа', 'байхаа', 'биз дээ', 'аа дээ',
            'шүү аа', 'ээ дээ', 'өө дээ', 
            'аа', 'ээ', 'өө', 'юу', 'гээд', 'тэгээд', 'за', 'тэгэхээр'
        ]
        
        for filler in fillers:
            # Word boundary ашиглах (богино үгэнд чухал)
            if len(filler) <= 3:
                text = re.sub(r'\b' + re.escape(filler) + r'\b', '', text, flags=re.IGNORECASE)
            else:
                text = text.replace(filler, '')
                text = text.replace(filler.capitalize(), '')
        
        # Давхар хоосон зай
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([,.!?])', r'\1', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Өгүүлбэр эхний үсэг том
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and len(line) > 0:
                line = line[0].upper() + line[1:] if len(line) > 1 else line.upper()
            lines.append(line)
        
        return '\n'.join(lines).strip()
    
    def _process_long_text(self, text: str) -> str:
        """
        Урт текстийг хэсэглэх
        """
        sentences = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 20]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.max_chunk_length:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        formalized_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"   📄 Хэсэг {i+1}/{len(chunks)} боловсруулж байна...")
            formalized = self.formalize_text(chunk, debug=False)
            formalized_chunks.append(formalized)
        
        return "\n\n".join(formalized_chunks)


# ТЕСТ
if __name__ == "__main__":
    print("\n" + "="*60)
    print("САЙЖРУУЛСАН SLM SUMMARIZER ТЕСТ")
    print("="*60 + "\n")
    
    try:
        summarizer = SLMOnlySummarizer(model="qwen2.5:7b")
        
        test_text = """
        Анна: Би энэ ажлыг даваа гарагт хийх болно шүү дээ.
        Жон: За тэгээд би шалгаж үзье л байх даа.
        Тогтоол: Ирэх долоо хоногт бүх ажлыг дуусгах.
        """
        
        print("АНХНЫ ТЕКСТ:")
        print(test_text)
        print()
        
        result = summarizer.formalize_text(test_text, debug=True)
        
        print("\n" + "="*60)
        print("ЭЦСИЙН ҮР ДҮН:")
        print("="*60)
        print(result)
        print("\n✅ АМЖИЛТТАЙ!\n")
        
    except RuntimeError as e:
        print(f"\n❌ АЛДАА:\n{e}\n")