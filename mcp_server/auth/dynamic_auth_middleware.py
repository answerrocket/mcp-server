"""Dynamic authentication middleware that uses starlette-context for resource metadata URL."""

from typing import Any
from starlette_context import context
from mcp.server.auth.middleware.bearer_auth import RequireAuthMiddleware
from starlette.types import Send
import json

class DynamicRequireAuthMiddleware(RequireAuthMiddleware):
    """
    Subclass of RequireAuthMiddleware that uses dynamic resource metadata URL.
    
    This uses starlette-context to dynamically determine the resource_metadata_url 
    from the request's base URL instead of using a static URL.
    """

    def __init__(self, app: Any, required_scopes: list[str]):
        """
        Initialize the middleware.

        Args:
            app: ASGI application
            required_scopes: List of scopes that the token must have
        """
        # Initialize parent with None for resource_metadata_url since we'll determine it dynamically
        super().__init__(app, required_scopes, resource_metadata_url=None)

    def _get_dynamic_resource_metadata_url(self) -> str | None:
        """Get the resource metadata URL dynamically from starlette-context."""
        try:
            base_url = context.get("base_url")
            if base_url:
                return f"{base_url.rstrip('/')}/.well-known/oauth-protected-resource"
        except (LookupError, RuntimeError):
            pass
        return None

    async def _send_auth_error(self, send: Send, status_code: int, error: str, description: str) -> None:
        """Send an authentication error response with dynamic WWW-Authenticate header."""
        
        # Build WWW-Authenticate header value
        www_auth_parts = [f'error="{error}"', f'error_description="{description}"']
        
        # Get dynamic resource metadata URL instead of using self.resource_metadata_url
        resource_metadata_url = self._get_dynamic_resource_metadata_url()
        if resource_metadata_url:
            www_auth_parts.append(f'resource_metadata="{resource_metadata_url}"')

        www_authenticate = f"Bearer {', '.join(www_auth_parts)}"

        # Send response
        body = {"error": error, "error_description": description}
        body_bytes = json.dumps(body).encode()

        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body_bytes)).encode()),
                    (b"www-authenticate", www_authenticate.encode()),
                ],
            }
        )

        await send(
            {
                "type": "http.response.body",
                "body": body_bytes,
            }
        ) 