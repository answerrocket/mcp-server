"""Copilot-related operations."""

import logging
from typing import Optional
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from starlette.requests import Request

from .context import RequestContextExtractor
from .client import ClientManager


class CopilotService:
    """Handles copilot-related operations."""
    
    @staticmethod
    def get_copilot_info(client: AnswerRocketClient, copilot_id: str) -> Optional[MaxCopilot]:
        """Get copilot information including name and skills."""
        try:
            if not client.can_connect():
                raise ValueError("Cannot connect to AnswerRocket")
            
            copilot_info = client.config.get_copilot(True, copilot_id)
            if not copilot_info:
                raise ValueError(f"Copilot with ID '{copilot_id}' not found")
            
            return copilot_info
        except Exception as e:
            logging.error(f"Error getting copilot info: {e}")
            return None

    @staticmethod
    def get_copilot_info_from_context(context: Context[ServerSession, object, Request], ar_url: str, copilot_id: Optional[str] = None, fallback_token: Optional[str] = None) -> Optional[MaxCopilot]:
        """Get copilot information from context-based client."""
        # Extract copilot ID from context if not provided
        if not copilot_id:
            copilot_id = RequestContextExtractor.extract_copilot_id(context)
        
        if not copilot_id:
            return None

        client = ClientManager.create_client_from_context(context, ar_url, fallback_token)
        if not client:
            return None
        
        return CopilotService.get_copilot_info(client, copilot_id) 