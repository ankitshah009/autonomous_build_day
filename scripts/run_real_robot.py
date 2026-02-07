#!/usr/bin/env python3
"""Run Track-1 autonomy on real SO-ARM100 hardware.

Supports three policy modes:
  - symbolic: classical planner (default, same as sim)
  - act:      LeRobot ACT policy checkpoint
  - groot:    GR00T N1.6 inference server

Usage:
  python scripts/run_real_robot.py --policy symbolic --robot-port /dev/ttyACM0
  python scripts/run_real_robot.py --policy act --checkpoint checkpoints/act_so100
  python scripts/run_real_robot.py --policy groot --groot-server localhost:5555
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy import Goal, ObjClass, PerceptionModule, Planner, StepExecutor, Track1Agent
from autonomy.lerobot_adapter import LeRobotAdapter
from autonomy.perception_providers import CameraPerceptionProvider, YOLOWorldDetector
from autonomy.policy_router import PolicyRouter, PolicyType
from autonomy.telemetry import InMemorySink, JsonlSink, MultiSink, StdoutSink
from autonomy.telemetry_http import TelemetryHttpFeed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Track-1 on real SO-ARM100 hardware")
    parser.add_argument("--policy", choices=["symbolic", "act", "groot"], default="symbolic",
                        help="Policy type (default: symbolic)")
    parser.add_argument("--robot-port", default="/dev/ttyACM0",
                        help="Serial port for SO-ARM100")
    parser.add_argument("--robot-type", default="so100_follower",
                        help="LeRobot robot type")
    parser.add_argument("--camera-wrist", type=int, default=0,
                        help="Wrist camera device index")
    parser.add_argument("--camera-front", type=int, default=2,
                        help="Front camera device index")
    parser.add_argument("--checkpoint", default="",
                        help="Path to ACT policy checkpoint (required for --policy act)")
    parser.add_argument("--groot-server", default="localhost:5555",
                        help="GR00T inference server address (for --policy groot)")
    parser.add_argument("--goal-target", default="cup",
                        choices=[c.value for c in ObjClass],
                        help="Target object class")
    parser.add_argument("--task-description", default="pick up the cup and place it in the bin",
                        help="Language instruction for GR00T/ACT")
    parser.add_argument("--yolo-classes", nargs="+",
                        default=["cup", "bottle", "bin", "drawer", "tool"],
                        help="Object classes for YOLO-World detector")
    parser.add_argument("--yolo-model", default="s", choices=["s", "m", "l"],
                        help="YOLO-World model size")
    parser.add_argument("--max-retries-step", type=int, default=2)
    parser.add_argument("--max-replans", type=int, default=3)
    parser.add_argument("--max-ticks", type=int, default=80)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--jsonl", default="runs/real_telemetry.jsonl")
    parser.add_argument("--http-port", type=int, default=8765,
                        help="Telemetry HTTP feed port (0 disables)")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # --- Robot ---
    camera_config = {"wrist": args.camera_wrist, "front": args.camera_front}
    robot = LeRobotAdapter(
        robot_type=args.robot_type,
        port=args.robot_port,
        camera_config=camera_config,
    )

    # --- Perception ---
    detector = YOLOWorldDetector(
        classes=args.yolo_classes,
        model_size=args.yolo_model,
    )
    camera_provider = CameraPerceptionProvider(
        camera_config=camera_config,
        detector=detector,
    )
    perception = PerceptionModule(provider=camera_provider)

    # --- Policy ---
    policy_type = PolicyType(args.policy)
    policy_router = PolicyRouter(
        policy_type=policy_type,
        checkpoint_path=args.checkpoint or None,
        server_url=args.groot_server if args.policy == "groot" else None,
    )

    # --- Goal ---
    target_class = ObjClass(args.goal_target)
    goal = Goal(goal_type="put_in_bin", target_obj_class=target_class)

    # --- Telemetry sinks ---
    jsonl_sink = JsonlSink(args.jsonl)
    memory_sink = InMemorySink()
    sinks: List[object] = [jsonl_sink, memory_sink]

    if args.verbose:
        sinks.append(StdoutSink())

    feed = None
    if args.http_port:
        try:
            feed = TelemetryHttpFeed(port=args.http_port)
            feed.start()

            class FeedSink:
                def emit(self, frame):
                    feed.update(frame.to_dict())

            sinks.append(FeedSink())
        except OSError as exc:
            print(f"warning: telemetry feed disabled ({exc})")
            feed = None

    sink = MultiSink(sinks)

    # --- Agent ---
    planner = Planner()
    executor = StepExecutor(planner)
    agent = Track1Agent(
        robot=robot,
        planner=planner,
        perception=perception,
        executor=executor,
        sink=sink,
        max_retries_per_step=args.max_retries_step,
        max_replans=args.max_replans,
    )

    # --- Run episodes ---
    successes = 0
    try:
        for idx in range(args.episodes):
            if idx > 0:
                robot.reset(seed=args.seed + idx)

            print(f"\n{'='*60}")
            print(f"Episode {idx + 1}/{args.episodes}  policy={args.policy}")
            print(f"{'='*60}")

            result = agent.run_episode(goal=goal, max_ticks=args.max_ticks)
            if result.metrics.success:
                successes += 1

            print(
                f"episode={idx + 1} success={result.metrics.success} "
                f"steps={result.metrics.steps_executed} retries={result.metrics.retries} "
                f"replans={result.metrics.replans} duration_s={result.metrics.duration_s:.2f} "
                f"fail_reason={result.metrics.fail_reason}"
            )

        success_rate = successes / max(args.episodes, 1)
        print(f"\nsummary episodes={args.episodes} success_rate={success_rate:.3f} telemetry={args.jsonl}")

        if feed is not None:
            print(f"telemetry feed active at http://127.0.0.1:{args.http_port}/latest")
            if args.episodes == 1:
                print("sleeping 20s so dashboards can inspect latest frame...")
                time.sleep(20)

    finally:
        sink.close()
        camera_provider.release()
        robot.disconnect()
        if feed is not None:
            feed.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
