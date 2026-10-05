#!/usr/bin/env bash

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

FORCE_BUILD=false
NO_CACHE=false

for arg in "$@"; do
    case $arg in
        --force-build)
            FORCE_BUILD=true
            ;;
        --no-cache)
            NO_CACHE=true
            ;;
    esac
done

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}BLAD: Docker nie jest uruchomiony! Uruchom usługę Docker i spróbuj ponownie.${NC}"
    exit 1
fi

if [ "$FORCE_BUILD" = true ]; then
    if [ "$NO_CACHE" = true ]; then
        echo -e "${CYAN}Wymuszone budowanie obrazow (BEZ CACHE)...${NC}"
        docker-compose build --no-cache
    else
        echo -e "${CYAN}Wymuszone budowanie obrazow Docker...${NC}"
        docker-compose build
    fi
    exit $?
fi

echo -e "${CYAN}Sprawdzanie obecnosci obrazow Docker...${NC}"
COMPOSE_IMAGES=$(docker-compose config --images 2>/dev/null)
MISSING_IMAGE=false

for img in $COMPOSE_IMAGES; do
    if [ -z "$img" ]; then
        continue
    fi
    if [ -z "$(docker images -q "$img" 2>/dev/null)" ]; then
        MISSING_IMAGE=true
        break
    fi
done

if [ "$MISSING_IMAGE" = true ]; then
    echo -e "${YELLOW}Brak obrazu – automatycznie uruchamiam budowanie...${NC}"
    docker-compose build
else
    echo -e "${GREEN}Wszystkie obrazy sa gotowe.${NC}"
fi

exit $?