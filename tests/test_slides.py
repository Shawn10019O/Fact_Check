from core.slides import sanitize

def test_sanitize():
    raw = "foo   bar \n\nbaz"
    assert sanitize(raw) == "foo bar。baz"
