"""Local mode handler for the MCP server."""

import logging
from answer_rocket.client import AnswerRocketClient

from mcp_server.config import ServerConfig
from mcp_server.modes.base import BaseMode
from mcp_server.tool_registry import ToolRegistry
from mcp_server.utils import SkillService, FastMCPExtended


class LocalMode(BaseMode):
    """Handler for local mode with direct token authentication."""
    
    def create_mcp_server(self) -> FastMCPExtended:
        """Create MCP server for local mode."""
        self.client = AnswerRocketClient(self.config.ar_url, self.config.ar_token)
        if not self.client.can_connect():
            raise ConnectionError(f"Cannot connect to AnswerRocket at {self.config.ar_url}")

        if not self.config.copilot_id:
            raise ValueError("Copilot ID is required for local mode")

        copilot_name = self.config.copilot_id

        return FastMCPExtended(
            copilot_name,
            host=self.config.host,
            port=self.config.port
        )
    
    def setup_tools(self):
        """Register copilot skills as MCP tools using hydrated reports."""
        if not self.mcp or not self.client:
            return

        skill_configs = SkillService.fetch_hydrated_reports(self.client, self.config.copilot_id, load_all_skills=False)
        
        if not skill_configs:
            logging.warning(f"No skills found for copilot {self.config.copilot_id}")
            return

        registry = ToolRegistry(
            mcp=self.mcp,
            ar_url=self.config.ar_url,
            ar_token=self.config.ar_token,
            copilot_id=self.config.copilot_id
        )
        
        registry.register_skills(skill_configs)
        logging.info(f"Registered {len(skill_configs)} skills for copilot {self.config.copilot_id}")