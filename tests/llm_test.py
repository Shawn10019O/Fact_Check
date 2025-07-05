import pytest
from core.llm import split_sentences, extract_correct_sentences

def test_split_sentences():                    # 単体テスト
    assert split_sentences("A。B。") == ["A。", "B。"]

@pytest.mark.asyncio
async def test_extract_correct_sentences():    # モックで常に SUPPORTED
    sents = await extract_correct_sentences("猫。犬。", model="gpt-3.5-turbo")
    assert sents == ["猫。", "犬。"]
