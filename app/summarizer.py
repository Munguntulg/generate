import re

def formalize_text(self, text: str) -> str:
    if chat is None:
        print("⚠️  Ollama байхгүй байна, fallback ашиглана")
        return self._fallback_formalize(text)
    

class OllamaSummarizer:
    """
    Ollama LLM ашиглан Монгол ярианы хэлийг албан бичгийн хэл рүү хөрвүүлнэ
    """
    
    def __init__(self, model: str = "mistral"):
        self.model = model
        self.max_chunk_length = 1500  # Текстийг хэсэглэх хэмжээ
    
    def formalize_text(self, text: str) -> str:
        """
        Ярианы хэлбэрийг албан ёсны бичгийн хэлбэр рүү хөрвүүлэх
        
        Args:
            text: Ярианы хэлбэрийн текст
            
        Returns:
            Албан ёсны бичгийн хэлбэр
        """
        # Урт текст бол хэсэглэнэ
        if len(text) > self.max_chunk_length:
            return self._process_long_text(text)
        
        system_prompt = """Та Монгол хэлний албан протокол бичдэг мэргэжилтэн. 
        
Таны үүрэг:
1. Ярианы хэллэг, хэв маягийг албан ёсны бичгийн хэл рүү хөрвүүлэх
2. Хэллэг үгс (аа, ээ, өө, юу, гээд, тэгээд, за) арилгах
3. Өгүүлбэрийг тодорхой, товч болгох
4. Албан ёсны үг хэллэг ашиглах
5. Протоколд тохирсон бүтэцтэй болгох

ЧУХАЛ: 
- Агуулгыг өөрчлөхгүй, зөвхөн хэв маягийг засах
- Хүний нэр, байгууллагын нэрийг яг хадгалах
- Огноо, тоо, цагийг хадгалах
- Шийдвэр, ажил үүргийг тодорхой илэрхийлэх"""

        user_prompt = f"""Энэ хурлын яриаг албан ёсны протоколын хэлбэрт бич:

{text}

Протокол бичих дүрэм:
- "Анна хэллээ" → "А.Анна дараах санал дэвшүүлэв"
- "Би хийнэ" → "Хариуцан гүйцэтгэнэ"
- "Тэгвэл" → өгүүлбэр эхлүүлэхгүй
- Ажил үүргийг тодорхой илэрхийлэх"""

        try:
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.3,  # Илүү тогтвортой үр дүн
                    "top_p": 0.9,
                }
            )
            
            result = response["message"]["content"].strip()
            
            # Post-processing: албан бус үгсийг цэвэрлэх
            result = self._post_process(result)
            
            return result
            
        except Exception as e:
            print(f"Ollama алдаа: {e}")
            # Fallback: энгийн цэвэрлэлт хийх
            return self._fallback_formalize(text)
    
    def _process_long_text(self, text: str) -> str:
        """
        Урт текстийг хэсэг хэсгээр боловсруулж нэгтгэх
        """
        # Өгүүлбэрээр хуваах
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
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
        
        # Хэсэг бүрийг боловсруулах
        formalized_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"Хэсэг {i+1}/{len(chunks)} боловсруулж байна...")
            formalized = self.formalize_text(chunk)
            formalized_chunks.append(formalized)
        
        return "\n\n".join(formalized_chunks)
    
    def _post_process(self, text: str) -> str:
        """
        Үр дүнг цэвэрлэх, албан бус үгсийг арилгах
        """
        # Үлдсэн хэллэг үгсийг арилгах
        fillers = ["аа", "ээ", "өө", "юу", "гээд", "тэгээд", "за", "тэгэхээр", "ээ нь"]
        for filler in fillers:
            text = re.sub(r'\b' + filler + r'\b', '', text, flags=re.IGNORECASE)
        
        # Давхар хоосон зайг арилгах
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([,.])', r'\1', text)
        
        # Давхар мөр арилгах
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def _fallback_formalize(self, text: str) -> str:
        """
        Ollama ажиллахгүй үед ашиглах энгийн хувилбар
        """
        # Хэллэг үгсийг арилгах
        text = self._post_process(text)
        
        # Өгүүлбэр эхлэлийг засах
        text = re.sub(r'\b(тэгвэл|тэгээд|тэгэхээр)\b', '', text, flags=re.IGNORECASE)
        
        # Өгүүлбэр эхний үсгийг том болгох
        sentences = text.split('.')
        formatted_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                formatted_sentences.append(sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper())
        
        return '. '.join(formatted_sentences) + '.'
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Текстийн товч нэгтгэл үүсгэх (опционал)
        """
        system_prompt = "Монгол хэлний текстийг товч нэгтгэх мэргэжилтэн"
        
        user_prompt = f"""Энэ хурлын протоколыг {max_length} үгээр товчилж нэгтгэ:

{text}

Дараах зүйлсийг заавал дурд:
- Үндсэн хэлэлцсэн асуудал
- Гарсан шийдвэрүүд
- Томоохон ажил үүргүүд"""

        try:
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={"temperature": 0.3}
            )
            
            return response["message"]["content"].strip()
            
        except Exception as e:
            print(f"Summary үүсгэхэд алдаа: {e}")
            # Эхний хэдэн өгүүлбэрийг буцаах
            sentences = text.split('.')[:3]
            return '. '.join([s.strip() for s in sentences if s.strip()]) + '.'