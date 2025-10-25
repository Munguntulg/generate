from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.exporter import export_protocol
from app.summarizer import summarize_mongolian_text

app = FastAPI()

class Transcript(BaseModel):
    title: str
    date: str
    participants: list[str]
    body: str

@app.post("/generate_protocol")
async def generate_protocol(transcript: Transcript):
    try:
        # Ярианы текстийг бичгийн хэлбэрт шилжүүлэх (SLM ашиглана)
        refined_text = summarize_mongolian_text(transcript.body)

        # Албан протокол бэлтгэх
        protocol = {
            "title": transcript.title,
            "date": transcript.date,
            "participants": transcript.participants,
            "body": refined_text
        }

        # DOCX файл үүсгэх
        filename = export_protocol(protocol)

        return {
            "message": "Протокол амжилттай үүсгэлээ",
            "file": filename,
            "protocol": protocol
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
