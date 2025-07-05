# tests/conftest.py
import os
import asyncio
import types
import pytest

for k in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "CUSTOM_SEARCH_ENGINE_ID"):
    os.environ.setdefault(k, "dummy")

# ---------- OpenAI ダミー ----------
class _FakeChat:
    async def create(self, **kwargs):
        # bullets_to_paragraph 用
        if "helper" in kwargs["messages"][0]["content"]:
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="整形済み段落。"))]
            )
        # get_verdict / split 文 用
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="SUPPORTED: 根拠十分"))]
        )

class _FakeEmbeddings:
    async def create(self, *, input, model):
        vec = [1.0, 0.0, 0.0]                       
        data = [types.SimpleNamespace(embedding=vec) for _ in input]
        return types.SimpleNamespace(data=data)

class _FakeOpenAI:
    def __init__(self):
        self.chat       = types.SimpleNamespace(completions=_FakeChat())
        self.embeddings = _FakeEmbeddings()  

@pytest.fixture(autouse=True)
def _patch_openai(monkeypatch):
    import core.llm as llm
    import core.search as search
    dummy = _FakeOpenAI()
    # llm 側
    monkeypatch.setattr(llm,    "client", dummy, raising=False)
    # search 側（Embedding 用）
    monkeypatch.setattr(search, "client", dummy, raising=False)
    yield

# ---------- Google 検索 ----------
@pytest.fixture(autouse=True)
def _patch_google(monkeypatch):
    async def _fake_search(q, num=5):
        snippet = "dummy snippet long enough to pass 50-char filter " * 2
        return [{"title": "t", "snippet": snippet, "link": "https://ex.com"}] * num
    import core.search as cs
    monkeypatch.setattr(cs, "google_search", _fake_search)
    yield

# ---------- pytest-asyncio ----------
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
