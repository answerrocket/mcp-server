"""AnswerRocket client management utilities."""

import sys
import logging
from typing import Optional
from answer_rocket.client import AnswerRocketClient
from mcp.server.fastmcp.server import Context

from .context import RequestContextExtractor


class ClientManager:
    """Manages AnswerRocket client creation and validation."""
    
    @staticmethod
    def create_client(ar_url: str, ar_token: str) -> AnswerRocketClient:
        """Create and validate AnswerRocket client."""
        client = AnswerRocketClient(ar_url, ar_token)
        
        if not client.can_connect():
            logging.error(f"Error: Cannot connect to AnswerRocket at {ar_url}")
            logging.error("Please check your AR_URL and AR_TOKEN")
            sys.exit(1)
            
        return client

    @staticmethod
    def create_client_from_context(context: Context, ar_url: str, fallback_token: Optional[str] = None) -> Optional[AnswerRocketClient]:
        """Create AnswerRocket client from context (extracting bearer token) or fallback token."""
        # Try to extract bearer token from context first
        bearer_token = RequestContextExtractor.extract_bearer_token(context)
        
        # Use bearer token if available, otherwise fallback
        token_to_use = bearer_token or fallback_token
        
        if not token_to_use:
            return None
        
        try:
            client = AnswerRocketClient(ar_url, token_to_use)
            return client
        except Exception as e:
            logging.error(f"Error creating client: {e}")
            return None 