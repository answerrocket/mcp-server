#!/bin/bash

set -e

# Configuration
PYTHON_VERSION="3.10.7"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AR_URL=""
AR_TOKEN=""
PROJECT_DIR="$HOME/answerrocket-mcp-server"

# Import library functions
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/deps.sh"
source "$SCRIPT_DIR/lib/project.sh"
source "$SCRIPT_DIR/lib/copilots.sh"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            AR_URL="$2"
            shift 2
            ;;
        --token)
            AR_TOKEN="$2"
            shift 2
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --url URL        AnswerRocket URL (e.g., https://your-instance.answerrocket.com)"
            echo "  --token TOKEN    AnswerRocket API token"
            echo "  --project-dir DIR Project directory (default: $HOME/answerrocket-mcp-server)"
            echo "  -h, --help       Show this help message"
            echo
            echo "If --url and --token are not provided, you will be prompted for them interactively."
            echo
            echo "Note: This installer uses the local repository. For remote installation, use bootstrap.sh"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Error handling
trap 'log_error "Installation failed. Please check the error messages above."; exit 1' ERR

# Get user credentials
get_user_credentials() {
    log_step "Setting up AnswerRocket MCP Server"
    
    AR_URL=$(get_ar_url "$AR_URL")
    AR_TOKEN=$(get_ar_token "$AR_TOKEN" "$AR_URL")
    
    log_success "AnswerRocket URL: $AR_URL"
    log_success "API token configured"
}

# Main installation function
main() {
    echo "AnswerRocket Multi-Copilot MCP Server Installer"
    echo "================================================"
    log_info "Using local repository"
    
    # Check system requirements
    check_requirements
    
    # Install dependencies
    install_uv
    setup_python "$PYTHON_VERSION"
    
    # Get user credentials
    get_user_credentials
    
    # Setup project
    PROJECT_DIR=$(setup_project_local "$PROJECT_DIR" "$SCRIPT_DIR")
    setup_python_env "$PYTHON_VERSION"
    
    # Validate connection
    if ! validate_connection "$AR_URL" "$AR_TOKEN"; then
        exit 1
    fi
    
    # Get and select copilots
    COPILOT_JSON=$(get_copilot_metadata "$AR_URL" "$AR_TOKEN")
    COPILOT_DATA=$(select_copilots "$COPILOT_JSON")
    
    # Install MCP servers
    INSTALLED_SERVERS_OUTPUT=$(install_mcp_servers "$COPILOT_DATA" "$AR_URL" "$AR_TOKEN")
    # Convert output to array using a more portable approach
    INSTALLED_SERVERS=()
    while IFS= read -r line; do
        [[ -n "$line" ]] && INSTALLED_SERVERS+=("$line")
    done <<< "$INSTALLED_SERVERS_OUTPUT"
    
    # Success message
    echo
    log_success "Installation completed successfully!"
    echo
    log_info "Your MCP servers are now installed and ready to use."
    log_info "Each copilot has its own dedicated MCP server:"
    echo
    for server in "${INSTALLED_SERVERS[@]}"; do
        echo "  - $server"
    done
    echo
    log_info "You can use these servers with MCP-compatible clients like Claude Desktop."
    echo
    log_info "Project location: $PROJECT_DIR"
    log_info "Configuration: AR_URL=$AR_URL"
    echo
    log_info "Next steps:"
    echo "1. Restart your MCP client (e.g., Claude desktop app)"
    echo "2. Your AnswerRocket copilots will appear as available tools"
    echo "3. Start using your copilots through the MCP interface"
    echo
    log_warning "Keep your API token secure and never share it publicly!"
}

# Run main function
main "$@"