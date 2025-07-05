import os
import asyncio
import types
import pytest

# tests/conftest.py
import os, asyncio, types, pytest
for k in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "CUSTOM_SEARCH_ENGINE_ID"):
    os.environ.setdefault(k, "dummy")

# ---------- OpenAI ダミー ---------- #
class _FakeChat:
    async def create(self, **kw):
        sys_msg = kw["messages"][0]["content"]
        if "helper" in sys_msg:                 # bullets_to_paragraph 用
            txt = "整形済み段落。"
        else:                                   # get_verdict 用
            txt = "SUPPORTED: 根拠十分"
        return types.SimpleNamespace(choices=[types.SimpleNamespace(
            message=types.SimpleNamespace(content=txt)
        )])

class _FakeEmb:
    async def create(self, **kw):
        # 入力数と同じ長さのダミーベクトル配列を返す
        n = len(kw["input"])
        return types.SimpleNamespace(
            data=[types.SimpleNamespace(embedding=[0.0]) for _ in range(n)]
        )

class _FakeOpenAI:
    def __init__(self):
        self.chat = types.SimpleNamespace(completions=_FakeChat())
        self.embeddings = _FakeEmb()

@pytest.fixture(autouse=True)
def _patch_openai(monkeypatch):
    import core.llm as llm, core.search as search
    dummy = _FakeOpenAI()
    monkeypatch.setattr(llm,    "client", dummy, raising=False)
    monkeypatch.setattr(search, "client", dummy, raising=False)
    yield

# ---------- Google 検索ダミー ---------- #
@pytest.fixture(autouse=True)
def _patch_google(monkeypatch):
    async def _fake_search(q, num=5):
        snip = "x" * 60
        return [{"link": "https://ex", "snippet": snip}] * num
    import core.search as search
    monkeypatch.setattr(search, "google_search", _fake_search, raising=False)
    yield

# pytest-asyncio 用イベントループ
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
