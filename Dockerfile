FROM python:3.10-slim

WORKDIR /app

#  Defense-in-depth for glibc CVE-2025-4802:
#    - Ensure no static setuid binaries exist; containers generally don't need setuid.
#      (Safe for most app images; omit if you truly need setuid.)
RUN set -eux; \
find / -xdev -type f -perm -4000 -print -exec chmod a-s {} + || true

# Fix CVE-2025-58050: Upgrade pcre2 to version 10.46+
RUN apt-get update && \
    apt-get upgrade -y libpcre2-8-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools to latest secure versions
RUN python -m pip install --upgrade 'pip>=24.2' 'setuptools>=78.1.1' wheel

COPY pyproject.toml ./
COPY mcp_server/ ./mcp_server/

RUN pip install --no-cache-dir -e .

ENV MCP_MODE=remote
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9090
ENV MCP_TRANSPORT=streamable-http

EXPOSE 9090

CMD ["maxai-mcp"] 