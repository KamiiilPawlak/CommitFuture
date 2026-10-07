#!/usr/bin/env bash

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

TARGET="${1:-all}"

run_backend_quality() {
    echo -e "${CYAN}Uruchomienie narzędzi jakości kodu: backend (ruff, mypy, pytest)...${NC}"
    (cd backend && ruff check . && mypy . && pytest)
}

run_frontend_quality() {
    echo -e "${CYAN}Uruchomienie narzędzi jakości kodu: frontend (eslint, prettier, knip, jest)...${NC}"
    (cd frontend && npm run lint && npm run format:check && npm run knip && npm run test)
}

case "$TARGET" in
    backend)
        run_backend_quality
        ;;
    frontend)
        run_frontend_quality
        ;;
    all)
        run_backend_quality && run_frontend_quality
        ;;
    *)
        echo -e "${RED}BŁĄD: Nieznany target '$TARGET'. Dostępne: backend, frontend, all${NC}"
        exit 1
        ;;
esac

status=$?
if [ $status -eq 0 ]; then
    echo -e "${GREEN}Zakończono sprawdzanie jakości kodu (${TARGET}).${NC}"
fi
exit $status
