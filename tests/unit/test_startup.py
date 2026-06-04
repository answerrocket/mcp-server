"""FastMCP construction must work on the installed mcp SDK."""
from mcp_server.auth.fastmcp_extended import FastMCPExtended


def test_fastmcp_extended_constructs():
    server = FastMCPExtended("test-startup", host="127.0.0.1", port=9099)
    assert server._mcp_server is not None


def test_initialization_options_build():
    server = FastMCPExtended("test-startup", host="127.0.0.1", port=9099)
    opts = server._mcp_server.create_initialization_options()
    assert opts is not None


def test_remote_streamable_http_app_builds():
    """Guards the remote-mode starlette / starlette-context middleware + route surgery."""
    from mcp_server.config import ServerConfig
    from mcp_server.modes.remote import RemoteMode

    cfg = ServerConfig(mode="remote", ar_url=None, host="127.0.0.1", port=9098,
                       transport="streamable-http")
    server = RemoteMode(cfg).initialize()
    app = server.streamable_http_app()
    paths = [getattr(r, "path", None) for r in app.routes]
    assert any("/mcp/agent/" in (p or "") for p in paths)
