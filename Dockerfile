# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY mcp_server/ ./mcp_server/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Set environment variables for remote mode
ENV AR_URL=${AR_URL}
ENV MCP_MODE=remote
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9090
ENV MCP_TRANSPORT=streamable-http

# Expose the port
EXPOSE 9090

# Run the application
CMD ["maxai-mcp"] 