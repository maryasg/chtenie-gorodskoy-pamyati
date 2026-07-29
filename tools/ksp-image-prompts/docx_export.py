"""Экспорт текста в .docx без метки python-docx в свойствах файла."""

from __future__ import annotations

from pathlib import Path

from docx import Document

DOCX_AUTHOR = "Автор"


def apply_docx_author(doc: Document) -> None:
    props = doc.core_properties
    props.author = DOCX_AUTHOR
    props.last_modified_by = DOCX_AUTHOR


def write_text_docx(text: str, path: Path) -> None:
    doc = Document()
    apply_docx_author(doc)

    blocks = [block.strip() for block in text.replace("\r\n", "\n").split("\n\n")]
    for block in blocks:
        if block:
            doc.add_paragraph(block)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
