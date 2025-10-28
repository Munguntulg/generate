#!/usr/bin/env python3
"""
SLM-ONLY Summarizer - Fallback байхгүй
SLM ажиллахгүй бол алдаа буцаана
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
    Зөвхөн SLM ашиглах - fallback байхгүй
    """
    
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.max_chunk_length = 1500
        
        # SLM бэлэн эсэх шалгах
        if not OLLAMA_AVAILABLE:
            raise RuntimeError(
                "❌ Ollama суулгаагүй байна!\n"
                "   Суулгах: pip install ollama\n"
                "   Model татах: ollama pull qwen2.5:7b"
            )
        
        # Model байгаа эсэх шалгах
        self._verify_model()
        
        print(f"✅ SLM бэлэн: {self.model}")
    
    def _verify_model(self):
        """
        Model байгаа эсэхийг шалгах
        """
        try:
            response = chat(
                model=self.model,
                messages=[{'role': 'user', 'content': 'test'}],
                options={'num_predict': 5}
            )
        except Exception as e:
            error_msg = str(e)
            
            if 'not found' in error_msg or '404' in error_msg:
                raise RuntimeError(
                    f"❌ Model '{self.model}' олдсонгүй!\n"
                    f"   Татах: ollama pull {self.model}\n"
                    f"   Эсвэл өөр model сонгох:\n"
                    f"   - ollama pull mistral\n"
                    f"   - ollama pull gemma2:9b\n"
                    f"   - ollama pull llama3.2:3b"
                )
            else:
                raise RuntimeError(
                    f"❌ Ollama server ажиллахгүй байна!\n"
                    f"   Эхлүүлэх: ollama serve\n"
                    f"   Алдаа: {error_msg}"
                )
    
    def formalize_text(self, text: str) -> str:
        """
        SLM ашиглан албан хэл болгох
        
        Raises:
            RuntimeError: SLM ажиллахгүй бол
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("❌ SLM ажиллахгүй байна (Ollama суулгаагүй)")
        
        # Урт текст бол хэсэглэнэ
        if len(text) > self.max_chunk_length:
            return self._process_long_text(text)
        
        system_prompt = """Та Монгол улсын албан ёсны протокол бичдэг мэргэжилтэн.

🎯 ҮНДСЭН ЗАРЧИМ:
1. Агуулгыг өөрчлөхгүй - зөвхөн хэв маяг засах
2. Хүний нэр, байгууллага, огноо, тоо - ЯАЖ БАЙ ХАДГАЛ
3. Хэллэг үгсийг БҮРЭН АРИЛГА: аа, ээ, өө, шүү дээ, л байх даа, за, тэгээд, гээд
4. Ярианы маягийг албан ёсны бичгийн хэл болгох

📋 ХУВИРГАЛТЫН ДҮРЭМ:
- "Би хийнэ" → "[Нэр] хариуцан гүйцэтгэнэ"
- "хэллээ" → "дэвшүүлэв"
- "бодож байна" → "үзэж байна"
- "болно" → "болох"
- "шүү дээ", "л байх даа" → устгах
- "Тэгвэл", "За" → устгах

⚠️ ЧУХАЛ: 
- Англи хэл рүү ОРЧУУЛАХГҮЙ
- Нэмэлт тайлбар БИЧИХГҮЙ
- Зөвхөн Монгол хэлээр протокол бич

ЖИШЭЭ:
Анхны: "Анна: Би энэ ажлыг даваа гарагт хийх болно шүү дээ."
Протокол: "А.Анна даваа гарагт ажлыг хариуцан гүйцэтгэнэ."

Анхны: "За тэгээд бид үргэлжлүүлье шүү."
Протокол: "Хэлэлцүүлгийг үргэлжлүүлэв."

Анхны: "Тогтоол: Ирэх долоо хоногт дуусгах."
Протокол: "ТОГТСОН: Ирэх долоо хоногт ажлыг дуусгахаар тогтов."
"""

        user_prompt = f"""Энэ хурлын ярианы бичлэгийг албан ёсны протокол болго:

{text}

