from bin.http_client import make_session, DEFAULT_HEADERS


def test_make_session_returns_session_with_impersonation():
    s = make_session()
    assert s is not None
    assert "ru" in DEFAULT_HEADERS["Accept-Language"]


def test_make_session_accepts_extra_cookies():
    cookies = {"qrator_jsr": "abc", "__Secure-ETC": "def"}
    s = make_session(cookies=cookies)
    jar_names = [c.name for c in s.cookies.jar]
    assert "qrator_jsr" in jar_names
    assert "__Secure-ETC" in jar_names
