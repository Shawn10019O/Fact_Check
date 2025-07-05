from __future__ import annotations
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Any

load_dotenv() 

client = AsyncOpenAI()

# LLM を使った変換・判定処理

BULLET_SYS_MSG = {
    "role": "system",
    "content": (
        "You are a helper that turns given text into formed Japanese sentences **without adding new information**. "
        "Do NOT chenge,insert, remove, or substitute any domain words"
        "Stay as close as possible to the original wording. Output a single "
        "Do not modify or correct any typos or factual mistakes. Preserve the original wording exactly as it appears."
        "paragraph."
        "When writing the paragraph, automatically remove any header or footer "
        "lines that contain boilerplate phrases such as copyright notices, "
        "license information, slide numbers, or terms like “©”, “licensed under”, "
        "“CC BY”, or “講義資料”.\n\n"
        "Ignore any standalone numbers or page markers that are not meaningful "
        "to content."
    ),
}

VERDICT_SYS_MSG = {
    "role": "system",
    "content": (
        "You are a fact-checker. Respond with exactly one of the labels: "
        "SUPPORTED(if all claims are factually correct.), REFUTED(if any claim is factually incorrect.) or NOT_SURE(if accuracy cannot be determined.), then a colon and Japanese rationale.\n"
        "Make judgments only on verifiable facts. Do not infer or hallucinate."
        
    ),
}


# 文章にまとめる
async def bullets_to_paragraph(text: str, model: str) -> str:
    msgs: list[Any] = [
        BULLET_SYS_MSG,
        {"role": "user", "content": text},
    ]

    rsp = await client.chat.completions.create(
        model=model,
        temperature=0,
        messages=msgs,
    )

    raw_msg: str | None = rsp.choices[0].message.content
    return "" if raw_msg is None else raw_msg.strip()


# 段落の真偽判定を取得
async def get_verdict(paragraph: str, model: str) -> tuple[str, str]:
    try:
        rsp = await client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[VERDICT_SYS_MSG, {"role": "user", "content": paragraph}],  # type: ignore[arg-type,list-item]
        )
        raw_msg = rsp.choices[0].message.content or ""
    except Exception:
        return "ERROR", ""
    if ":" in raw_msg:
        label, reason = raw_msg.split(":", 1)
        return label.strip().upper(), reason.strip()
    return "ERROR", raw_msg.strip()

# 「。」で区切る。
def split_sentences(text: str) -> list[str]: 
    return [s.strip() for s in re.split(r'(?<=。)', text) if s.strip()]

# SUPPORTED な文のみ抽出
async def extract_correct_sentences(
    paragraph: str,
    model: str,
    topic_hint: str | None = None, 
) -> list[str]:
    corrects = []
    for sent in split_sentences(paragraph):
        query = f"{topic_hint}: {sent}" if topic_hint else sent
        label, _ = await get_verdict(query, model)
        if label == "SUPPORTED":
            corrects.append(sent)     
    return corrects
