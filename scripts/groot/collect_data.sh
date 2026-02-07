#!/usr/bin/env bash
set -euo pipefail

# Collect demonstration data from SO-ARM100 using LeRobot teleoperation.
# Usage: ./scripts/groot/collect_data.sh <dataset_name> [num_episodes] [task_description]

DATASET_NAME="${1:?Usage: $0 <dataset_name> [num_episodes] [task]}"
NUM_EPISODES="${2:-50}"
TASK="${3:-Pick up the object and place it in the bin}"
ROBOT_PORT="${ROBOT_PORT:-/dev/ttyACM0}"
WRIST_CAM="${WRIST_CAMERA_ID:-0}"
FRONT_CAM="${FRONT_CAMERA_ID:-2}"

echo "=== Track-1 Data Collection ==="
echo "Dataset:  $DATASET_NAME"
echo "Episodes: $NUM_EPISODES"
echo "Task:     $TASK"
echo "Port:     $ROBOT_PORT"
echo "Cameras:  wrist=$WRIST_CAM, front=$FRONT_CAM"
echo ""

lerobot-record \
  --robot.type=so100_follower \
  --robot.port="$ROBOT_PORT" \
  --robot.id=track1_follower \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: $WRIST_CAM, width: 640, height: 480, fps: 30}, front: {type: opencv, index_or_path: $FRONT_CAM, width: 640, height: 480, fps: 30} }" \
  --dataset.repo_id="$DATASET_NAME" \
  --dataset.num_episodes="$NUM_EPISODES" \
  --dataset.single_task="$TASK" \
  --display_data=true

echo ""
echo "Data collection complete!"
echo "Next: ./scripts/groot/prepare_data.py --dataset-dir data/$DATASET_NAME"
