"""Exercise the HTTP middleware too: AppTest alone doesn't run the web server."""
import asyncio
from copy import deepcopy

import pytest
from streamlit.web.server.starlette.starlette_gzip_middleware import SelectiveGZipMiddleware


@pytest.mark.parametrize("accept_encoding", [b"identity", b"gzip"])
@pytest.mark.parametrize("content_type,encoded", [
    (b"text/html", False),
    (b"image/png", False),
    (b"text/event-stream", False),
    (b"text/html", True),
])
def test_http_response_always_sends_headers_before_body(accept_encoding, content_type, encoded):
    messages = []

    async def app(scope, receive, send):
        headers = [(b"content-type", content_type)]
        if encoded:
            headers.append((b"content-encoding", b"gzip"))
        await send({"type": "http.response.start", "status": 200, "headers": headers})
        await send({"type": "http.response.body", "body": b"example", "more_body": False})

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        # Same protocol invariant enforced by Uvicorn in the production trace.
        if not messages:
            assert message["type"] == "http.response.start", "Body arrived before response headers"
        messages.append(deepcopy(message))

    asyncio.run(SelectiveGZipMiddleware(app)(
        {"type": "http", "path": "/component/example/index.html",
         "headers": [(b"accept-encoding", accept_encoding)]}, receive, send))
    assert [message["type"] for message in messages] == ["http.response.start", "http.response.body"]
