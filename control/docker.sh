#!/usr/bin/env bash

function rebuild_docker_containers_proxy_manager () {
    local env_name="${1:-local}"
    resolve_compose_cmd
    resolve_env_file "$env_name"

    local compose_file="${PROJECT_ROOT}/docker/docker-compose.yml"

    info "Rebuilding containers for Proxy Manager (env: ${env_name}). Please wait..."

    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" down
    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" build --no-cache
    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" up -d
}

function start_docker_container_proxy_manager () {
    local env_name="${1:-local}"
    resolve_compose_cmd
    resolve_env_file "$env_name"

    local compose_file="${PROJECT_ROOT}/docker/docker-compose.yml"

    info "Starting docker containers for Proxy Manager (env: ${env_name}). Please wait..."

    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" up -d
}
