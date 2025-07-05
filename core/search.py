from __future__ import annotations
import os
import json
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv
import numpy as np
import aiohttp 
import asyncio
import hashlib
from typing import Dict, List
from core.models import SuspiciousClaim


load_dotenv() 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")
CACHE_DB = Path(".gsearch_cache.json")
client = AsyncOpenAI()

_cache = {}
if CACHE_DB.exists():
    _cache = json.loads(CACHE_DB.read_text())

def _key(q):
    return hashlib.sha256(q.encode()).hexdigest()

def save_cache():
    CACHE_DB.write_text(json.dumps(_cache, ensure_ascii=False, indent=2))

async def google_search(query: str, num: int = 5) -> List[Dict[str, str]]:
    k = _key(query)
    if k in _cache:
        return _cache[k]

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": CUSTOM_SEARCH_ENGINE_ID, "q": query, "num": num}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as sess:
        async with sess.get(url, params=params) as resp:
            data = await resp.json()
            items = data.get("items", [])
            _cache[k] = items
            return items
        
async def fetch_and_filter_snippets(claim: str, k: int = 5) -> List[Dict[str, str]]:
    items = await google_search(claim)
    snippets = [
        {"url": it["link"], "snippet": it["snippet"]}
        for it in items
        if len(it.get("snippet", "")) > 50
    ][:k]

    # Embedding 類似度でスコアリング
    inputs = [claim] + [s["snippet"] for s in snippets]
    embs = await client.embeddings.create(input=inputs, model="text-embedding-3-small")
    c_emb = np.array(embs.data[0].embedding)
    s_embs = [np.array(e.embedding) for e in embs.data[1:]]
    sims  = [float((c_emb @ s) / (np.linalg.norm(c_emb)*np.linalg.norm(s))) for s in s_embs]

    evidences = [
        s for s, sim in sorted(zip(snippets, sims), key=lambda x: x[1], reverse=True) if sim > 0.7
    ]
    return evidences

async def enrich_and_filter(sentences: list[str],topic_hint: str | None = None,) -> list[SuspiciousClaim]:
    async def enrich(sent:str):
        query = f"{topic_hint}: {sent}" if topic_hint else sent
        evids = await fetch_and_filter_snippets(query)
        if not evids:      # 証拠ゼロ ⇒ suspicious
            return SuspiciousClaim(sent)
        return None

    batch = await asyncio.gather(*(enrich(s) for s in sentences))
    return [c for c in batch if c] 