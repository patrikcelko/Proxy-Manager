#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/helpers.sh"
source "${SCRIPT_DIR}/build.sh"

function deploy_proxy_manager() {
    local SERVICE_HOST="root@x.x.x.x"  # Remote server SSH address
    local ENV_NAME="${1:-prod}"
    local SERVER_WORK_DIR="/root/docker/proxy_manager"
    local DOCKER_DIR="${PROJECT_ROOT}/docker"

    resolve_env_file "$ENV_NAME"

    info "Starting deployment to remote server..."

    if ! ssh -o ConnectTimeout=3 "$SERVICE_HOST" "hostname" 1>/dev/null; then
        error "Cannot connect to host ($SERVICE_HOST)."
        exit 2
    fi

    # Detect compose command on the remote server
    resolve_compose_cmd "$SERVICE_HOST"
    info "Remote compose command: ${COMPOSE_CMD}"

    info "Copying configuration files to server..."
    if ! scp "${DOCKER_DIR}/docker-compose-server.yml" "$SERVICE_HOST:$SERVER_WORK_DIR/docker-compose.yml"; then
        error "Failed to copy docker-compose-server.yml."
        exit 1
    fi
    if ! scp "$ENV_FILE" "$SERVICE_HOST:$SERVER_WORK_DIR/.env_${ENV_NAME}"; then
        error "Failed to copy environment file."
        exit 1
    fi

    local REMOTE_CMD="$COMPOSE_CMD -f $SERVER_WORK_DIR/docker-compose.yml --env-file $SERVER_WORK_DIR/.env_${ENV_NAME}"

    info "Pulling latest image from registry..."
    if ! ssh "$SERVICE_HOST" "$REMOTE_CMD pull"; then
        error "Failed to pull image from registry."
        exit 1
    fi

    info "Starting containers..."
    if ! ssh "$SERVICE_HOST" "$REMOTE_CMD up -d --remove-orphans"; then
        error "Failed to start containers."
        exit 1
    fi

    success "Deployment completed successfully."
    return 0
}

function main() {
    if ! deploy_proxy_manager "$@"; then
        exit 1
    fi
    exit 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
