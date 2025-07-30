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
            if not request or not hasattr(request, 'headers'):
                return None
            
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                return auth_header[7:]
            
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
        """Extract copilot ID from request path parameters for remote mode."""
        return str(context.request_context.request.path_params["copilot_id"])