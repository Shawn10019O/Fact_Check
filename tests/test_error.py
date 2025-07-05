import pytest
from core.llm import get_verdict

@pytest.mark.asyncio
async def test_get_verdict_error(monkeypatch):
    async def _boom(*a, **k): raise RuntimeError("fail")
    # 強制エラーで ERROR ラベル確認
    monkeypatch.setattr("core.llm.client.chat.completions.create", _boom)
    label, _ = await get_verdict("dummy", model="gpt-3.5-turbo")
    assert label == "ERROR"
