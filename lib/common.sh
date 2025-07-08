#!/bin/bash

# Common utilities and functions for AnswerRocket MCP Server installation

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

log_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}" >&2
}

log_info() {
    echo -e "${BLUE}INFO: $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" >&2
}

log_step() {
    echo -e "\n${BLUE}STEP: $1${NC}" >&2
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_step "Checking system requirements"
    
    if ! command_exists curl; then
        log_error "curl is required but not installed. Please install curl and try again."
        exit 1
    fi
    
    if ! command_exists git; then
        log_error "git is required but not installed. Please install git and try again."
        exit 1
    fi
    
    log_success "System requirements satisfied"
}

# Get user input for URL
get_ar_url() {
    local ar_url="$1"
    
    if [ -z "$ar_url" ]; then
        echo >&2
        while true; do
            read -p "Please enter your AnswerRocket URL (e.g., https://your-instance.answerrocket.com): " ar_url
            
            if [[ -z "$ar_url" ]]; then
                log_warning "URL cannot be empty. Please try again."
                continue
            fi
            
            # Remove trailing slash if present
            ar_url="${ar_url%/}"
            
            # Basic URL validation
            if [[ ! "$ar_url" =~ ^https?:// ]]; then
                log_warning "Please enter a valid URL starting with http:// or https://"
                continue
            fi
            
            break
        done
    else
        # Clean up the URL (remove trailing slash if present)
        ar_url="${ar_url%/}"
        log_info "Using provided AnswerRocket URL: $ar_url"
    fi
    
    echo "$ar_url"
}

# Get user input for token
get_ar_token() {
    local ar_token="$1"
    local ar_url="$2"
    
    if [ -z "$ar_token" ]; then
        echo >&2
        log_info "To get your API key:"
        echo "1. Open this URL in your browser: ${ar_url}/apps/chat/topics?panel=user-info" >&2
        echo "2. Click 'Generate' under 'Client API Key'" >&2
        echo "3. Copy the generated API key" >&2
        echo >&2
        
        while true; do
            echo -n "Please paste your AnswerRocket API Token: " >&2
            ar_token=""
            while IFS= read -r -s -n1 char; do
                if [[ -z "$char" ]]; then
                    # Enter pressed
                    break
                elif [[ "$char" == $'\177' ]] || [[ "$char" == $'\b' ]]; then
                    # Backspace
                    if [[ -n "$ar_token" ]]; then
                        ar_token="${ar_token%?}"
                        echo -ne "\b \b" >&2
                    fi
                else
                    # Regular character
                    ar_token="${ar_token}${char}"
                    echo -n "*" >&2
                fi
            done
            echo >&2  # New line after token entry
            
            if [[ -z "$ar_token" ]]; then
                log_warning "API token cannot be empty. Please try again."
                continue
            fi
            
            break
        done
    else
        log_info "Using provided API token"
    fi
    
    echo "$ar_token"
} 