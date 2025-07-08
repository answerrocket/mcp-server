#!/bin/bash

# Dependency installation functions for AnswerRocket MCP Server

# Source common utilities
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Install uv package manager
install_uv() {
    log_step "Installing uv package manager"
    
    if command_exists uv; then
        UV_VERSION=$(uv --version 2>/dev/null || echo "unknown")
        log_success "uv is already installed: $UV_VERSION"
        return
    fi
    
    local os_type=$(detect_os)
    case "$os_type" in
        macos|linux)
            log_info "Installing uv for $os_type..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            # Add uv to PATH for current session
            export PATH="$HOME/.cargo/bin:$PATH"
            source $HOME/.local/bin/env
            ;;
        windows)
            log_info "Installing uv for Windows..."
            powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
            ;;
        *)
            log_error "Unsupported operating system: $os_type"
            exit 1
            ;;
    esac
    
    # Verify installation
    if command_exists uv; then
        UV_VERSION=$(uv --version)
        log_success "uv installed successfully: $UV_VERSION"
    else
        log_error "Failed to install uv. Please install manually and try again."
        log_info "Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
}

# Setup Python with uv
setup_python() {
    local python_version="$1"
    log_step "Setting up Python $python_version with uv"
    
    # Install Python if not available
    log_info "Installing Python $python_version..."
    uv python install "$python_version"
    
    # Verify Python installation
    if uv python list | grep -q "$python_version"; then
        log_success "Python $python_version installed successfully"
    else
        log_error "Failed to install Python $python_version"
        exit 1
    fi
}

# Setup Python environment and install dependencies
setup_python_env() {
    local python_version="$1"
    log_step "Setting up Python virtual environment with uv"
    
    # Unset VIRTUAL_ENV to avoid path mismatch warnings
    unset VIRTUAL_ENV
    
    # Initialize uv project if pyproject.toml doesn't exist
    if [[ ! -f "pyproject.toml" ]]; then
        log_info "Initializing uv project..."
        uv init --python "$python_version"
    fi
    
    # Create virtual environment with uv in server/venv
    log_info "Creating virtual environment..."
    uv venv --python "$python_version"
    
    log_success "Virtual environment created with Python $python_version"
    
    # Install dependencies using uv
    log_info "Installing dependencies with uv..."
    
    # Install mcp[cli] using uv
    log_info "Installing MCP with CLI support..."
    uv add "mcp[cli]"
    log_success "Installed mcp[cli]"
    
    # Install answerrocket-client from git repository
    log_info "Installing answerrocket-client from git repository..."
    uv add "answerrocket-python-client"
    log_success "AnswerRocket client installed from git repository"
} 