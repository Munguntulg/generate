from docx import Document
from docx.shared import Pt, RGBColor
from datetime import datetime

def export_enhanced_protocol(protocol: dict) -> str:
    """
    Протоколыг DOCX файл болгох
    """
    doc = Document()
    
    # 1. Толгой
    doc.add_heading(protocol['title'], level=1)
    
    # 2. Мета мэдээлэл
    doc.add_paragraph(f"Огноо: {protocol['date']}")
    doc.add_paragraph(f"Оролцогчид: {', '.join(protocol['participants'])}")
    
    # 3. Үндсэн агуулга
    doc.add_heading("Хэлэлцсэн асуудал", level=2)
    doc.add_paragraph(protocol['body'])
    
    # 4. Ажил үүргийн хүснэгт
    if protocol.get('action_items'):
        doc.add_heading("Ажил үүрэг ба шийдвэрүүд", level=2)
        
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Light Grid Accent 1'
        
        # Header
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Хариуцагч'
        hdr_cells[1].text = 'Ажил үүрэг'
        hdr_cells[2].text = 'Хугацаа'
        hdr_cells[3].text = 'Төрөл'
        
        # Data rows
        for action in protocol['action_items']:
            row = table.add_row().cells
            row[0].text = action['who']
            row[1].text = action['action']
            row[2].text = action['due']
            row[3].text = 'Шийдвэр' if action['type'] == 'decision' else 'Ажил үүрэг'
    
    # 5. Footer
    doc.add_paragraph(f"Үүсгэсэн: {datetime.now()}")
    
    # 6. Хадгалах
    filename = f"protocol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    doc.save(filename)
    
    return filename