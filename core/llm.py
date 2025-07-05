from __future__ import annotations
import re
from typing import List
from openai import AsyncOpenAI
import re
from typing import List
from dotenv import load_dotenv

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
    rsp = await client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[BULLET_SYS_MSG, {"role": "user", "content": text}],
    )
    return rsp.choices[0].message.content.strip()

# 事実判定を実行
async def get_verdict(paragraph: str, model: str) -> tuple[str, str]:
    rsp = await client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[VERDICT_SYS_MSG, {"role": "user", "content": paragraph}],
    )
    raw = rsp.choices[0].message.content.strip()
    if ":" in raw:
        label, reason = raw.split(":", 1)
        return label.strip().upper(), reason.strip()
    return "ERROR", raw

# 「。」で区切る。
def split_sentences(text: str) -> List[str]: 
    return [s.strip() for s in re.split(r'(?<=。)', text) if s.strip()]

# SUPPORTED な文のみ抽出
async def extract_correct_sentences(
    paragraph: str,
    model: str,
    topic_hint: str | None = None, 
) -> List[str]:
    corrects = []
    for sent in split_sentences(paragraph):
        query = f"{topic_hint}: {sent}" if topic_hint else sent
        label, _ = await get_verdict(query, model)
        if label == "SUPPORTED":
            corrects.append(sent)     
    return corrects
