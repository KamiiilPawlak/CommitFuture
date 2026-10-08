invoke_frontend() {
    local frontend_path="$REPO_ROOT/frontend"
    if [ ! -d "$frontend_path" ]; then
        echo -e "${RED}BŁĄD: Nie znaleziono katalogu frontend${NC}"
        exit 1
    fi

    echo -e "${CYAN}Uruchomienie React (npm run dev)...${NC}"
    (
        cd "$frontend_path" || exit 1
        npm run dev &
        local pid=$!
        echo "$pid" > "$FRONTEND_PID_FILE"
        wait "$pid"
    )
    rm -f "$FRONTEND_PID_FILE"
}

invoke_stop_frontend() {
    stop_tracked_process "$FRONTEND_PID_FILE" "Frontend"
    echo -e "${GREEN}Frontend wylaczony.${NC}"
}
