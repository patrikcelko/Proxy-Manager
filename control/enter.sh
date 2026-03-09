#!/usr/bin/env bash

function _fetch_containers {
    docker ps --format "{{.ID}} ({{.Image}}): {{.Names}}"
}

function enter {
    for ARG in $@; do
        if [[ "$ARG" == "-r" ]]; then
                AS_ROOT="-u 0"
        elif [[ -n "$ARG" && ${#ARG} -ge 3 ]]; then
                PATTERN=$ARG
        fi
    done

    info "Fetching available Docker containers..."
    if [[ -z "$PATTERN" ]]; then
        echo
        _fetch_containers
        echo
        read -p "${C_BLUE}■ ${C_BRIGHT_WHITE}Enter ID or name: " PATTERN
    fi

    CONTAINER=$(_fetch_containers | grep -i $PATTERN | head -1)
    ID=$(echo $CONTAINER | awk '{print $1}')
    NAME=$(echo $CONTAINER | awk '{print $3}')
    if [[ -z "$ID" ]]; then
        error "No container matched."
        exit 0
    fi

    success "Entering container $NAME ($ID)${C_BRIGHT_WHITE}"
    docker exec $AS_ROOT -it $ID /bin/bash
}
