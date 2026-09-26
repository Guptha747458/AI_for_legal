"""
Core document processing services for LegalLens.
"""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.core.settings import settings
from app.core.cleanup import remove_path_safely


class TextExtractor(ABC):
    """Abstract base class for text extraction."""

    @abstractmethod
    def extract_text(self, file_path: Path) -> list[dict[str, Any]]:
        pass


class TxtExtractor(TextExtractor):
    """Extract text from plain text files."""

    def extract_text(self, file_path: Path) -> list[dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return [
            {
                "text": content,
                "page_number": 1,
                "start_pos": 0,
                "end_pos": len(content),
                "char_count": len(content),
            }
        ]


class DocxExtractor(TextExtractor):
    """Extract text from DOCX files."""

    def extract_text(self, file_path: Path) -> list[dict[str, Any]]:
        try:
            import docx
        except ImportError:
            raise ImportError("python-docx is required to parse DOCX files")

        with open(file_path, "rb") as f:
            doc = docx.Document(f)
        chunks = []

        for para in doc.paragraphs:
            if para.text:
                chunk_text = para.text

                chunks.append(
                    {
                        "text": chunk_text,
                        "page_number": 1,
                        "start_pos": 0,
                        "end_pos": len(chunk_text),
                        "char_count": len(chunk_text),
                    }
                )

        if not chunks:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if content:
                chunks.append(
                    {
                        "text": content,
                        "page_number": 1,
                        "start_pos": 0,
                        "end_pos": len(content),
                        "char_count": len(content),
                    }
                )

        return chunks


class PdfExtractor(TextExtractor):
    """Extract text from PDF files."""

    def extract_text(self, file_path: Path) -> list[dict[str, Any]]:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber is required to parse PDF files")

        chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue

                chunks.append(
                    {
                        "text": text,
                        "page_number": page_num,
                        "start_pos": 0,
                        "end_pos": len(text),
                        "char_count": len(text),
                    }
                )

        if not chunks:
            try:
                from PyPDF2 import PdfReader

                with open(file_path, "rb") as f:
                    reader = PdfReader(f)
                    all_text = ""
                    for page in reader.pages:
                        all_text += page.extract_text() or ""
                    if all_text:
                        chunks.append(
                            {
                                "text": all_text,
                                "page_number": 1,
                                "start_pos": 0,
                                "end_pos": len(all_text),
                                "char_count": len(all_text),
                            }
                        )
            except ImportError:
                pass

        return chunks


class DocumentProcessor:
    """Process uploaded documents and extract text with metadata."""

    def __init__(self) -> None:
        self.extractors: dict[str, TextExtractor] = {
            "txt": TxtExtractor(),
            "docx": DocxExtractor(),
            "pdf": PdfExtractor(),
        }

    def _get_file_type(self, filename: str | None) -> str:
        if not filename or "." not in filename:
            raise ValueError("Uploaded file must have a .pdf, .docx, or .txt extension")
        ext = filename.lower().rsplit(".", 1)[-1]
        return ext

    def _get_text_extractor(self, file_type: str) -> TextExtractor:
        if file_type not in self.extractors:
            raise ValueError(
                f"Unsupported file type: {file_type}. Supported types: {list(self.extractors.keys())}"
            )
        return self.extractors[file_type]

    def _calculate_text_position(self, chunks: list[dict], current_chunk_index: int) -> dict:
        total_pos = 0
        for i, chunk in enumerate(chunks):
            if i == current_chunk_index:
                return {
                    "start_pos": total_pos,
                    "end_pos": total_pos + len(chunk["text"]),
                    "page_number": chunk["page_number"],
                }
            total_pos += len(chunk["text"]) + 1

        return {"start_pos": 0, "end_pos": len(chunks[current_chunk_index]["text"]), "page_number": 1}

    async def process_file(self, file: UploadFile, content: bytes | None = None) -> dict[str, Any]:
        """
        Process an uploaded file and extract text with metadata.

        Returns:
            dict with document_id, filename, file_type, chunks, and metadata.
        """
        file_type = self._get_file_type(file.filename)
        extractor = self._get_text_extractor(file_type)

        file_id = str(uuid.uuid4())
        upload_dir = settings.upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{file_id}.{file_type}"

        try:
            with open(file_path, "wb") as f:
                f.write(content if content is not None else await file.read())

            chunks = extractor.extract_text(file_path)
        finally:
            remove_path_safely(file_path)

        processed_chunks = []
        for i, chunk in enumerate(chunks):
            pos_info = self._calculate_text_position(chunks, i)

            processed_chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": file_id,
                    "text": chunk["text"],
                    "char_count": len(chunk["text"]),
                    "page_number": pos_info["page_number"],
                    "start_pos": pos_info["start_pos"],
                    "end_pos": pos_info["end_pos"],
                }
            )

        return {
            "document_id": file_id,
            "filename": file.filename,
            "file_type": file_type,
            "chunks": processed_chunks,
            "total_chars": sum(chunk["char_count"] for chunk in processed_chunks),
            "chunk_count": len(processed_chunks),
        }


# Global instance
processor = DocumentProcessor()
