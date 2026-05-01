from bin.browser import save_cookies, load_cookies


def test_save_and_load_cookies(tmp_path, monkeypatch):
    monkeypatch.setattr("bin.browser.COOKIES_DIR", tmp_path)
    sample = [
        {"name": "qrator_jsr", "value": "abc", "domain": ".ozon.ru"},
        {"name": "__Secure-ETC", "value": "def", "domain": ".ozon.ru"},
    ]
    save_cookies("ozon", sample)

    loaded = load_cookies("ozon")
    assert len(loaded) == 2
    assert loaded[0]["name"] == "qrator_jsr"


def test_load_cookies_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("bin.browser.COOKIES_DIR", tmp_path)
    assert load_cookies("nonexistent") == []
