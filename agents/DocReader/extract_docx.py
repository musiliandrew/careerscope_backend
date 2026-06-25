from docx import Document


def extract_docx_text(docx_path):
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])
