#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Track-1 Competition Launcher
# Starts all services needed for a competition run.
#
# Usage:
#   ./scripts/start_competition.sh simulation 5
#   ./scripts/start_competition.sh real 3
#   ./scripts/start_competition.sh groot 1
# ──────────────────────────────────────────────────────

MODE="${1:-simulation}"
EPISODES="${2:-1}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# --- Config (override via env vars) ---
LIVEKIT_URL="${LIVEKIT_URL:-ws://127.0.0.1:7880}"
LIVEKIT_API_KEY="${LIVEKIT_API_KEY:-API4DMWY4jSEmer}"
LIVEKIT_API_SECRET="${LIVEKIT_API_SECRET:-JWbzTgL0ZuIycEG30kRvyVa0ohF5mH8GOtKBinblxhN}"
TOKEN_SERVER_PORT="${TOKEN_SERVER_PORT:-3000}"
TELEMETRY_PORT="${TELEMETRY_PORT:-8765}"
DASHBOARD_PORT="${DASHBOARD_PORT:-3001}"
ROOM_NAME="${ROOM_NAME:-track1-room}"
ROBOT_PORT="${ROBOT_PORT:-/dev/ttyACM0}"
GROOT_SERVER="${GROOT_SERVER:-localhost:5555}"
ACT_CHECKPOINT="${ACT_CHECKPOINT:-checkpoints/act_so100}"

# Track PIDs for cleanup
PIDS=()

cleanup() {
    echo ""
    echo "Shutting down all services..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null
    echo "All services stopped."
}

trap cleanup EXIT INT TERM

echo "╔══════════════════════════════════════════════════════╗"
echo "║         Track-1 Competition Launcher                ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Mode:     $MODE"
echo "║  Episodes: $EPISODES"
echo "║  LiveKit:  $LIVEKIT_URL"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# --- 1) Token Server ---
echo "[1/4] Starting token server on port $TOKEN_SERVER_PORT..."
export LIVEKIT_API_KEY LIVEKIT_API_SECRET
cd "$ROOT_DIR/services/livekit"
if [ ! -d "node_modules" ]; then
    echo "  Installing token server deps..."
    npm install --silent
fi
PORT="$TOKEN_SERVER_PORT" node token_server.mjs &
PIDS+=($!)
cd "$ROOT_DIR"
sleep 1
echo "  Token server ready at http://127.0.0.1:$TOKEN_SERVER_PORT/token"

# --- 2) Next.js Dashboard ---
echo "[2/4] Starting judge dashboard on port $DASHBOARD_PORT..."
cd "$ROOT_DIR/web"
if [ ! -d "node_modules" ]; then
    echo "  Installing dashboard deps..."
    npm install --silent
fi
PORT="$DASHBOARD_PORT" npm run dev -- --port "$DASHBOARD_PORT" > /dev/null 2>&1 &
PIDS+=($!)
cd "$ROOT_DIR"
sleep 2
echo "  Dashboard ready at http://127.0.0.1:$DASHBOARD_PORT"

# --- 3) Static file server for robot_publisher.html ---
echo "[3/4] Starting robot publisher server on port 8080..."
python3 -m http.server 8080 --directory "$ROOT_DIR" > /dev/null 2>&1 &
PIDS+=($!)
echo "  Robot publisher at http://127.0.0.1:8080/livekit/robot_publisher.html"

# --- 4) Autonomy Runtime ---
echo "[4/4] Starting autonomy runtime (mode=$MODE, episodes=$EPISODES)..."
echo ""

case "$MODE" in
    simulation)
        python3 "$ROOT_DIR/scripts/run_demo.py" \
            --seed 7 \
            --goal-target cup \
            --max-retries-step 2 \
            --max-replans 3 \
            --max-ticks 80 \
            --http-port "$TELEMETRY_PORT" \
            --episodes "$EPISODES" \
            --verbose &
        PIDS+=($!)
        ;;
    real)
        python3 "$ROOT_DIR/scripts/run_real_robot.py" \
            --policy symbolic \
            --robot-port "$ROBOT_PORT" \
            --http-port "$TELEMETRY_PORT" \
            --episodes "$EPISODES" \
            --verbose &
        PIDS+=($!)
        ;;
    act)
        python3 "$ROOT_DIR/scripts/run_real_robot.py" \
            --policy act \
            --robot-port "$ROBOT_PORT" \
            --checkpoint "$ACT_CHECKPOINT" \
            --http-port "$TELEMETRY_PORT" \
            --episodes "$EPISODES" \
            --verbose &
        PIDS+=($!)
        ;;
    groot)
        python3 "$ROOT_DIR/scripts/run_real_robot.py" \
            --policy groot \
            --robot-port "$ROBOT_PORT" \
            --groot-server "$GROOT_SERVER" \
            --http-port "$TELEMETRY_PORT" \
            --episodes "$EPISODES" \
            --verbose &
        PIDS+=($!)
        ;;
    *)
        echo "Unknown mode: $MODE (use: simulation, real, act, groot)"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  All services running. URLs:"
echo ""
echo "    Dashboard:        http://127.0.0.1:$DASHBOARD_PORT"
echo "    Robot Publisher:   http://127.0.0.1:8080/livekit/robot_publisher.html"
echo "    Token Server:     http://127.0.0.1:$TOKEN_SERVER_PORT/token"
echo "    Telemetry Feed:   http://127.0.0.1:$TELEMETRY_PORT/latest"
echo ""
echo "  Press Ctrl+C to stop all services."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait for autonomy to finish, then keep dashboard alive
wait "${PIDS[-1]}" 2>/dev/null || true

echo ""
echo "Autonomy runtime finished. Dashboard still running."
echo "Press Ctrl+C to stop remaining services."
wait
