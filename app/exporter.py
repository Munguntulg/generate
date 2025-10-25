from docx import Document

def export_protocol(protocol):
    doc = Document()

    doc.add_heading(protocol['title'], level=1)
    doc.add_paragraph(f"Огноо: {protocol['date']}")
    doc.add_paragraph(f"Оролцогчид: {', '.join(protocol['participants'])}")
    doc.add_paragraph("")
    doc.add_heading("Хэлэлцсэн асуудал:", level=2)
    doc.add_paragraph(protocol['body'])

    filename = "protocol_mn.docx"
    doc.save(filename)
    return filename
