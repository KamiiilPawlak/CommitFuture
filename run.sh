#!/usr/bin/env bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ACTION=""
NO_CACHE=false

for arg in "$@"; do
    case $arg in
        --no-cache)
            NO_CACHE=true
            ;;
        clean|build)
            ACTION="$arg"
            ;;
        *)
            ;;
    esac
done

if [ -f "backend/.venv/bin/activate" ]; then
    source backend/.venv/bin/activate
fi

case "$ACTION" in
    clean)
        ./scripts/clean.sh
        ;;

    build)
        if [ "$NO_CACHE" = true ]; then
            ./scripts/build.sh --force-build --no-cache
        else
            ./scripts/build.sh --force-build
        fi
        ;;

    *)
        ./scripts/build.sh
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Uruchamiam kontenery...${NC}"
            docker-compose up
        else
            echo -e "${RED}Anulowano uruchamianie aplikacji.${NC}"
        fi
        ;;
esac