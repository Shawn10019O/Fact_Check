import pytest
from core.search import enrich_and_filter

@pytest.mark.asyncio
async def test_enrich_and_filter():
    suspicious = await enrich_and_filter(["テスト文"])
    # google_search モックがヒット → suspicious 空
    assert suspicious == []
