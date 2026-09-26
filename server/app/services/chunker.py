"""
Document chunking service - splits documents into sections/clauses
with stable IDs and source offsets for mapping back to original content.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass


@dataclass
class Clause:
    """A clause extracted from a document."""

    clause_id: str
    document_id: str
    text: str
    char_count: int
    page_number: int
    start_pos: int
    end_pos: int
    clause_index: int
    category: str | None = None
    title: str | None = None
    heading_level: int | None = None


class DocumentChunker:
    """
    Split documents into semantic chunks (sections/clauses).
    Uses numbered headings, common legal patterns, and heuristics.
    """

    def __init__(self, max_chunk_chars: int = 5000) -> None:
        self.max_chunk_chars = max_chunk_chars

    def _find_section_boundaries(self, text: str) -> list[tuple[int, int, str | None]]:
        """
        Find positions of section boundaries (headings, numbered sections).
        Returns list of (start, end, heading_text) tuples.
        """
        boundaries = []
        lines = text.split("\n")

        current_section_start = 0
        in_section = False
        section_pattern = re.compile(
            r"^(\d+\.\s+.+|^ARTICLE\s+\d+|^SECTION\s+\d+|^TITLE\s+\d+|^[A-Z][A-Z\s]{5,}:)",
            re.MULTILINE,
        )

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            if section_pattern.match(line_stripped):
                if in_section:
                    prev_position = current_section_start
                    prev_text = text[prev_position:]
                    next_newline = prev_text.find("\n\n")
                    if next_newline > 0:
                        section_end = prev_position + next_newline
                    else:
                        section_end = len(text)
                    boundaries.append((current_section_start, section_end, None))

                current_section_start = self._line_position(text, i)
                in_section = True
            elif in_section and len(line_stripped) > 100:
                cumulative = sum(len(ln) + 1 for ln in lines[:i + 1])
                if cumulative - current_section_start > self.max_chunk_chars:
                    boundaries.append((current_section_start, cumulative - len(line_stripped) - 1, None))
                    current_section_start = cumulative - len(line_stripped) - 1
                    in_section = False

        if in_section:
            boundaries.append((current_section_start, len(text), None))

        return boundaries

    def _line_position(self, text: str, line_index: int) -> int:
        """Get character position of a given line index in the text."""
        lines = text.split("\n")
        pos = 0
        for i in range(line_index):
            pos += len(lines[i]) + 1
        return pos

    def _split_into_paragraphs(self, text: str) -> list[tuple[int, int]]:
        """Split text into paragraph boundaries."""
        paragraphs = []
        lines = text.split("\n")

        current_para_start = 0
        para_lines = 0

        for i, line in enumerate(lines):
            if line.strip():
                para_lines += 1
            else:
                if para_lines > 0:
                    para_end = self._line_position(text, i)
                    paragraphs.append((current_para_start, para_end))
                    current_para_start = para_end
                    para_lines = 0

        if para_lines > 0:
            paragraphs.append((current_para_start, len(text)))

        return paragraphs

    def chunk_document(
        self,
        document_id: str,
        chunks: list[dict],
    ) -> list[Clause]:
        """
        Process document chunks into refined clause units.

        Args:
            document_id: Unique identifier for the document
            chunks: List of chunk dictionaries with text, page_number, start_pos, end_pos

        Returns:
            List of Clause objects with stable IDs and source offsets
        """
        clauses: list[Clause] = []
        clause_index = 0

        for chunk in chunks:
            text = chunk.get("text", "")
            page_number = chunk.get("page_number", 1)
            chunk_start_pos = chunk.get("start_pos", 0)

            section_boundaries = self._find_section_boundaries(text)

            if not section_boundaries:
                section_boundaries = [(0, len(text), None)]

            for i, (start, end, heading) in enumerate(section_boundaries):
                section_text = text[start:end]

                if not section_text.strip():
                    continue

                paragraph_bounds = self._split_into_paragraphs(section_text)

                for para_start, para_end in paragraph_bounds:
                    para_text = section_text[para_start:para_end].strip()
                    if not para_text:
                        continue

                    abs_start = chunk_start_pos + para_start
                    abs_end = chunk_start_pos + para_end

                    clause = Clause(
                        clause_id=str(uuid.uuid4()),
                        document_id=document_id,
                        text=para_text,
                        char_count=len(para_text),
                        page_number=page_number,
                        start_pos=abs_start,
                        end_pos=abs_end,
                        clause_index=clause_index,
                        title=heading,
                    )
                    clauses.append(clause)
                    clause_index += 1

        return clauses