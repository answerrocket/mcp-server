"""Request context extraction utilities."""

import logging
from typing import Optional
from mcp.server.fastmcp.server import Context


class RequestContextExtractor:
    """Extracts information from HTTP request contexts."""
    
    @staticmethod
    def extract_bearer_token(context: Context) -> Optional[str]:
        """Extract bearer token from request headers."""
        try:
            request = context.request_context.request
            if request and hasattr(request, 'headers'):

                auth_header = request.headers.get('authorization', '')
                if auth_header.startswith('Bearer '):
                    return auth_header[7:]  # Remove 'Bearer ' prefix
                

                if hasattr(request.headers, 'raw'):
                    for header_name, header_value in request.headers.raw:
                        if header_name.lower() == b'authorization':
                            auth_value = header_value.decode('utf-8')
                            if auth_value.startswith('Bearer '):
                                return auth_value[7:]
        except Exception as e:
            logging.error(f"Error extracting bearer token: {e}")
        return None

    @staticmethod
    def extract_copilot_id(context: Context) -> Optional[str]:
        """Extract copilot ID from request path for remote mode."""
        try:
            request = context.request_context.request
            if request and hasattr(request, 'scope'):
                path = request.scope.get("path", "")
                # Look for patterns like /mcp/copilot/{copilot_id}
                if "/agent/" in path:
                    parts = path.split("/agent/")
                    if len(parts) > 1:
                        copilot_id = parts[1].split("/")[0]  # Get first part after /copilot/
                        return copilot_id
        except Exception as e:
            logging.error(f"Error extracting copilot ID from context: {e}")
        return None 