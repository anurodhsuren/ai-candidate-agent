"""Safe, in-memory resume text extraction helpers."""

from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

MAX_RESUME_BYTES = 5 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def extract_resume_text(filename: str | None, content: bytes) -> str:
    """Extract text from an uploaded PDF, DOCX, or UTF-8 text resume.

    Files are never saved to disk.  The caller is responsible for passing a
    validated upload and for handling ValueError as a client-facing error.
    """
    extension = Path(filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Upload a PDF, DOCX, or TXT resume.")
    if not content:
        raise ValueError("The uploaded resume is empty.")
    if len(content) > MAX_RESUME_BYTES:
        raise ValueError("The resume must be 5 MB or smaller.")

    try:
        if extension == ".pdf":
            reader = PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif extension == ".docx":
            document = Document(BytesIO(content))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            text = content.decode("utf-8")
    except Exception as exc:
        raise ValueError("This resume could not be read. Try a text-based PDF, DOCX, or TXT file.") from exc

    text = text.strip()
    if len(text) < 40:
        raise ValueError("Too little text could be extracted from this resume.")
    return text
