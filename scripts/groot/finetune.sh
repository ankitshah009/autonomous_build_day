#!/usr/bin/env bash
set -euo pipefail

# Fine-tune GR00T N1.6 on SO-ARM100 dataset.
# Requires 48GB+ VRAM (H100, L40, or RTX A6000).
# Usage: ./scripts/groot/finetune.sh <dataset_path> [output_dir] [max_steps]

DATASET_PATH="${1:?Usage: $0 <dataset_path> [output_dir] [max_steps]}"
OUTPUT_DIR="${2:-checkpoints/groot}"
MAX_STEPS="${3:-10000}"
BASE_MODEL="${GROOT_BASE_MODEL:-nvidia/GR00T-N1.6-3B}"
NUM_GPUS="${NUM_GPUS:-1}"
BATCH_SIZE="${BATCH_SIZE:-32}"

echo "=== GR00T N1.6 Fine-Tuning ==="
echo "Dataset:    $DATASET_PATH"
echo "Base model: $BASE_MODEL"
echo "Output:     $OUTPUT_DIR"
echo "Max steps:  $MAX_STEPS"
echo "GPUs:       $NUM_GPUS"
echo "Batch size: $BATCH_SIZE"
echo ""
echo "This requires 48GB+ VRAM and may take several hours."
echo ""

mkdir -p "$OUTPUT_DIR"

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" python \
  gr00t/experiment/launch_finetune.py \
  --base-model-path "$BASE_MODEL" \
  --dataset-path "$DATASET_PATH" \
  --embodiment-tag NEW_EMBODIMENT \
  --modality-config-path examples/SO100/so100_config.py \
  --num-gpus "$NUM_GPUS" \
  --output-dir "$OUTPUT_DIR" \
  --max-steps "$MAX_STEPS" \
  --global-batch-size "$BATCH_SIZE" \
  --save-steps 2000 \
  --save-total-limit 5 \
  --dataloader-num-workers 4 \
  --color-jitter-params brightness 0.3 contrast 0.4 saturation 0.5 hue 0.08

echo ""
echo "Fine-tuning complete!"
echo "Checkpoint saved to: $OUTPUT_DIR"
echo ""
echo "Next step:"
echo "  ./scripts/groot/deploy.sh $OUTPUT_DIR"
