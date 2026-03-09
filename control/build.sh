#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/helpers.sh"

if [[ -z "${IMAGE_NAME+x}" ]]; then
    readonly IMAGE_NAME="proxy-manager"
    readonly ENV_NAME="prod"
    readonly DOCKER_REGISTRY="harbor.celko.cz/proxy-manager"
    readonly DOCKER_DIR="${PROJECT_ROOT}/docker"
fi

export DOCKER_BUILDKIT=1

function build_proxy_manager() {
    info "Building Docker image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${ENV_NAME}"
    cd "${DOCKER_DIR}"

    if ! docker buildx build --load --no-cache --pull \
        -t "${DOCKER_REGISTRY}/${IMAGE_NAME}:${ENV_NAME}" \
        -f Dockerfile ..; then
        error "Docker build failed."
        return 1
    fi

    success "Docker image built successfully."
    cd "${SCRIPT_DIR}"
    return 0
}

function push_to_registry() {
    info "Pushing image to registry: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${ENV_NAME}"

    if ! docker push "${DOCKER_REGISTRY}/${IMAGE_NAME}:${ENV_NAME}"; then
        error "Docker push to registry failed."
        return 1
    fi

    success "Image pushed to registry successfully."
    return 0
}

function main() {
    if ! build_proxy_manager; then
        error "Build failed."
        exit 1
    fi

    if ! push_to_registry; then
        error "Push to registry failed."
        exit 1
    fi

    success "Build and push completed successfully."
    exit 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi