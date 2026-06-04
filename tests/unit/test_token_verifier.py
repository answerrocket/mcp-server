"""Introspection host allowlist + token validation."""
import httpx
import pytest
from starlette_context import request_cycle_context

from mcp_server.auth.token_verifier import IntrospectionTokenVerifier

ACTIVE = {"active": True, "client_id": "c1", "scope": "read:copilots ping",
          "exp": 9999999999, "aud": "http://localhost:1234"}


class _FakeResp:
    def __init__(self, data, status=200):
        self.status_code = status
        self._data = data

    def json(self):
        return self._data


def _fake_client_factory(data, status=200, on_post=None):
    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kw):
            if on_post:
                on_post(url, kw)
            return _FakeResp(data, status)
    return lambda *a, **k: _FakeClient()


@pytest.mark.asyncio
async def test_rejects_host_not_in_allowlist(monkeypatch):
    # If the allowlist check fails we must NOT make any HTTP call (no token leakage).
    def _boom(*a, **k):
        raise AssertionError("httpx must not be called for a disallowed host")
    monkeypatch.setattr(httpx, "AsyncClient", _boom)

    verifier = IntrospectionTokenVerifier(allowed_hosts=("good.host:1234",))
    with request_cycle_context({"base_url": "http://evil.attacker.com/"}):
        result = await verifier.verify_token("some-token")
    assert result is None


@pytest.mark.asyncio
async def test_allowlisted_host_active_token_passes(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(ACTIVE))
    verifier = IntrospectionTokenVerifier(allowed_hosts=("localhost:1234",))
    with request_cycle_context({"base_url": "http://localhost:1234/"}):
        result = await verifier.verify_token("good-token")
    assert result is not None
    assert "ping" in result.scopes


@pytest.mark.asyncio
async def test_inactive_token_rejected(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory({"active": False}))
    verifier = IntrospectionTokenVerifier(allowed_hosts=("localhost:1234",))
    with request_cycle_context({"base_url": "http://localhost:1234/"}):
        result = await verifier.verify_token("bad-token")
    assert result is None


@pytest.mark.asyncio
async def test_empty_allowlist_still_works_with_warning(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(ACTIVE))
    verifier = IntrospectionTokenVerifier(allowed_hosts=())
    with request_cycle_context({"base_url": "http://localhost:1234/"}):
        result = await verifier.verify_token("good-token")
    assert result is not None
