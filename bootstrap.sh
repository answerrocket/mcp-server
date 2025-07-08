#!/bin/bash

set -e

# Configuration
GITHUB_REPO="AnswerrocketKW/mcp-test"
GITHUB_BRANCH="main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cross-platform application directory
get_app_dir() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        echo "$APPDATA/AnswerRocket/mcp-server"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "$HOME/Library/Application Support/AnswerRocket/mcp-server"
    else
        # Linux and other Unix-like systems
        echo "$HOME/.local/share/answerrocket/mcp-server"
    fi
}

# Main bootstrap function
main() {
    echo "AnswerRocket MCP Server Bootstrap Installer"
    echo "==========================================="
    echo
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not installed. Please install git first."
        exit 1
    fi
    
    # Get application directory
    APP_DIR=$(get_app_dir)
    
    # Check if directory already exists
    if [[ -d "$APP_DIR" ]]; then
        log_warning "Directory $APP_DIR already exists."
        read -p "Do you want to update it? (y/N): " CONFIRM
        if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
            log_info "Updating existing installation..."
            cd "$APP_DIR"
            git fetch origin
            git reset --hard "origin/$GITHUB_BRANCH"
            log_success "Repository updated"
        else
            log_info "Using existing installation"
            cd "$APP_DIR"
        fi
    else
        # Create parent directory if it doesn't exist
        log_info "Creating application directory: $APP_DIR"
        mkdir -p "$(dirname "$APP_DIR")"
        
        # Clone the repository
        log_info "Cloning repository from GitHub..."
        git clone -b "$GITHUB_BRANCH" "https://github.com/$GITHUB_REPO.git" "$APP_DIR"
        cd "$APP_DIR"
        log_success "Repository cloned to $APP_DIR"
    fi
    
    # Make install script executable
    chmod +x install.sh
    
    # Run the installer with all passed arguments
    log_info "Running installer..."
    ./install.sh "$@"
    
    log_success "Bootstrap installation completed!"
    echo
    log_info "The AnswerRocket MCP Server has been installed to: $APP_DIR"
    log_info "You can run the installer directly from this location in the future."
}

# Run main function with all arguments (Homebrew-style execution)
main "$@" 