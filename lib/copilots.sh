#!/bin/bash

# Copilot management functions for AnswerRocket MCP Server

# Source common utilities
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Get copilot metadata
get_copilot_metadata() {
    local ar_url="$1"
    local ar_token="$2"
    
    log_step "Getting copilot metadata"
    
    # Ensure VIRTUAL_ENV is unset to avoid path mismatch warnings
    unset VIRTUAL_ENV
    
    # Use the existing get_copilots.py script
    local copilot_json=$(uv run python scripts/get_copilots.py "$ar_url" "$ar_token")
    
    if [[ $? -ne 0 ]]; then
        log_error "Failed to get copilot metadata"
        exit 1
    fi
    
    # Store the full JSON for later use
    local copilot_count=$(echo "$copilot_json" | uv run python -c "import sys, json; print(len(json.load(sys.stdin)))")
    log_success "Found $copilot_count copilots"
    
    echo "$copilot_json"
}

# Select copilots using TUI
select_copilots() {
    local copilot_json="$1"
    
    log_step "Select copilots to install"
    
    # Create temporary file for copilot data
    local temp_json=$(mktemp)
    echo "$copilot_json" > "$temp_json"
    
    # Try wrapper script approach first
    local selected_copilots=""
    local selection_status=1
    
    if [[ -f "scripts/copilot_selector_wrapper.sh" ]]; then
        chmod +x scripts/copilot_selector_wrapper.sh
        log_info "Launching interactive copilot selector..."
        
        selected_copilots=$(./scripts/copilot_selector_wrapper.sh "$temp_json" 2>/dev/null)
        selection_status=$?
        
        if [[ $selection_status -eq 0 ]] && [[ -n "$selected_copilots" ]]; then
            log_success "Interactive copilot selection completed successfully"
        fi
    fi
    
    # Clean up temp file
    rm -f "$temp_json"
    
    if [[ $selection_status -ne 0 ]] || [[ -z "$selected_copilots" ]]; then
        log_error "No copilots selected. Installation cancelled."
        exit 1
    fi
    
    # Parse the selected copilots to get IDs and names
    # Ensure VIRTUAL_ENV is unset to avoid path mismatch warnings
    unset VIRTUAL_ENV
    local copilot_data=$(echo "$selected_copilots" | uv run python -c "
import sys, json
data = json.load(sys.stdin)
for copilot in data:
    print(f\"{copilot['copilot_id']}|{copilot['name']}\")
")
    
    local selected_count=$(echo "$copilot_data" | wc -l)
    log_success "Selected $selected_count copilots for installation"
    
    echo "$copilot_data"
}

# Install MCP servers for selected copilots
install_mcp_servers() {
    local copilot_data="$1"
    local ar_url="$2"
    local ar_token="$3"
    
    log_step "Installing MCP servers for selected copilots"
    
    # Ensure VIRTUAL_ENV is unset to avoid path mismatch warnings
    unset VIRTUAL_ENV
    
    # Check if mcp command is available through uv
    if ! uv run mcp --help > /dev/null 2>&1; then
        log_error "mcp command not found in uv environment. Please ensure mcp[cli] is properly installed."
        exit 1
    fi
    
    # Install a server for each copilot
    local installed_servers=()
    while IFS='|' read -r copilot_id copilot_name; do
        if [[ -n "$copilot_id" ]]; then
            log_info "Installing MCP server for copilot: $copilot_name ($copilot_id)"
            
            # Create safe server name from copilot name
            # Remove special characters and spaces, convert to lowercase
            local safe_copilot_name=$(echo "$copilot_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
            local server_name="${safe_copilot_name}-Assistant"
            
            if uv run mcp install mcp_server/src/main.py -n "$server_name" -v "AR_URL=$ar_url" -v "AR_TOKEN=$ar_token" -v "COPILOT_ID=$copilot_id" --with "answerrocket-client" --with "fastmcp" ; then
                log_success "Installed MCP server: $server_name"
                installed_servers+=("$server_name ($copilot_name)")
            else
                log_warning "Failed to install MCP server for copilot: $copilot_name"
            fi
        fi
    done <<< "$copilot_data"
    
    if [[ ${#installed_servers[@]} -eq 0 ]]; then
        log_error "No MCP servers were successfully installed"
        exit 1
    fi
    
    log_success "Successfully installed ${#installed_servers[@]} MCP servers"
    
    # Return the installed servers list
    printf '%s\n' "${installed_servers[@]}"
} 