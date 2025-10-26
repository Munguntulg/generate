from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date

# Модулиуд import хийх
from app.preprocess import clean_text, extract_entities
from app.nlp_processor import MongolianNLPProcessor
from app.summarizer import OllamaSummarizer
from app.action_extractor import ActionItemExtractor
from app.exporter import export_enhanced_protocol

app = FastAPI()

# Компонентууд эхлүүлэх
try:
    nlp_processor = MongolianNLPProcessor("mn_model.udpipe")
except:
    nlp_processor = None

summarizer = OllamaSummarizer()
action_extractor = ActionItemExtractor(nlp_processor)

# Request model
class TextInput(BaseModel):
    text: str
    title: str = "Хурлын протокол"
    participants: list[str] = []

@app.post("/generate_protocol")
async def generate_protocol(input_data: TextInput):
    """
    ҮНДСЭН ENDPOINT: Текстээс протокол үүсгэх
    """
    try:
        # 1. Цэвэрлэх
        cleaned = clean_text(input_data.text)
        
        # 2. Нэр илрүүлэх
        if nlp_processor:
            nlp_result = nlp_processor.process_text(cleaned)
            entities = nlp_processor.extract_named_entities(nlp_result)
        else:
            entities = extract_entities(cleaned)
        
        # 3. Албан хэлбэрт хөрвүүлэх
        formalized = summarizer.formalize_text(cleaned)
        
        # 4. Action items
        actions = action_extractor.extract_actions_with_llm(cleaned)
        
        # 5. Протокол бүтэц
        protocol = {
            "title": input_data.title,
            "date": str(date.today()),
            "participants": input_data.participants or entities,
            "body": formalized,
            "action_items": actions,
            "entities": entities
        }
        
        # 6. DOCX үүсгэх
        filename = export_enhanced_protocol(protocol)
        
        return {
            "success": True,
            "file": filename,
            "protocol": protocol
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))