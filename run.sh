#!/usr/bin/env bash

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ACTION="default"
FORCE_BUILD=false
NO_CACHE=false
RECREATE=false


while [[ "$#" -gt 0 ]]; do
    case $1 in
        clean|cleanup|build|dev|default|backend|frontend|start|stop|stop-backend|stop-frontend|quality|quality-backend|quality-frontend|help)
            ACTION="$1"
            shift
            ;;
        --force-build)
            FORCE_BUILD=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --recreate)
            RECREATE=true
            shift
            ;;
        *)
            if [ "$ACTION" = "default" ] && [[ "$1" != -* ]]; then
                ACTION="$1"
            fi
            shift
            ;;
    esac
done



invoke_cleanup_task() {
    local script_path="./scripts/cleanup.sh"
    if [ -f "$script_path" ]; then
        echo -e "${CYAN}Uruchomienie zadania: Cleanup...${NC}"
        bash "$script_path"
    else
        echo -e "${RED}BŁĄD: Nie znaleziono pliku skryptu: $script_path${NC}"
        exit 1
    fi
}

invoke_build_task() {
    local script_path="./scripts/build.sh"
    if [ -f "$script_path" ]; then
        echo -e "${CYAN}Uruchomienie zadania: Build / Lifecycle...${NC}"


        local args=()
        if [ "$FORCE_BUILD" = true ]; then
            args+=("--force-build")
        fi
        if [ "$NO_CACHE" = true ]; then
            args+=("--no-cache")
        fi
        if [ "$RECREATE" = true ]; then
            args+=("--recreate")
        fi

        bash "$script_path" "${args[@]}"
    else
        echo -e "${RED}BŁĄD: Nie znaleziono pliku skryptu: $script_path${NC}"
        exit 1
    fi
}

invoke_dev() {
    local venv_path="backend/.venv/bin/activate"
    if [ -f "$venv_path" ]; then
        echo -e "${CYAN}Aktywacja środowiska wirtualnego Pythona...${NC}"

        source "$venv_path"
        echo -e "${GREEN}Środowisko .venv aktywowane.${NC}"
    else
        echo -e "${YELLOW}Nie znaleziono środowiska wirtualnego Pythona. Pomijam aktywację.${NC}"
    fi
}

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/process-tracking.sh"

invoke_quality() {
    local quality_target="$1"
    local script_path="./scripts/quality.sh"
    if [ -f "$script_path" ]; then
        echo -e "${CYAN}Uruchomienie zadania: Quality (${quality_target})...${NC}"
        bash "$script_path" "$quality_target"
    else
        echo -e "${RED}BŁĄD: Nie znaleziono pliku skryptu: $script_path${NC}"
        exit 1
    fi
}

invoke_default_workflow() {
    invoke_build_task
}

show_help() {
    echo -e "${CYAN}Uzycie: ./run.sh <akcja> [--force-build] [--no-cache] [--recreate]${NC}"
    echo -e "${YELLOW}Dostepne akcje: clean, cleanup, build, dev, backend, frontend, start, stop, stop-backend, stop-frontend, quality, quality-backend, quality-frontend, default, help${NC}"
}


invoke_orchestrator() {
    case "$ACTION" in
        clean|cleanup)
            invoke_cleanup_task
            ;;
        build)
            invoke_build_task
            ;;
        dev)
            invoke_dev
            ;;
        backend)
            invoke_start
            ;;
        frontend)
            invoke_frontend
            ;;
        start)
            invoke_start_all
            ;;
        stop)
            invoke_stop_all
            ;;
        stop-backend)
            invoke_stop_backend
            ;;
        stop-frontend)
            invoke_stop_frontend
            ;;
        quality)
            invoke_quality "all"
            ;;
        quality-backend)
            invoke_quality "backend"
            ;;
        quality-frontend)
            invoke_quality "frontend"
            ;;
        default)
            invoke_default_workflow
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}BŁĄD: Nieznana akcja '$ACTION'.${NC}"
            show_help
            exit 1
            ;;
    esac
}


if invoke_orchestrator; then
    echo -e "${GREEN}Success${NC}"
    exit 0
else
    echo -e "${RED}BŁĄD WYKONANIA${NC}"
    exit 1
fi
