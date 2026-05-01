from curl_cffi import requests as cr


DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.5",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

DEFAULT_IMPERSONATE = "chrome124"
DEFAULT_TIMEOUT = 30


def make_session(
    cookies: dict[str, str] | None = None,
    impersonate: str = DEFAULT_IMPERSONATE,
    extra_headers: dict[str, str] | None = None,
) -> cr.Session:
    """Create curl_cffi Session with TLS-fingerprint impersonation, sane defaults."""
    s = cr.Session(impersonate=impersonate)
    headers = {**DEFAULT_HEADERS, **(extra_headers or {})}
    s.headers.update(headers)
    if cookies:
        for name, value in cookies.items():
            s.cookies.set(name, value)
    return s
