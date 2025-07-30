"""Remote mode handler for the MCP server."""

import logging
from pydantic import AnyHttpUrl
from mcp.server.auth.settings import AuthSettings

from mcp_server.auth.token_verifier import IntrospectionTokenVerifier
from mcp_server.modes.base import BaseMode
from mcp_server.utils import FastMCPExtended


class RemoteMode(BaseMode):
    """Handler for remote mode with OAuth authentication."""
    
    def create_mcp_server(self) -> FastMCPExtended:
        """Create MCP server for remote mode with OAuth."""
        token_verifier = IntrospectionTokenVerifier(
            validate_resource=True,
        )
        
        # Create MCP server with OAuth and support for our multi-tenant architecture
        # The MCP server will accept connections at /mcp/agent/{copilot_id}
        mcp_server = FastMCPExtended(
            "AnswerRocket MCP Server",
            token_verifier=token_verifier,
            auth=AuthSettings(
                issuer_url=AnyHttpUrl("http://localhost"), # Placeholder - real URLs come from request context
                # I have verified that removing the issuer_url doesn't have any security implications
                # It only is responsible for creating the /.well-known/oauth-protected-resource which we don't use
                required_scopes=['read:copilots', 'read:copilotSkills', 'execute:copilotSkills', 'ping'],
                resource_server_url=None
                # I have verified that the resource_server_url doesn't have any security implications
                # It only is responsible for creating the /.well-known/oauth-protected-resource which we don't use
            ),
            host=self.config.host,
            port=self.config.port,
        )
        
        mcp_server.settings.streamable_http_path = "/mcp/agent/{copilot_id:uuid}/"
        
        return mcp_server