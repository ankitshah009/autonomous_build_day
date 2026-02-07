#!/usr/bin/env bash
set -euo pipefail

# Deploy GR00T N1.6 inference (server + optional robot client).
# Usage: ./scripts/groot/deploy.sh <checkpoint_dir> [mode]
#   mode: server | client | both (default: server)

CHECKPOINT_DIR="${1:?Usage: $0 <checkpoint_dir> [mode]}"
MODE="${2:-server}"
POLICY_PORT="${POLICY_PORT:-5555}"
ROBOT_PORT="${ROBOT_PORT:-/dev/ttyACM0}"
WRIST_CAM="${WRIST_CAMERA_ID:-0}"
FRONT_CAM="${FRONT_CAMERA_ID:-2}"
LANG_INSTRUCTION="${LANG_INSTRUCTION:-Pick up the object and place it in the bin}"

start_server() {
  echo "=== Starting GR00T Policy Server ==="
  echo "Checkpoint: $CHECKPOINT_DIR"
  echo "Port:       $POLICY_PORT"
  echo ""

  python gr00t/eval/run_gr00t_server.py \
    --model-path "$CHECKPOINT_DIR" \
    --embodiment-tag NEW_EMBODIMENT \
    --port "$POLICY_PORT"
}

start_client() {
  echo "=== Starting Robot Client ==="
  echo "Server:   localhost:$POLICY_PORT"
  echo "Robot:    $ROBOT_PORT"
  echo "Task:     $LANG_INSTRUCTION"
  echo ""

  python gr00t/eval/real_robot/SO100/eval_so100.py \
    --robot.type=so100_follower \
    --robot.port="$ROBOT_PORT" \
    --robot.id=track1_follower \
    --robot.cameras="{ wrist: {type: opencv, index_or_path: $WRIST_CAM, width: 640, height: 480, fps: 30}, front: {type: opencv, index_or_path: $FRONT_CAM, width: 640, height: 480, fps: 30} }" \
    --policy_host=localhost \
    --policy_port="$POLICY_PORT" \
    --lang_instruction="$LANG_INSTRUCTION"
}

case "$MODE" in
  server)
    start_server
    ;;
  client)
    start_client
    ;;
  both)
    start_server &
    SERVER_PID=$!
    echo "Server PID: $SERVER_PID"
    echo "Waiting 10s for server to start..."
    sleep 10
    start_client
    wait "$SERVER_PID"
    ;;
  *)
    echo "Unknown mode: $MODE (use: server, client, both)" >&2
    exit 1
    ;;
esac
