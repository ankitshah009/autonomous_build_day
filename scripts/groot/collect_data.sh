#!/usr/bin/env bash
set -euo pipefail

# Collect demonstration data from SO-ARM100 using LeRobot teleoperation.
#
# Prerequisites:
#   pip install -e . (from cloned lerobot repo)
#
# Usage:
#   ./scripts/groot/collect_data.sh <dataset_name> [num_episodes] [task_description]
#   ./scripts/groot/collect_data.sh my_pick_place 50 "Pick up the cup and place it in the bin"

DATASET_NAME="${1:?Usage: $0 <dataset_name> [num_episodes] [task]}"
NUM_EPISODES="${2:-50}"
TASK="${3:-Pick up the object and place it in the bin}"

# Robot config
ROBOT_TYPE="${ROBOT_TYPE:-so100_follower}"
TELEOP_TYPE="${TELEOP_TYPE:-so100_leader}"
ROBOT_PORT="${ROBOT_PORT:-/dev/tty.usbmodem5AB01833401}"
TELEOP_PORT="${TELEOP_PORT:-/dev/tty.usbmodem5A4B0479761}"
HF_USER="${HF_USER:-ankits0052}"

# Camera config
WRIST_CAM="${WRIST_CAMERA_ID:-1}"
FRONT_CAM="${FRONT_CAMERA_ID:-0}"

# Timing
EPISODE_TIME="${EPISODE_TIME_S:-45}"
RESET_TIME="${RESET_TIME_S:-15}"

echo "=== Track-1 Data Collection ==="
echo "Dataset:      $DATASET_NAME"
echo "Episodes:     $NUM_EPISODES"
echo "Task:         $TASK"
echo "Follower:     $ROBOT_TYPE on $ROBOT_PORT"
echo "Leader:       $TELEOP_TYPE on $TELEOP_PORT"
echo "Cameras:      wrist=$WRIST_CAM, front=$FRONT_CAM"
echo "Episode time: ${EPISODE_TIME}s (reset: ${RESET_TIME}s)"
echo ""

lerobot-record \
  --robot.type="$ROBOT_TYPE" \
  --robot.port="$ROBOT_PORT" \
  --robot.cameras='{ "wrist": {"type": "opencv", "index_or_path": '"$WRIST_CAM"', "width": 640, "height": 480, "fps": 30}, "front": {"type": "opencv", "index_or_path": '"$FRONT_CAM"', "width": 640, "height": 480, "fps": 30} }' \
  --teleop.type="$TELEOP_TYPE" \
  --teleop.port="$TELEOP_PORT" \
  --display_data=true \
  --dataset.repo_id="$HF_USER/$DATASET_NAME" \
  --dataset.num_episodes="$NUM_EPISODES" \
  --dataset.single_task="$TASK" \
  --dataset.episode_time_s="$EPISODE_TIME" \
  --dataset.reset_time_s="$RESET_TIME" \
  --dataset.push_to_hub=true

echo ""
echo "Data collection complete!"
echo "Dataset saved to: data/$DATASET_NAME"
echo ""
echo "Next steps:"
echo "  1. Prepare: python scripts/groot/prepare_data.py --dataset-path data/$DATASET_NAME"
echo "  2. Fine-tune (on CUDA machine): ./scripts/groot/finetune.sh data/$DATASET_NAME checkpoints/groot"
