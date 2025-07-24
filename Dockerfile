FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY mcp_server/ ./mcp_server/

RUN pip install --no-cache-dir -e .

ENV MCP_MODE=remote
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9090
ENV MCP_TRANSPORT=streamable-http

EXPOSE 9090

CMD ["maxai-mcp"] 