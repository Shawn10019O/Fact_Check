from __future__ import annotations
import re
from dataclasses import dataclass, asdict ,field
from pathlib import Path
from typing import List
# 3rd‑party parsing libs
from pptx import Presentation
import PyPDF2
import re
from typing import List


def extract_slides(path: Path) -> List[str]:
    """Return list[str] where index == slide number‑1."""
    ext = path.suffix.lower()
    if ext == ".pptx":
        return _extract_pptx(path)
    if ext == ".pdf":
        return _extract_pdf(path)
    raise ValueError(f"Unsupported file type: {ext}")


def _extract_pptx(path: Path) -> List[str]:
    prs = Presentation(path)
    out: List[str] = []
    for slide in prs.slides:
        parts: List[str] = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                parts.append(shape.text)
        out.append("\n".join(parts))
    return out


def _extract_pdf(path: Path) -> List[str]:
    reader = PyPDF2.PdfReader(path)
    out: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        out.append(txt)
    return out


def sanitize(text: str) -> str:
    # CRLF -> LF に正規化
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.replace("\n", "。")
    return text.strip("。 ")


def get_topic_hint(raw_slide: str, is_pptx: bool, slide_obj=None) -> str | None:
    if is_pptx and slide_obj and getattr(slide_obj.shapes, "title", None):
        return slide_obj.shapes.title.text.strip()
    # fallback: 最初の「。」まで
    first_sentence = re.split(r"(?<=。)", raw_slide, maxsplit=1)[0].strip()
    print(first_sentence)
    return first_sentence[:10] 