#!/usr/bin/env bash

CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${CYAN}Czyszczenie plikow tymczasowych Pythona...${NC}"


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


if docker info >/dev/null 2>&1; then
    echo -e "${CYAN}Zatrzymywanie i czyszczenie kontenerow...${NC}"
    docker-compose down --remove-orphans
fi

echo -e "${GREEN}Gotowe! Projekt wyczyszczony.${NC}"