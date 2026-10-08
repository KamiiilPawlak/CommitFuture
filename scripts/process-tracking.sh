SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_DIR="$REPO_ROOT/PID"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_LAUNCHER_PID_FILE="$PID_DIR/backend-launcher.pid"
FRONTEND_LAUNCHER_PID_FILE="$PID_DIR/frontend-launcher.pid"

mkdir -p "$PID_DIR"

stop_tracked_process() {
    local pid_file="$1"
    local label="$2"

    if [ ! -f "$pid_file" ]; then
        return 0
    fi

    local tracked_pid
    tracked_pid=$(cat "$pid_file" 2>/dev/null)

    if [ -n "$tracked_pid" ] && kill -0 "$tracked_pid" 2>/dev/null; then
        # odpowiednik `taskkill /PID $pid /T /F` z run.ps1: najpierw lagodnie (TERM)
        # dzieci (-P) i sam proces, a jesli po chwili ktos przezyl - dobijamy KILL.
        pkill -TERM -P "$tracked_pid" 2>/dev/null
        kill -TERM "$tracked_pid" 2>/dev/null
        sleep 1
        pkill -KILL -P "$tracked_pid" 2>/dev/null
        kill -KILL "$tracked_pid" 2>/dev/null
    fi

    rm -f "$pid_file"
}

source "$SCRIPT_DIR/backend.sh"
source "$SCRIPT_DIR/frontend.sh"

invoke_start_all() {
    echo -e "${CYAN}Uruchomienie backendu i frontendu w tle...${NC}"

    local backend_log="$PID_DIR/backend.log"
    local frontend_log="$PID_DIR/frontend.log"

    nohup "$REPO_ROOT/run.sh" backend > "$backend_log" 2>&1 &
    echo "$!" > "$BACKEND_LAUNCHER_PID_FILE"
    disown
    nohup "$REPO_ROOT/run.sh" frontend > "$frontend_log" 2>&1 &
    echo "$!" > "$FRONTEND_LAUNCHER_PID_FILE"
    disown

    echo -e "${GREEN}Backend (uvicorn) i frontend (npm run dev) zostaly wystartowane w tle.${NC}"
    echo -e "${GREEN}Logi: ${backend_log}, ${frontend_log}${NC}"
}

invoke_stop_all() {
    stop_tracked_process "$BACKEND_PID_FILE" "Backend"
    stop_tracked_process "$FRONTEND_PID_FILE" "Frontend"
    stop_tracked_process "$BACKEND_LAUNCHER_PID_FILE" "Okno Backend"
    stop_tracked_process "$FRONTEND_LAUNCHER_PID_FILE" "Okno Frontend"
    echo -e "${GREEN}Aplikacja wylaczona.${NC}"
}
