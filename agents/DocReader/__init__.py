import os
from typing import Union
from tempfile import NamedTemporaryFile
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from .extract_pdf import extract_pdf_text
from .extract_docx import extract_docx_text


def _read_path(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".pdf"):
        return extract_pdf_text(path)
    if lower.endswith(".docx"):
        return extract_docx_text(path)
    if lower.endswith(".doc"):
        # Best-effort: require external conversion handled upstream
        # Here just return empty; callers may choose to convert via pandoc first
        return ""
    return ""


def read_resume(file: Union[InMemoryUploadedFile, TemporaryUploadedFile, str]) -> str:
    if isinstance(file, str):
        return _read_path(file)

    name = getattr(file, 'name', 'resume')
    suffix = os.path.splitext(name)[1].lower() or '.pdf'

    # Persist to a temporary file for libraries that need file paths
    with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp.flush()
        return _read_path(tmp.name)
