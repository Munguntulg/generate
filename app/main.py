from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date

# Модулиуд import хийх
from app.preprocess import clean_text, extract_entities

# SLM-only imports
try:
    from app.summarizer import SLMOnlySummarizer
    from app.action_extractor import SLMOnlyActionExtractor
    SLM_AVAILABLE = True
except ImportError as e:
    SLM_AVAILABLE = False
    SLM_ERROR = str(e)

from app.exporter import export_enhanced_protocol

app = FastAPI(
    title="Mongolian Protocol Generator",
    description="Монгол ярианы текстийг албан протокол болгох систем (SLM-only)",
    version="2.0.0"
)

# NLP processor (optional)
try:
    from app.nlp_processor import MongolianNLPProcessor
    nlp_processor = MongolianNLPProcessor("mn_model.udpipe")
except:
    nlp_processor = None
    print("⚠️  UDPipe байхгүй, rule-based entity extraction ашиглана")

# SLM компонентууд эхлүүлэх
if not SLM_AVAILABLE:
    print(f"❌ SLM модулиуд ачаалагдсангүй: {SLM_ERROR}")
    summarizer = None
    action_extractor = None
else:
    try:
        summarizer = SLMOnlySummarizer(model="qwen2.5:7b")
        action_extractor = SLMOnlyActionExtractor(nlp_processor)
        print("✅ SLM систем бэлэн")
    except RuntimeError as e:
        print(f"❌ SLM эхлүүлэхэд алдаа: {e}")
        summarizer = None
        action_extractor = None


# Request model
class TextInput(BaseModel):
    text: str
    title: str = "Хурлын протокол"
    participants: list[str] = []


@app.get("/")
async def root():
    """
    API мэдээлэл
    """
    return {
        "service": "Mongolian Protocol Generator",
        "version": "2.0.0",
        "mode": "SLM-only (No fallback)",
        "slm_status": "ready" if summarizer else "not_ready",
        "model": "qwen2.5:7b" if summarizer else None,
        "endpoints": {
            "generate": "/generate_protocol",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """
    Системийн төлөв шалгах
    """
    status = {
        "status": "healthy" if summarizer else "unhealthy",
        "components": {
            "ollama": summarizer is not None,
            "summarizer": summarizer is not None,
            "action_extractor": action_extractor is not None,
            "nlp_processor": nlp_processor is not None
        }
    }
    
    if not summarizer:
        status["error"] = "SLM ажиллахгүй байна"
        status["solution"] = [
            "1. Ollama суулгах: pip install ollama",
            "2. Ollama server эхлүүлэх: ollama serve",
            "3. Model татах: ollama pull qwen2.5:7b"
        ]
    
    return status


@app.post("/generate_protocol")
async def generate_protocol(input_data: TextInput):
    """
    ҮНДСЭН ENDPOINT: Текстээс протокол үүсгэх (SLM-only)
    
    SLM ажиллахгүй бол 503 Service Unavailable буцаана
    """
    
    # SLM бэлэн эсэх шалгах
    if not summarizer or not action_extractor:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SLM систем ажиллахгүй байна",
                "message": "Ollama болон qwen2.5:7b model шаардлагатай",
                "solution": [
                    "1. Ollama суулгах: pip install ollama",
                    "2. Terminal дээр: ollama serve",
                    "3. Өөр terminal дээр: ollama pull qwen2.5:7b",
                    "4. API дахин эхлүүлэх"
                ]
            }
        )
    
    try:
        # 1. Цэвэрлэх
        print(f"1️⃣  Текст цэвэрлэж байна...")
        cleaned = clean_text(input_data.text)
        
        # 2. Нэр илрүүлэх
        print(f"2️⃣  Нэр илрүүлж байна...")
        if nlp_processor:
            nlp_result = nlp_processor.process_text(cleaned)
            entities = nlp_processor.extract_named_entities(nlp_result)
        else:
            entities = extract_entities(cleaned)
        
        # 3. SLM: Албан хэлбэрт хөрвүүлэх
        print(f"3️⃣  SLM ашиглан албан хэл болгож байна...")
        try:
            formalized = summarizer.formalize_text(cleaned)
        except RuntimeError as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "SLM албан хэл болгож чадсангүй",
                    "message": str(e),
                    "step": "formalization"
                }
            )
        
        # 4. SLM: Action items гаргах
        print(f"4️⃣  SLM ашиглан ажил үүрэг илрүүлж байна...")
        try:
            actions = action_extractor.extract_actions_with_llm(cleaned)
        except RuntimeError as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "SLM ажил үүрэг илрүүлж чадсангүй",
                    "message": str(e),
                    "step": "action_extraction"
                }
            )
        
        # 5. Протокол бүтэц
        print(f"5️⃣  Протокол бүтэц үүсгэж байна...")
        protocol = {
            "title": input_data.title,
            "date": str(date.today()),
            "participants": input_data.participants or entities,
            "body": formalized,
            "action_items": actions,
            "entities": entities,
            "metadata": {
                "original_length": len(input_data.text),
                "processed_length": len(formalized),
                "model": "qwen2.5:7b",
                "mode": "SLM-only"
            }
        }
        
        # 6. DOCX үүсгэх
        print(f"6️⃣  DOCX файл үүсгэж байна...")
        filename = export_enhanced_protocol(protocol)
        
        print(f"✅ Амжилттай!")
        
        return {
            "success": True,
            "file": filename,
            "protocol": protocol,
            "stats": {
                "original_length": len(input_data.text),
                "formalized_length": len(formalized),
                "entities_found": len(entities),
                "actions_found": len(actions),
                "processing_mode": "SLM-only"
            }
        }
        
    except HTTPException:
        raise  # HTTP алдааг дахин шидэх
    except Exception as e:
        # Бусад алдаа
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Протокол үүсгэхэд алдаа гарлаа",
                "message": str(e),
                "type": type(e).__name__
            }
        )


@app.post("/test_slm")
async def test_slm():
    """
    SLM тестлэх endpoint
    """
    if not summarizer:
        raise HTTPException(
            status_code=503,
            detail="SLM ажиллахгүй байна"
        )
    
    test_text = "Би энэ ажлыг хийх болно шүү дээ."
    
    try:
        result = summarizer.formalize_text(test_text)
        
        return {
            "success": True,
            "test_input": test_text,
            "test_output": result,
            "model": "qwen2.5:7b"
        }
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SLM тест амжилтгүй",
                "message": str(e)
            }
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Server эхлэхэд
    """
    print("\n" + "="*60)
    print("MONGOLIAN PROTOCOL GENERATOR API")
    print("="*60)
    print(f"Mode: SLM-only (No fallback)")
    print(f"Model: qwen2.5:7b")
    
    if summarizer:
        print(f"Status: ✅ Бэлэн")
    else:
        print(f"Status: ❌ SLM ажиллахгүй")
        print(f"\nШалгах:")
        print(f"  1. ollama serve")
        print(f"  2. ollama pull qwen2.5:7b")
    
    print("="*60 + "\n")


# Error handlers
@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    """
    RuntimeError-ийг HTTP 500 болгох
    """
    return HTTPException(
        status_code=500,
        detail={
            "error": "Системийн алдаа",
            "message": str(exc)
        }
    )