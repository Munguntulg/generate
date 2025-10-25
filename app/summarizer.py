from transformers import pipeline

# Монгол хэлний SLM ачааллах
summarizer = pipeline(
    "text2text-generation",
    model="tugstugi/mt5-mn",
    tokenizer="tugstugi/mt5-mn"
)

def summarize_mongolian_text(text: str) -> str:
    """
    Ярианы хэлбэртэй монгол текстийг илүү албан, товч тодорхой бичгийн хэлбэрт хөрвүүлнэ.
    """
    instruction = f"Дараах яриаг албан хэлбэрийн протоколын хэсэг болго: {text}"
    result = summarizer(instruction, max_length=300, min_length=80, do_sample=False)
    return result[0]['generated_text']
