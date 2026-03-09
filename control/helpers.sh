#!/usr/bin/env bash

C_BLACK=$(tput setaf 0)
C_RED=$(tput setaf 1)
C_GREEN=$(tput setaf 2)
C_YELLOW=$(tput setaf 3)
C_BLUE=$(tput setaf 4)
C_MAGENTA=$(tput setaf 5)
C_CYAN=$(tput setaf 6)
C_WHITE=$(tput setaf 7)
C_BRIGHT_BLACK=$(tput setaf 8)
C_BRIGHT_RED=$(tput setaf 9)
C_BRIGHT_GREEN=$(tput setaf 10)
C_BRIGHT_YELLOW=$(tput setaf 11)
C_BRIGHT_BLUE=$(tput setaf 12)
C_BRIGHT_MAGENTA=$(tput setaf 13)
C_BRIGHT_CYAN=$(tput setaf 14)
C_BRIGHT_WHITE=$(tput setaf 15)
C_NC=$(tput sgr0)

function option {
	echo -e "${C_GREEN}$1${C_WHITE}"
}

function success {
    echo -e "${C_GREEN}[OK] $1${C_NC}"
}

function error {
    echo -e "${C_RED}[Error] $1${C_NC}"
}

function info {
    echo -e "${C_CYAN}[Info] $1${C_NC}"
}

function warning {
    echo -e "${C_YELLOW}[Warning] $1${C_NC}"
}

function logo {
    echo -e "${C_GREEN}";
    echo -e "  ____                        __  __                                   ";
    echo -e " |  _ \\ _ __ _____  ___   _  |  \\/  |  _ _ _ __   __ _  __ _  ___ _ __ ";
    echo -e " | |_) | '__/ _ \\ \\/ / | | | | |\\/| |/  _\`| '_ \\ / _\` |/ _\` |/ _ \\ '__|";
    echo -e " |  __/| | | (_) >  <| |_| | | |  | | (_| | | | | (_| | (_| |  __/ |   ";
    echo -e " |_|   |_|  \\___/_/\\_\\\\\\__, | |_|  |_|\\__,_|_| |_|\\__,_|\\__, |\\___|_|   ";
    echo -e "                      |___/                             |___/           ";
    printf "${C_NC}";
}

function header {
    echo -e "${C_YELLOW}▄${C_WHITE}"
    echo -e "${C_YELLOW}█ ${C_WHITE}${C_RED}$1${C_WHITE}"
    echo -e "${C_YELLOW}▀${C_WHITE}"
}

function print_help {
    logo
    header "Proxy Manager helper-script"

    option "  help"
    echo "    Display this help message."

    option "  deploy [env]"
    echo "    Deploy Proxy Manager to a remote server. Uses .env_<env> (default: prod)."
    echo "    The ENV_NAME from the env file determines the image tag pulled from registry."

    option "  build"
    echo "    Build the Docker image and push it to the registry."

    option "  start-docker [env]"
    echo "    Start already built container. Uses .env_<env> (default: local)."
    echo "    Note that if the container is not built, this process will fail."

    option "  rebuild-docker [env]"
    echo "    This command will add a forced build attribute to docker compose."
    echo "    Uses .env_<env> (default: local). It should not affect stored data."

    option "  kill-docker"
    echo "    Forcefully kills all running docker containers (all containers!)."

    option "  enter [name|id]"
    echo "    Allows us to enter any of the running docker containers if an ID"
    echo "    or name is provided. If left empty, a listing will be displayed."
    echo
}

# Resolve which docker compose binary to use (v2 plugin vs v1 standalone).
function resolve_compose_cmd() {
    local remote_host="$1"

    if [[ -z "$remote_host" ]]; then
        # Local detection (skip if already resolved without a host)
        if [[ -n "${COMPOSE_CMD+x}" ]]; then
            return 0
        fi

        if docker compose version &>/dev/null; then
            COMPOSE_CMD="docker compose"
        elif command -v docker-compose &>/dev/null; then
            COMPOSE_CMD="docker-compose"
        else
            error "Neither 'docker compose' (v2) nor 'docker-compose' (v1) found."
            exit 1
        fi
    else
        # Remote detection via SSH
        if ssh "$remote_host" "docker compose version" &>/dev/null; then
            COMPOSE_CMD="docker compose"
        elif ssh "$remote_host" "command -v docker-compose" &>/dev/null; then
            COMPOSE_CMD="docker-compose"
        else
            error "Neither 'docker compose' (v2) nor 'docker-compose' (v1) found on ${remote_host}."
            exit 1
        fi
    fi
}

# Resolve the env-file path for a given environment name.
function resolve_env_file() {
    local env_name="${1:-local}"
    local docker_dir="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}/docker"
    ENV_FILE="${docker_dir}/data/.env_${env_name}"

    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: ${ENV_FILE}"
        exit 1
    fi

    info "Using environment: .env_${env_name}"
}