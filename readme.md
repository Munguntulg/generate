# 🇲🇳 Монгол Протокол Үүсгэх Систем

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Хурлын ярианы бичлэгийг **автоматаар албан протокол** болгон хөрвүүлдэг систем.

---

## ✨ Онцлог

- ✅ **SLM (qwen2.5:7b)** ашиглан Монгол хэл дэмждэг
- ✅ **Хэллэг үгс автомат арилгах** (аа, ээ, шүү дээ гэх мэт)
- ✅ **Action items илрүүлэх** - Ажил үүрэг, шийдвэрүүд
- ✅ **DOCX файл үүсгэх** - Албан форматтай протокол
- ✅ **REST API** - FastAPI ашигласан
- ✅ **UDPipe дэмжлэг** - Named Entity Recognition (опционал)

---

## 🚀 Богино танилцуулга

### Жишээ:

**Орох:**
```
Анна: Би энэ ажлыг даваа гарагт хийх болно шүү дээ.
Жон: За тэгээд би шалгаж үзье.
Тогтоол: Ирэх долоо хоногт бүх ажлыг дуусгах.
```

**Гарах (protocol_20241215_143022.docx):**
```
ХУРЛЫН ПРОТОКОЛ

Огноо: 2024-12-15
Оролцогчид: Анна, Жон

Хэлэлцсэн асуудал:
А.Анна даваа гарагт ажлыг хариуцан гүйцэтгэх болов.
Хэлэлцүүлгийг үргэлжлүүлэв.
ТОГТСОН: Ирэх долоо хоногт бүх ажлыг дуусгахаар тогтов.

Ажил үүрэг ба шийдвэрүүд:
| Хариуцагч | Ажил үүрэг | Хугацаа | Төрөл |
|-----------|-----------|---------|-------|
| Анна | Ажлыг гүйцэтгэх | даваа гараг | Ажил үүрэг |
| Хурлын шийдвэр | Бүх ажлыг дуусгах | ирэх долоо хоног | Шийдвэр |
```

---

## 📦 Суулгалт

### Шаардлага:
- Python 3.8+
- Ollama + qwen2.5:7b модель
- 8GB+ RAM

### 1️⃣ Repository татах

```bash
git clone https://github.com/yourusername/mongolian-protocol-generator.git
cd mongolian-protocol-generator
```

### 2️⃣ Virtual environment үүсгэх

```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# Windows: venv\Scripts\activate
```

### 3️⃣ Dependencies суулгах

```bash
pip install -r requirements.txt
```

### 4️⃣ Ollama суулгах

```bash
# Mac/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: https://ollama.ai/download аас татах

# Model татах
ollama pull qwen2.5:7b
```

### 5️⃣ Environment variables (опционал)

```bash
cp .env.example .env
# .env файлыг засах
```

---

## 🎯 Хэрэглэх

### Хувилбар 1: Python скрипт

```bash
# Энгийн тест
python3 test_protocol.py

# Өөр файл заах
python3 test_protocol.py custom_text.json
```

### Хувилбар 2: API server

```bash
# Server эхлүүлэх
uvicorn app.main:app --reload

# Өөр терминал дээр тестлэх
curl -X POST http://localhost:8000/generate_protocol \
     -H "Content-Type: application/json" \
     -d @text.json
```

### Хувилбар 3: Python модуль

```python
from app.summarizer import SLMOnlySummarizer
from app.action_extractor import SLMOnlyActionExtractor
from app.exporter import export_enhanced_protocol

# Текст боловсруулах
summarizer = SLMOnlySummarizer()
formalized = summarizer.formalize_text("Анна: Би хийнэ")

# Action items
extractor = SLMOnlyActionExtractor()
actions = extractor.extract_actions_with_llm(text)

# Протокол үүсгэх
protocol = {
    "title": "Хурлын протокол",
    "body": formalized,
    "action_items": actions,
    # ...
}
filename = export_enhanced_protocol(protocol)
```

---

## 📁 Файлын бүтэц

```
mongolian-protocol-generator/
├── .env.example              # Environment variables жишээ
├── .gitignore               # Git ignore файл
├── README.md                # Энэ файл
├── requirements.txt         # Python dependencies
├── text.json                # Жишээ өгөгдөл
├── test_protocol.py         # Тест скрипт
├── test_ollama_connection.py
│
├── app/
│   ├── __init__.py
│   ├── config.py            # Тохиргоо
│   ├── main.py              # FastAPI endpoints
│   ├── summarizer.py        # SLM summarization
│   ├── action_extractor.py  # Action items extraction
│   ├── nlp_processor.py     # UDPipe NLP
│   ├── preprocess.py        # Текст цэвэрлэх
│   ├── exporter.py          # DOCX export
│   └── prompts/
│       ├── extract_prompt.txt
│       └── summarize_prompt.txt
│
└── tests/                   # Unit tests (TODO)
    └── __init__.py
```

---

## 🔧 API Endpoints

### GET `/`
API мэдээлэл

### GET `/health`
Системийн төлөв шалгах

### POST `/generate_protocol`
Протокол үүсгэх

**Request:**
```json
{
  "text": "Хурлын текст",
  "title": "Хурлын протокол",
  "participants": ["Анна", "Жон"]
}
```

**Response:**
```json
{
  "success": true,
  "file": "protocol_20241215_143022.docx",
  "protocol": { ... },
  "stats": {
    "original_length": 500,
    "formalized_length": 450,
    "entities_found": 2,
    "actions_found": 3
  }
}
```

---

## ⚙️ Тохиргоо

Environment variables (.env файл):

```bash
SLM_MODEL=qwen2.5:7b
SLM_TEMPERATURE=0.1
UDPIPE_MODEL=mn_model.udpipe
API_PORT=8000
```

Дэлгэрэнгүй: [.env.example](.env.example) харах

---

## 🧪 Тест

```bash
# Ollama холболт шалгах
python3 test_ollama_connection.py

# Бүтэн систем тест
python3 test_protocol.py

# Unit tests (TODO)
pytest tests/
```

---

## 🐛 Түгээмэл асуудал

### 1. Ollama ажиллахгүй байна

```bash
# Шалгах
ollama list

# Эхлүүлэх
ollama serve

# Model татах
ollama pull qwen2.5:7b
```

### 2. UDPipe модель олдохгүй

UDPipe байхгүй ч систем ажиллана (Regex ашиглана). Хэрэв татахыг хүсвэл:

```bash
wget https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/mongolian-udtb-ud-2.5-191206.udpipe -O mn_model.udpipe
```

### 3. RAM дутагдаж байна

Бага модель ашиглах:
```bash
ollama pull qwen2.5:3b  # 7b оронд 3b
```

---

## 🤝 Хөгжүүлэлтэд оролцох

1. Fork хийх
2. Feature branch үүсгэх (`git checkout -b feature/amazing-feature`)
3. Commit хийх (`git commit -m 'feat: Amazing feature нэмсэн'`)
4. Push хийх (`git push origin feature/amazing-feature`)
5. Pull Request үүсгэх

---

## 📝 License

MIT License - [LICENSE](LICENSE) файл харах

---

## 👥 Холбоо барих

- GitHub Issues: Асуудал гарвал энд бичих
- Email: moogii2032@gmail.com

---

##

- [Ollama](https://ollama.ai/) - Локал LLM
- [UDPipe](https://ufal.mff.cuni.cz/udpipe) - NLP боловсруулалт
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework

---

**⭐ Хэрэв төсөл таалагдвал star өгнө үү!**