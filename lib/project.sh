#!/bin/bash

# Project setup functions for AnswerRocket MCP Server

# Source common utilities
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Setup project directory (local mode only)
setup_project_local() {
    local project_dir="$1"
    local script_dir="$2"
    
    log_step "Setting up project directory"
    
    # Get the repository root
    local repo_root="$script_dir"
    # If we're in a subdirectory (like scripts/), go to parent
    while [ ! -f "$repo_root/pyproject.toml" ] && [ "$repo_root" != "/" ]; do
        repo_root="$(dirname "$repo_root")"
    done
    
    if [ ! -f "$repo_root/pyproject.toml" ]; then
        log_error "Could not find pyproject.toml. Please run from the repository root."
        exit 1
    fi
    
    project_dir="$repo_root"
    log_info "Using local repository at: $project_dir"
    cd "$project_dir"
    log_success "Using local repository"
    echo "$project_dir"
}

# Setup project directory (original function for backward compatibility)
setup_project() {
    local local_mode="$1"
    local project_dir="$2"
    local github_repo="$3"
    local github_branch="$4"
    local script_dir="$5"
    
    log_step "Setting up project directory"
    
    if [ "$local_mode" = true ]; then
        # Get the repository root
        local repo_root="$script_dir"
        # If we're in a subdirectory (like scripts/), go to parent
        while [ ! -f "$repo_root/pyproject.toml" ] && [ "$repo_root" != "/" ]; do
            repo_root="$(dirname "$repo_root")"
        done
        
        if [ ! -f "$repo_root/pyproject.toml" ]; then
            log_error "Could not find pyproject.toml. Please run from the repository root."
            exit 1
        fi
        
        project_dir="$repo_root"
        log_info "Using local repository at: $project_dir"
        cd "$project_dir"
        log_success "Using local repository"
        echo "$project_dir"
        return
    fi
    
    # Create project directory
    if [[ -d "$project_dir" ]]; then
        log_warning "Directory $project_dir already exists."
        read -p "Do you want to remove it and reinstall? (y/N): " CONFIRM
        if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
            rm -rf "$project_dir"
            log_info "Removed existing directory"
        else
            log_error "Installation cancelled"
            exit 1
        fi
    fi
    
    # Clone the repository
    log_info "Cloning repository from GitHub..."
    git clone -b "$github_branch" "https://github.com/$github_repo.git" "$project_dir"
    
    # Copy selector scripts if they exist in the current directory
    copy_selector_scripts "$script_dir" "$project_dir"
    
    cd "$project_dir"
    log_success "Repository cloned to $project_dir"
    echo "$project_dir"
}

# Copy selector scripts to project directory
copy_selector_scripts() {
    local script_dir="$1"
    local project_dir="$2"
    
    local scripts_copied=0
    for script in copilot_selector_wrapper.sh select_copilots_interactive.py select_copilots_simple.py; do
        if [[ -f "$script_dir/$script" ]]; then
            cp "$script_dir/$script" "$project_dir/"
            chmod +x "$project_dir/$script"
            scripts_copied=1
        fi
    done
    
    if [[ $scripts_copied -eq 1 ]]; then
        log_info "Copied copilot selector scripts"
    fi
}

# Validate AnswerRocket connection
validate_connection() {
    local ar_url="$1"
    local ar_token="$2"
    
    log_info "Validating connection to AnswerRocket..."
    
    # Unset VIRTUAL_ENV to avoid path mismatch warnings
    unset VIRTUAL_ENV
    
    if AR_URL="$ar_url" AR_TOKEN="$ar_token" uv run python scripts/validate_connection.py 2>/dev/null; then
        log_success "Connected to AnswerRocket successfully"
        return 0
    else
        log_error "Failed to connect to AnswerRocket. Please check your URL and token."
        return 1
    fi
} 