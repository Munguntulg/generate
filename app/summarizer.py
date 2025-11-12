#!/usr/bin/env python3
"""
SLM Summarizer - УТГА ХАДГАЛАХ сайжруулалт
Үндсэн өөрчлөлт:
1. Prompt илүү тодорхой - АГУУЛГА ӨӨРЧЛӨХГҮЙ
2. Утгын шалгалт нэмэх
3. Sentence-level боловсруулалт
"""

import re
from typing import Dict, Optional, Tuple, List

try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Зөв бичгийн шалгагч
try:
    from .spell_checker import MongolianSpellChecker
    SPELL_CHECKER_AVAILABLE = True
except ImportError:
    SPELL_CHECKER_AVAILABLE = False
    print("⚠️ spell_checker.py байхгүй")


class SLMOnlySummarizer:
    """
    УТГА ХАДГАЛДАГ summarizer
    """
    
    def __init__(self, model: str = "qwen2.5:7b", use_spell_check: bool = True):
        self.model = model
        self.max_chunk_length = 1500
        self.use_spell_check = use_spell_check and SPELL_CHECKER_AVAILABLE
        
        if not OLLAMA_AVAILABLE:
            raise RuntimeError(
                "❌ Ollama суулгаагүй байна!\n"
                "   Суулгах: pip install ollama"
            )
        
        if self.use_spell_check:
            try:
                self.spell_checker = MongolianSpellChecker()
                print("✅ Зөв бичгийн шалгагч идэвхтэй")
            except Exception as e:
                print(f"⚠️ Зөв бичгийн шалгагч эхлэхгүй: {e}")
                self.use_spell_check = False
        
        self._verify_model()
        print(f"✅ SLM бэлэн: {self.model}")
    
    def _verify_model(self):
        """Model шалгах"""
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
        АГУУЛГА ХАДГАЛСАН албан хэл болгох
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("❌ SLM ажиллахгүй байна")
        
        # Зөв бичгийн урьдчилсан шалгалт
        if self.use_spell_check:
            if debug:
                print("\n📝 Зөв бичгийн урьдчилсан шалгалт хийж байна...")
            text = self.spell_checker.integrate_with_summarizer(text)
        
        if len(text) > self.max_chunk_length:
            return self._process_long_text(text)
        
        # ШИНЭЧИЛСЭН PROMPT - АГУУЛГА ӨӨРЧЛӨХГҮЙ
        system_prompt = """Та протокол засварлагч. Яг нэг зүйл хийнэ: Ярианы маягийг албан маяг болгоно.

🎯 ХАМГИЙН ЧУХАЛ: АГУУЛГА ӨӨРЧЛӨХГҮЙ
- Нэр → нэр (өөрчлөхгүй)
- Огноо → огноо (өөрчлөхгүй)
- Тоо → тоо (өөрчлөхгүй)
- Үйл → үйл (өөрчлөхгүй)
- Зөвхөн ХЭЛЛЭГ ҮГС арилгана

📝 ЯРИАНЫ МАЯГ → АЛБАН МАЯГ:

1. Хэллэг үгс АРИЛГА:
   - шүү дээ, л байх даа, байхаа → (устгах)
   - за, тэгээд, гээд → (устгах)

2. Үйл үг албан хэл болго:
   - "би хийнэ" → "[Нэр] гүйцэтгэнэ"
   - "би бэлднэ" → "[Нэр] бэлтгэнэ"
   - "болно" → "болов"
   
3. Зөв бичгийн дүрэм:
   - Өгүүлбэр эхний үсэг том
   - Таслалын өмнө зай БАЙХГҮЙ
   - Давхар зай БАЙХГҮЙ

⚠️ ХОРИОТОЙ:
- Үг солихгүй (Анна → Жон БИШІ)
- Огноо өөрчлөхгүй (даваа гараг → утга алдахгүй)
- Тоо өөрчлөхгүй
- Нэмэлт тайлбар БАЙХГҮЙ
- Англи хэл БАЙХГҮЙ

ЖИШЭЭ:

Ярианы хэл:
"Анна: Би энэ төслийг даваа гарагт дуусгах болно шүү дээ."

Албан хэл:
"А.Анна уг төслийг даваа гарагт дуусгах болов."

АНХААР: "энэ төсөл" → "уг төсөл" (утга адил)
АНХААР: "даваа гараг" → "даваа гараг" (өөрчлөхгүй)"""

        user_prompt = f"""Энэ ярианы бичлэгийг албан протокол болго. АГУУЛГА ӨӨРЧЛӨХГҮЙ.

ЯРИАНЫ БИЧЛЭГ:
{text}

ЗӨВХӨН албан маяг бич. Агуулга бүрэн хадгал."""

        try:
            if debug:
                print(f"\n   📤 SLM рүү хүсэлт илгээж байна...")
                print(f"   Модель: {self.model}")
                print(f"   Урт: {len(text)} тэмдэгт")
            
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # 0.05 → 0.1 (илүү creative)
                    "top_p": 0.9,       # 0.7 → 0.9
                    "num_predict": 2000,
                    "repeat_penalty": 1.1,
                }
            )
            
            result = response["message"]["content"].strip()
            
            if debug:
                print(f"\n   📥 SLM хариулт ирлээ ({len(result)} тэмдэгт)")
            
            # Post-processing
            cleaned = self._aggressive_postprocess(result)
            
            # УТГЫН ШАЛГАЛТ - ШИНЭ!
            is_meaningful = self._check_meaning_preserved(text, cleaned)
            
            if not is_meaningful:
                print(f"\n   ⚠️ АНХААРУУЛГА: Утга алдагдсан байж магадгүй!")
                print(f"   🔄 Дахин оролдож байна (илүү консерватив)...")
                
                retry_result = self._retry_formalize_conservative(text, system_prompt, user_prompt)
                if retry_result:
                    cleaned = retry_result
            
            # Зөв бичгийн эцсийн шалгалт
            if self.use_spell_check:
                if debug:
                    print(f"   🔍 Эцсийн зөв бичгийн шалгалт...")
                
                final_check = self.spell_checker.check_text(cleaned, verbose=False)
                
                if final_check['errors']:
                    if debug:
                        print(f"   ⚠️ {len(final_check['errors'])} алдаа засагдаж байна")
                    cleaned = final_check['corrected_text']
                else:
                    if debug:
                        print(f"   ✅ Зөв бичиг хангагдсан")
            
            # Эцсийн validation
            is_valid, errors = self._validate_result_flexible(text, cleaned)
            
            if not is_valid:
                if debug:
                    print(f"\n   ⚠️ Validation:")
                    for error in errors[:3]:
                        print(f"      • {error}")
            else:
                if debug:
                    print(f"   ✅ Чанар хангалттай")
            
            return cleaned
            
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            else:
                raise RuntimeError(
                    f"❌ SLM алдаа!\n"
                    f"   Model: {self.model}\n"
                    f"   Алдаа: {str(e)}"
                )
    
    def _check_meaning_preserved(self, original: str, formalized: str) -> bool:
        """
        УТГА ХАДГАЛАГДСАН эсэх шалгах
        
        Шалгах зүйлс:
        1. Үндсэн үг байгаа эсэх (нэр, огноо)
        2. Утгагүй өгүүлбэр үүссэн эсэх
        3. Хэт богино болоогүй эсэх
        """
        # 1. Нэрс хадгалагдсан эсэх
        original_names = re.findall(r'\b[А-ЯЁҮӨ][а-яёүө]{2,}\b', original)
        formalized_names = re.findall(r'\b[А-ЯЁҮӨ][а-яёүө]{2,}\b', formalized)
        
        # Үндсэн нэрс алга болсон эсэх
        important_names = set(original_names[:10])  # Эхний 10 нэр
        preserved_names = set(formalized_names)
        
        missing_names = important_names - preserved_names
        if len(missing_names) > len(important_names) * 0.5:
            print(f"      ⚠️ Олон нэр алдагдсан: {missing_names}")
            return False
        
        # 2. Огноо, хугацаа хадгалагдсан эсэх
        date_patterns = [
            r'даваа гараг', r'мягмар гараг', r'лхагва гараг',
            r'долоо хоног', r'сар', r'өдөр', r'жил',
            r'\d+', r'нэг', r'хоёр', r'гурав'
        ]
        
        original_has_dates = any(re.search(pattern, original, re.IGNORECASE) for pattern in date_patterns)
        formalized_has_dates = any(re.search(pattern, formalized, re.IGNORECASE) for pattern in date_patterns)
        
        if original_has_dates and not formalized_has_dates:
            print(f"      ⚠️ Огноо/хугацаа алдагдсан")
            return False
        
        # 3. Утгагүй өгүүлбэр эсэх
        # "Хэдүүлэх төслийг" гэх мэт утгагүй үг
        nonsense_patterns = [
            r'хэдүүлэх',  # Утгагүй үйл үг
            r'[а-яёүө]{15,}',  # Хэт урт утгагүй үг
            r'\b[а-яёүө]\b\s+\b[а-яёүө]\b\s+\b[а-яёүө]\b',  # "а б в" гэх мэт
        ]
        
        for pattern in nonsense_patterns:
            if re.search(pattern, formalized):
                print(f"      ⚠️ Утгагүй өгүүлбэр илэрсэн: {pattern}")
                return False
        
        # 4. Хэт богино эсэх
        ratio = len(formalized) / len(original) if len(original) > 0 else 0
        if ratio < 0.3:  # 30%-с бага бол хэт богино
            print(f"      ⚠️ Хэт богино болсон (харьцаа: {ratio:.2f})")
            return False
        
        return True
    
    def _retry_formalize_conservative(
        self,
        text: str,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[str]:
        """
        КОНСЕРВАТИВ retry - агуулга илүү хадгална
        """
        try:
            # Илүү тодорхой анхааруулга
            conservative_prompt = user_prompt + """

🚨 ЧУХАЛ АНХААРУУЛГА:
1. Нэр үгс БҮРЭН хадгал (Анна → А.Анна, утга ижил)
2. Огноо БҮРЭН хадгал (даваа гараг → даваа гараг)
3. Тоо БҮРЭН хадгал
4. Үйл үгийн утга хадгал (дуусгах → дуусгах)
5. ЗӨВХӨН хэллэг үгс арилга

Үг солихгүй, утгыг алдахгүй!"""
            
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": conservative_prompt}
                ],
                options={
                    "temperature": 0.05,  # Илүү консерватив
                    "top_p": 0.7,
                    "num_predict": 2000,
                    "repeat_penalty": 1.15,
                }
            )
            
            result = response["message"]["content"].strip()
            cleaned = self._aggressive_postprocess(result)
            
            # Дахин утгын шалгалт
            is_meaningful = self._check_meaning_preserved(text, cleaned)
            
            if is_meaningful:
                print(f"   ✅ Retry амжилттай - утга хадгалагдсан!")
                return cleaned
            else:
                print(f"   ⚠️ Retry ч утга алдсан - анхны үр дүнг ашиглана")
                return None
                
        except Exception as e:
            print(f"   ❌ Retry алдаа: {e}")
            return None
    
    def _aggressive_postprocess(self, text: str) -> str:
        """
        Хүчтэй post-processing
        """
        # Хэллэг үгс
        filler_phrases = [
            'шүү дээ', 'л байх даа', 'л байх', 'байхаа', 'биз дээ', 
            'аа дээ', 'шүү аа', 'ээ дээ', 'өө дээ', 'даа шүү',
            'гэж бодож байна', 'гэж боддог', 'гэж үзэж байна'
        ]
        
        for phrase in sorted(filler_phrases, key=len, reverse=True):
            text = re.sub(
                r'\b' + re.escape(phrase) + r'\b',
                '',
                text,
                flags=re.IGNORECASE
            )
        
        # Богино хэллэг үгс
        short_fillers = [
            'шүү', 'дээ', 'даа', 'аа', 'ээ', 'өө', 'юу', 
            'гээд', 'тэгээд', 'за', 'тэгэхээр', 'байхаа'
        ]
        
        for filler in short_fillers:
            text = re.sub(
                r'\b' + re.escape(filler) + r'\b',
                '',
                text,
                flags=re.IGNORECASE
            )
        
        # Зөв бичгийн дүрмүүд
        text = re.sub(r'\s+([,.!?:;])', r'\1', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # MARKDOWN ФОРМАТЛАЛТ АРИЛГАХ (ШИНЭ!)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **text** → text
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *text* → text
        text = re.sub(r'^[-•]\s+', '', text, flags=re.MULTILINE)  # - text → text
        text = re.sub(r'#{1,6}\s+', '', text)           # # heading → heading
        
        # Өгүүлбэр эхний үсэг том
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                line = line[0].upper() + line[1:] if len(line) > 1 else line.upper()
                lines.append(line)
        
        return '\n'.join(lines).strip()
    
    def _validate_result_flexible(
        self, 
        original: str, 
        result: str
    ) -> Tuple[bool, List[str]]:
        """
        Уян хатан validation
        """
        errors = []
        
        if len(result.strip()) < 10:
            errors.append(f"Хэт богино")
            return False, errors
        
        ratio = len(result) / len(original) if len(original) > 0 else 0
        if ratio < 0.1:
            errors.append(f"Хэт богино (харьцаа {ratio:.2f})")
        elif ratio > 10.0:
            errors.append(f"Хэт урт (харьцаа {ratio:.2f})")
        
        # Англи хэл
        cyrillic_chars = len(re.findall(r'[А-Яа-яЁёӨөҮү]', result))
        english_chars = len(re.findall(r'[A-Za-z]', result))
        
        if cyrillic_chars > 0 and english_chars > cyrillic_chars * 0.5:
            errors.append(f"Англи хэл их")
        
        # Критик хэллэг үгс
        critical_fillers = ['шүү дээ', 'л байх даа', 'биз дээ']
        found = [f for f in critical_fillers if f in result.lower()]
        
        if found:
            errors.append(f"Хэллэг үгс үлдсэн: {', '.join(found)}")
        
        has_critical = len(found) > 0
        
        return not has_critical, errors
    
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
    print("УТГА ХАДГАЛАХ SUMMARIZER ТЕСТ")
    print("="*60 + "\n")
    
    try:
        summarizer = SLMOnlySummarizer(model="qwen2.5:7b", use_spell_check=False)
        
        # ТЕСТ 1: Огноотой
        test1 = """
        Анна: Би энэ төслийг даваа гарагт дуусгах болно шүү дээ.
        Жон: За тэгээд би шалгаж үзье л байх даа.
        """
        
        print("ТЕСТ 1: Огноотой текст")
        print("Орох:", test1)
        
        result1 = summarizer.formalize_text(test1, debug=True)
        
        print("\nҮр дүн:", result1)
        
        # "даваа гараг" хадгалагдсан эсэх шалгах
        if "даваа гараг" in result1.lower():
            print("✅ Огноо хадгалагдсан")
        else:
            print("❌ Огноо алдагдсан!")
        
        print("\n" + "="*60)
        print("✅ ТЕСТ ДУУСЛАА\n")
        
    except RuntimeError as e:
        print(f"\n❌ АЛДАА:\n{e}\n")