Зөвхөн албан ёсны протокол бич, нэмэлт тайлбар бичихгүй."""

        try:
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.2,
                    "top_p": 0.85,
                    "num_predict": 2000,
                }
            )
            
            result = response["message"]["content"].strip()
            
            # Quality check
            if not self._is_valid_result(text, result):
                raise RuntimeError(
                    f"❌ SLM чанаргүй үр дүн гаргалаа!\n"
                    f"   - Англи хэл ашигласан эсвэл\n"
                    f"   - Хэт богино/урт үр дүн эсвэл\n"
                    f"   - Хэллэг үгс үлдсэн\n"
                    f"\n   Дахин оролдож байна..."
                )
            
            return self._post_process(result)
            
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise  # Манай алдааг дахин шидэх
            else:
                raise RuntimeError(
                    f"❌ SLM алдаа гарлаа!\n"
                    f"   Model: {self.model}\n"
                    f"   Алдаа: {str(e)}\n"
                    f"\n   Шалгах:\n"
                    f"   1. ollama serve ажиллаж байгаа эсэх\n"
                    f"   2. Model татсан эсэх: ollama list\n"
                    f"   3. RAM хангалттай эсэх (8GB+)"
                )
    
    def _is_valid_result(self, original: str, result: str) -> bool:
        """
        SLM үр дүн зөв эсэхийг шалгах
        """
        # 1. Хоосон эсэх
        if len(result.strip()) < 10:
            return False
        
        # 2. Хэт богино эсвэл урт эсэх
        ratio = len(result) / len(original)
        if ratio < 0.2 or ratio > 3.0:
            return False
        
        # 3. Англи хэл хэтэрхий их эсэх
        english_chars = len(re.findall(r'[a-zA-Z]', result))
        if english_chars > len(result) * 0.3:
            return False
        
        # 4. Хэллэг үгс үлдсэн эсэх
        bad_fillers = ['шүү дээ', 'л байх даа', 'байхаа', 'аа дээ']
        if any(filler in result.lower() for filler in bad_fillers):
            return False
        
        return True
    
    def _post_process(self, text: str) -> str:
        """
        Эцсийн цэвэрлэлт
        """
        # Үлдсэн хэллэг үгс
        fillers = [
            'аа', 'ээ', 'өө', 'юу', 'гээд', 'тэгээд', 'за',
            'тэгэхээр', 'шүү дээ', 'л байх', 'байхаа', 'биз дээ'
        ]
        for filler in fillers:
            text = re.sub(r'\b' + re.escape(filler) + r'\b', '', text, flags=re.IGNORECASE)
        
        # Давхар хоосон зай
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([,.])', r'\1', text)
        
        # Өгүүлбэр эхний үсэг том
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 0:
                line = line[0].upper() + line[1:] if len(line) > 1 else line.upper()
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines).strip()
    
    def _process_long_text(self, text: str) -> str:
        """
        Урт текстийг хэсэглэх
        """
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.max_chunk_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        formalized_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"   Хэсэг {i+1}/{len(chunks)} боловсруулж байна...")
            try:
                formalized = self.formalize_text(chunk)
                formalized_chunks.append(formalized)
            except RuntimeError as e:
                raise RuntimeError(
                    f"❌ Хэсэг {i+1}/{len(chunks)} боловсруулж чадсангүй!\n{str(e)}"
                )
        
        return "\n\n".join(formalized_chunks)


# ============================================
# ТЕСТЛЭХ КОД
# ============================================

def test_slm_only():
    """
    SLM-only режим тестлэх
    """
    print("\n" + "="*60)
    print("SLM-ONLY SUMMARIZER ТЕСТ")
    print("="*60 + "\n")
    
    try:
        # SLM эхлүүлэх (бэлэн эсэхийг шалгана)
        summarizer = SLMOnlySummarizer(model="qwen2.5:7b")
        
        # Тест текст
        test_text = """
        Анна: Би энэ ажлыг даваа гарагт хийх болно шүү дээ.
        Жон: За тэгээд би шалгаж үзье.
        Тогтоол: Ирэх долоо хоногт бүх ажлыг дуусгах.
        """
        
        print("Анхны текст:")
        print(test_text)
        print("\n" + "-"*60 + "\n")
        
        # SLM ашиглах
        result = summarizer.formalize_text(test_text)
        
        print("✅ SLM үр дүн:")
        print(result)
        print("\n" + "="*60 + "\n")
        
        print("✅ АМЖИЛТТАЙ! SLM ажиллаж байна.\n")
        
    except RuntimeError as e:
        print("\n" + "="*60)
        print("❌ АЛДАА ГАРЛАА")
        print("="*60)
        print(f"\n{str(e)}\n")
        return False
    
    return True


if __name__ == "__main__":
    test_slm_only()