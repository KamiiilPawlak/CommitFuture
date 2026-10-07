#!/usr/bin/env bash

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
GRAY='\033[0;90m'
RED='\033[0;31m'
NC='\033[0m'


invoke_python_cleanup() {
    echo -e "${CYAN}Czyszczenie plików tymczasowych Pythona...${NC}"

    find . -type d \( \
        -name "__pycache__" -o \
        -name "*.egg-info" -o \
        -name ".pytest_cache" -o \
        -name ".mypy_cache" -o \
        -name ".ruff_cache" -o \
        -name ".tox" -o \
        -name ".cache" -o \
        -name "build" -o \
        -name "dist" \
    \) -exec rm -rf {} + 2>/dev/null

    find . -type f \( \
        -name "*.pyc" -o \
        -name "*.pyo" -o \
        -name ".coverage" \
    \) -exec rm -f {} + 2>/dev/null
}


test_docker_running() {
    if docker info >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}


invoke_docker_cleanup() {
    if ! test_docker_running; then
        echo -e "${YELLOW}Docker nie jest uruchomiony. Pomijam czyszczenie kontenerów Docker.${NC}"
        return 0
    fi


    read -p "Czy chcesz usunąć powiązane kontenery Docker? (y/n): " odpowiedz


    odpowiedz=$(echo "$odpowiedz" | tr '[:upper:]' '[:lower:]')

    if [[ "$odpowiedz" != "y" && "$odpowiedz" != "yes" && "$odpowiedz" != "t" && "$odpowiedz" != "tak" ]]; then
        echo -e "${GRAY}Pominięto czyszczenie kontenerów Docker.${NC}"
        return 0
    fi

    echo -e "${CYAN}Zatrzymywanie i czyszczenie kontenerów Docker...${NC}"
    docker-compose down --remove-orphans
}


invoke_python_cleanup
invoke_docker_cleanup

echo -e "${GREEN}Gotowe! Projekt wyczyszczony.${NC}"
