#!/bin/bash
set -euo pipefail

# Design Team Pod Deployment Script
# Secure production deployment with Podman and Quadlet

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POD_NAME="design-team-pod"
IMAGE_NAME="localhost/design-team-pod"
VERSION="2.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running as non-root
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
    
    # Check Podman version
    if ! command -v podman &> /dev/null; then
        error "Podman is not installed"
    fi
    
    local podman_version=$(podman --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    info "Podman version: $podman_version"
    
    # Check if systemd user services are enabled
    if ! systemctl --user status &> /dev/null; then
        warn "User systemd services may not be available"
    fi
    
    # Check available disk space
    local available_space=$(df "$HOME" | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        warn "Less than 5GB disk space available"
    fi
    
    log "Prerequisites check completed"
}

create_directories() {
    log "Creating required directories..."
    
    # Create data directories
    mkdir -p /data/design-team/{workspace,knowledge,config}
    mkdir -p /data/design-team/workspace/{projects,output,temp,cache}
    
    # Set proper ownership and permissions
    sudo chown -R $(id -u):$(id -g) /data/design-team
    chmod -R 755 /data/design-team
    
    # Create systemd user directory
    mkdir -p ~/.config/containers/systemd
    
    log "Directories created successfully"
}

copy_knowledge_base() {
    log "Copying knowledge base..."
    
    if [[ -d "$SCRIPT_DIR/knowledge" ]]; then
        cp -r "$SCRIPT_DIR/knowledge/"* /data/design-team/knowledge/
        log "Knowledge base copied"
    else
        warn "Knowledge directory not found, creating minimal knowledge base"
        echo "# Design Team Pod Knowledge Base" > /data/design-team/knowledge/README.md
    fi
    
    # Copy configuration
    if [[ -d "$SCRIPT_DIR/config" ]]; then
        cp -r "$SCRIPT_DIR/config/"* /data/design-team/config/
        log "Configuration copied"
    fi
}

copy_tools() {
    log "Copying design tools..."
    
    # Create temporary build context
    local build_dir=$(mktemp -d)
    
    # Copy all necessary files
    cp -r "$SCRIPT_DIR/tools" "$build_dir/"
    cp -r "$SCRIPT_DIR/knowledge" "$build_dir/"
    cp -r "$SCRIPT_DIR/api" "$build_dir/"
    cp -r "$SCRIPT_DIR/config" "$build_dir/"
    cp "$SCRIPT_DIR/requirements.txt" "$build_dir/"
    cp "$SCRIPT_DIR/Containerfile" "$build_dir/"
    
    echo "$build_dir"
}

build_image() {
    log "Building Design Team Pod image..."
    
    local build_dir=$(copy_tools)
    
    # Build with security-focused options
    podman build \
        --tag "$IMAGE_NAME:$VERSION" \
        --tag "$IMAGE_NAME:latest" \
        --security-opt label=disable \
        --cap-drop=ALL \
        --no-cache \
        --squash \
        --format docker \
        "$build_dir"
    
    # Clean up build directory
    rm -rf "$build_dir"
    
    log "Image built successfully: $IMAGE_NAME:$VERSION"
}

create_secrets() {
    log "Creating container secrets..."
    
    # Check for API keys in environment
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
        echo -n "$ANTHROPIC_API_KEY" | podman secret create anthropic-key -
        log "Anthropic API key secret created"
    else
        warn "ANTHROPIC_API_KEY not set - AI analysis may not work"
    fi
    
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        echo -n "$OPENAI_API_KEY" | podman secret create openai-key -
        log "OpenAI API key secret created"
    else
        warn "OPENAI_API_KEY not set - GPT analysis may not work"
    fi
    
    if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
        echo -n "$GOOGLE_API_KEY" | podman secret create google-key -
        log "Google API key secret created"
    else
        info "GOOGLE_API_KEY not set - Gemini analysis not available"
    fi
}

deploy_quadlet_configs() {
    log "Deploying Quadlet configurations..."
    
    # Copy Quadlet files to systemd user directory
    cp "$SCRIPT_DIR/design-team.container" ~/.config/containers/systemd/
    cp "$SCRIPT_DIR/design-team.network" ~/.config/containers/systemd/
    cp "$SCRIPT_DIR/design-team.volume" ~/.config/containers/systemd/
    
    # Reload systemd to pick up new configurations
    systemctl --user daemon-reload
    
    log "Quadlet configurations deployed"
}

start_services() {
    log "Starting Design Team Pod services..."
    
    # Start network first
    systemctl --user start design-team-net.service
    
    # Start volumes
    systemctl --user start design-team-workspace.service
    systemctl --user start design-team-knowledge.service
    systemctl --user start design-team-config.service
    
    # Start main container
    systemctl --user start design-team-pod.service
    
    # Enable for auto-start
    systemctl --user enable design-team-pod.service
    
    log "Services started and enabled"
}

verify_deployment() {
    log "Verifying deployment..."
    
    # Wait for container to be ready
    local retries=30
    local count=0
    
    while [[ $count -lt $retries ]]; do
        if curl -f http://127.0.0.1:8081/health &> /dev/null; then
            log "Design Team Pod is healthy and responding"
            break
        fi
        
        ((count++))
        if [[ $count -eq $retries ]]; then
            error "Design Team Pod failed to start within timeout"
        fi
        
        info "Waiting for service to be ready... ($count/$retries)"
        sleep 5
    done
    
    # Show service status
    systemctl --user status design-team-pod.service --no-pager
    
    # Show API endpoints
    info "Design Team Pod deployed successfully!"
    info "API available at: http://127.0.0.1:8081"
    info "Documentation: http://127.0.0.1:8081/docs"
    info "Health check: http://127.0.0.1:8081/health"
}

show_usage() {
    log "Design Team Pod Management Commands:"
    echo ""
    echo "  Status:   systemctl --user status design-team-pod.service"
    echo "  Logs:     journalctl --user -u design-team-pod.service -f"
    echo "  Stop:     systemctl --user stop design-team-pod.service"
    echo "  Restart:  systemctl --user restart design-team-pod.service"
    echo ""
    echo "  Shell:    podman exec -it design-team-pod /bin/bash"
    echo "  API:      curl http://127.0.0.1:8081/health"
    echo ""
    echo "  Workspace: /data/design-team/workspace"
    echo "  Knowledge: /data/design-team/knowledge"
    echo "  Config:    /data/design-team/config"
}

cleanup_failed_deployment() {
    warn "Cleaning up failed deployment..."
    
    systemctl --user stop design-team-pod.service 2>/dev/null || true
    systemctl --user disable design-team-pod.service 2>/dev/null || true
    
    podman rm -f design-team-pod 2>/dev/null || true
    
    # Remove secrets (they can be recreated)
    podman secret rm anthropic-key 2>/dev/null || true
    podman secret rm openai-key 2>/dev/null || true
    podman secret rm google-key 2>/dev/null || true
    
    error "Deployment failed and cleaned up"
}

main() {
    log "Starting Design Team Pod deployment..."
    
    # Set trap for cleanup on failure
    trap cleanup_failed_deployment ERR
    
    check_prerequisites
    create_directories
    copy_knowledge_base
    build_image
    create_secrets
    deploy_quadlet_configs
    start_services
    verify_deployment
    show_usage
    
    log "Design Team Pod deployment completed successfully!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "build")
        build_image
        ;;
    "start")
        systemctl --user start design-team-pod.service
        ;;
    "stop")
        systemctl --user stop design-team-pod.service
        ;;
    "restart")
        systemctl --user restart design-team-pod.service
        ;;
    "status")
        systemctl --user status design-team-pod.service --no-pager
        ;;
    "logs")
        journalctl --user -u design-team-pod.service -f
        ;;
    "clean")
        cleanup_failed_deployment
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [deploy|build|start|stop|restart|status|logs|clean|help]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  build    - Build image only"
        echo "  start    - Start services"
        echo "  stop     - Stop services"
        echo "  restart  - Restart services"
        echo "  status   - Show service status"
        echo "  logs     - Follow service logs"
        echo "  clean    - Clean up failed deployment"
        echo "  help     - Show this help"
        ;;
    *)
        error "Unknown command: $1. Use 'help' for usage information."
        ;;
esac