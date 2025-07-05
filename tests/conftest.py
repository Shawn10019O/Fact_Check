import os
import asyncio
import types
import pytest

for k in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "CUSTOM_SEARCH_ENGINE_ID"):
    os.environ.setdefault(k, "dummy")

# OpenAI
class _FakeChat:
    async def create(self, **kwargs):

        if kwargs["messages"][0]["role"] == "system" and "helper" in kwargs["messages"][0]["content"]:
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="整形済み段落。"))]
            )
        
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="SUPPORTED: 根拠十分"))]
        )

class _FakeOpenAI:                                # client の代替
    def __init__(self): self.chat = types.SimpleNamespace(completions=_FakeChat())

@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import core.llm as llm
    monkeypatch.setattr(llm, "client", _FakeOpenAI())
    yield

# Google 検索
@pytest.fixture(autouse=True)
def patch_google(monkeypatch):
    async def _fake_search(q, num=5):
        snippet = "dummy snippet long enough to pass 50-char filter " * 2
        return [{"title": "t", "snippet": snippet, "link": "https://ex.com"}] * num
    import core.search as cs
    monkeypatch.setattr(cs, "google_search", _fake_search)
    yield

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
