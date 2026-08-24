from starlette.requests import Request

from app.core.security import ClientIPResolver


def make_request(peer: str, forwarded: str | None = None) -> Request:
    headers = []
    if forwarded:
        headers.append((b"x-forwarded-for", forwarded.encode("ascii")))
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/chat/stream",
            "headers": headers,
            "client": (peer, 12345),
            "server": ("test", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def test_untrusted_peer_cannot_spoof_forwarded_for():
    resolver = ClientIPResolver(("10.0.0.0/8",))
    assert resolver.resolve(make_request("198.51.100.5", "1.1.1.1")) == "198.51.100.5"


def test_trusted_proxy_uses_first_untrusted_address_from_right():
    resolver = ClientIPResolver(("10.0.0.0/8",))
    request = make_request("10.0.0.2", "203.0.113.8, 10.0.0.3")
    assert resolver.resolve(request) == "203.0.113.8"

