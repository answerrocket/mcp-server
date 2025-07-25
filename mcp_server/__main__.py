"""MCP Server entry point for the AnswerRocket MCP server."""

import sys
import logging
from typing import cast, Literal
from mcp_server.modes import LocalMode, RemoteMode
from mcp_server.config import ServerConfig
from mcp.server import FastMCP

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s'
    )


def main():
    """Main entry point"""
    setup_logging()

    config = ServerConfig.from_environment()

    mode_handler = LocalMode(config) if config.is_local else RemoteMode(config)

    logging.info(f"Creating MCP server in {config.mode} mode...")
    server = mode_handler.initialize()

    transport = cast(Literal["stdio", "streamable-http"], config.transport)

    logging.info(f"Running MCP server in {transport} mode...")
    server.run(transport=transport)



if __name__ == "__main__":
    main()