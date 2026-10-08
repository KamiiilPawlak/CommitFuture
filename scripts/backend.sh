invoke_start() {
    local uvicorn_path="$REPO_ROOT/backend/.venv/bin/uvicorn"
    if [ ! -f "$uvicorn_path" ]; then
        echo -e "${RED}BŁĄD: Nie znaleziono uvicorn w srodowisku wirtualnym: backend/.venv/bin/uvicorn${NC}"
        exit 1
    fi

    echo -e "${CYAN}Uruchomienie FastAPI (uvicorn)...${NC}"
    (
        cd "$REPO_ROOT/backend" || exit 1
        "$uvicorn_path" app.main:app --reload &
        local pid=$!
        echo "$pid" > "$BACKEND_PID_FILE"
        wait "$pid"
    )
    rm -f "$BACKEND_PID_FILE"
}

invoke_stop_backend() {
    stop_tracked_process "$BACKEND_PID_FILE" "Backend"
    echo -e "${GREEN}Backend wylaczony.${NC}"
}
