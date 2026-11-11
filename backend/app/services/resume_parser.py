from io import BytesIO
from zipfile import ZipFile, BadZipFile
from pypdf import PdfReader
from docx import Document

MAX_BYTES = 10 * 1024 * 1024


def extract(data: bytes, filename: str):
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Upload a nonempty PDF or DOCX up to 10 MB")
    suffix = filename.lower().rsplit(".", 1)[-1]
    try:
        if suffix == "pdf" and data.startswith(b"%PDF-"):
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted or len(reader.pages) > 100:
                raise ValueError(
                    "Encrypted PDFs and PDFs over 100 pages are unsupported"
                )
            result = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix == "docx" and data.startswith(b"PK"):
            with ZipFile(BytesIO(data)) as archive:
                if (
                    sum(item.file_size for item in archive.infolist())
                    > 30 * 1024 * 1024
                ):
                    raise ValueError("DOCX expands beyond the allowed size")
            doc = Document(BytesIO(data))
            result = "\n".join(
                [p.text for p in doc.paragraphs]
                + [c.text for t in doc.tables for r in t.rows for c in r.cells]
            )
        else:
            raise ValueError("Only valid PDF and DOCX files are supported")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The document could not be read") from exc
    if len(result.strip()) < 30:
        raise ValueError(
            "No readable resume text found. Use a text-based document, not a scan."
        )
    return result[:60000]
