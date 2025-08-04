"""Lifted from https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/servers/simple-auth/mcp_simple_auth/token_verifier.py"""

import logging

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.shared.auth_utils import check_resource_allowed
from starlette_context import context

logger = logging.getLogger(__name__)


class IntrospectionTokenVerifier(TokenVerifier):
    """Token verifier that uses OAuth 2.0 Token Introspection (RFC 7662).

    TODO: Implement the following best production practices:
    - Connection pooling and reuse
    - More sophisticated error handling
    - Rate limiting and retry logic
    - Comprehensive configuration options
    """

    def __init__(
        self,
        validate_resource: bool = False,
    ):
        self.validate_resource = validate_resource

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify token via introspection endpoint."""
        import httpx
        from mcp_server.config import ServerConfig
        
        # Use hardcoded auth server URL instead of dynamic base_url
        auth_server_url = ServerConfig.HARDCODED_AUTH_SERVER_URL.rstrip("/")
        introspection_endpoint = auth_server_url + "/api/oauth2/introspect"
        
        # For resource validation, still use the original base_url context
        base_url = context.get("base_url", "").rstrip("/")
        server_url = base_url
        resource_url = base_url
        
        # Validate URL to prevent SSRF attacks
        if not introspection_endpoint.startswith(("https://", "http://localhost", "http://127.0.0.1")) and not "local.answerrocket.com" in introspection_endpoint:
            logger.warning(f"Rejecting introspection endpoint with unsafe scheme: {introspection_endpoint}")
            return None

        timeout = httpx.Timeout(
            connect=10,    # Connection timeout
            read=10.0,      # Read timeout
            write=5.0,      # Write timeout
            pool=2.0        # Pool connection timeout
        )

        limits = httpx.Limits(
            max_connections=20,           # Increased from 10
            max_keepalive_connections=10, # Increased from 5
            keepalive_expiry=30.0,       # Keep connections alive for 30s
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            verify=True,  # Enforce SSL verification
            headers={
                "User-Agent": "MCP-Server/1.0",
                "Accept": "application/json"
            }
        ) as client:
            try:
                response = await client.post(
                    introspection_endpoint,
                    data={"token": token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    logger.debug(f"Token introspection returned status {response.status_code}")
                    return None

                data = response.json()
                if not data.get("active", False):
                    return None

                # RFC 8707 resource validation (only when --oauth-strict is set)
                if self.validate_resource and not self._validate_resource(data, resource_url, server_url):
                    logger.warning(f"Token resource validation failed. Expected: {resource_url}")
                    return None

                return AccessToken(
                    token=token,
                    client_id=data.get("client_id", "unknown"),
                    scopes=data.get("scope", "").split() if data.get("scope") else [],
                    expires_at=data.get("exp"),
                    resource=data.get("aud"),  # Include resource in token
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.warning(f"Token introspection failed: {e}")
                return None

    def _validate_resource(self, token_data: dict, resource_url: str, server_url: str) -> bool:
        """Validate token was issued for this resource server."""
        if not server_url or not resource_url:
            return False  # Fail if strict validation requested but URLs missing

        # Check 'aud' claim first (standard JWT audience)
        aud = token_data.get("aud")
        if isinstance(aud, list):
            for audience in aud:
                if self._is_valid_resource(audience.rstrip("/"), resource_url, server_url):
                    return True
            return False
        elif aud:
            return self._is_valid_resource(aud.rstrip("/"), resource_url, server_url)

        # No resource binding - invalid per RFC 8707
        return False

    def _is_valid_resource(self, resource: str, resource_url: str, server_url: str) -> bool:
        """Check if resource matches this server using hierarchical matching."""
        if not resource_url:
            return False

        return check_resource_allowed(requested_resource=resource_url, configured_resource=resource)