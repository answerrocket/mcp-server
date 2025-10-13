"""MCP Server entry point for the AnswerRocket MCP server."""

import sys
import logging
from typing import cast, Literal
from mcp_server.modes import LocalMode, RemoteMode
from mcp_server.config import ServerConfig
from mcp.server import FastMCP
import yaml

DEFAULT_LOGGING_CONFIG_PATH = "./logging.yaml"

def setup_logging():
    
    import os.path

    if not os.path.exists(DEFAULT_LOGGING_CONFIG_PATH):
        logging.getLogger().debug("Unable to configure AR logging: config file not found (%s)", DEFAULT_LOGGING_CONFIG_PATH)
        return
        
    try:
        with open(DEFAULT_LOGGING_CONFIG_PATH, "r") as loggingConfigYaml:
            logging.config.dictConfig(yaml.safe_load(loggingConfigYaml))
    except Exception as e:
        logging.getLogger().error("Unable to configure AR logging: %s", e)


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