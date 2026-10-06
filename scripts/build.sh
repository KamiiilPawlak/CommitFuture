#!/usr/bin/env bash

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' 

FORCE_BUILD=false
NO_CACHE=false
RECREATE=false


for arg in "$@"; do
    case $arg in
        --force-build)
            FORCE_BUILD=true
            ;;
        --no-cache)
            NO_CACHE=true
            ;;
        --recreate)
            RECREATE=true
            ;;
    esac
done

test_docker_running() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}BŁĄD: Docker nie jest uruchomiony! Włącz Docker Desktop i spróbuj ponownie.${NC}"
        exit 1
    fi
}


test_docker_images_exist() {
    local compose_images
    compose_images=$(docker-compose config --images 2>/dev/null)
    for img in $compose_images; do
        if [ -z "$img" ]; then
            continue
        fi
        if [ -z "$(docker images -q "$img" 2>/dev/null)" ]; then
            return 1 
        fi
    done
    return 0 
}


invoke_docker_build_lifecycle() {
    local use_no_cache=$1
    local clean_old=$2

    if [ "$clean_old" = true ]; then
        echo -e "${YELLOW}Usuwanie starych kontenerów i czyszczenie...${NC}"
        docker-compose down --rmi local --volumes --remove-orphans
    fi

    if [ "$use_no_cache" = true ]; then
        echo -e "${CYAN}Budowanie obrazów od zera (BEZ CACHE)...${NC}"
        docker-compose build --no-cache
    else
        echo -e "${CYAN}Budowanie obrazów...${NC}"
        docker-compose build
    fi
}


start_docker_containers() {
    echo -e "${GREEN}Uruchamianie kontenerów (docker-compose up)...${NC}"
    docker-compose up -d
}

start_build_workflow() {
    test_docker_running

    if [ "$FORCE_BUILD" = true ] || [ "$RECREATE" = true ]; then
        invoke_docker_build_lifecycle "$NO_CACHE" "$FORCE_BUILD"
        start_docker_containers
        return 0
    fi

    echo -e "${CYAN}Sprawdzanie obecności obrazów Docker...${NC}"
    if ! test_docker_images_exist; then
        echo -e "${YELLOW}Brak obrazu – automatycznie uruchamiam budowanie...${NC}"
        invoke_docker_build_lifecycle false false
    else
        echo -e "${GREEN}Wszystkie obrazy są gotowe.${NC}"
    fi

    start_docker_containers
}

if start_build_workflow; then
    exit 0
else
    echo -e "${RED}BŁĄD: Wystąpił problem podczas budowania lub uruchamiania kontenerów.${NC}"
    exit 1
fi