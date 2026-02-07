#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy import Goal, ObjClass, PerceptionModule, Planner, SimRobot, StepExecutor, Track1Agent
from autonomy.telemetry import InMemorySink, MultiSink


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run randomized Track-1 trials")
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--goal-target", default="cup", choices=[c.value for c in ObjClass])
    parser.add_argument("--max-retries-step", type=int, default=2)
    parser.add_argument("--max-replans", type=int, default=3)
    parser.add_argument("--max-ticks", type=int, default=80)
    parser.add_argument("--csv", default="runs/trials.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    goal = Goal(goal_type="put_in_bin", target_obj_class=ObjClass(args.goal_target))

    planner = Planner()
    perception = PerceptionModule()
    robot = SimRobot(seed=args.seed)
    executor = StepExecutor(planner)

    sink = MultiSink([InMemorySink()])
    agent = Track1Agent(
        robot=robot,
        planner=planner,
        perception=perception,
        executor=executor,
        sink=sink,
        max_retries_per_step=args.max_retries_step,
        max_replans=args.max_replans,
    )

    rows = []
    successes = 0
    total_retries = 0
    total_replans = 0

    for i in range(args.trials):
        robot.reset(seed=args.seed + i)
        result = agent.run_episode(goal=goal, max_ticks=args.max_ticks)
        m = result.metrics
        successes += int(m.success)
        total_retries += m.retries
        total_replans += m.replans
        rows.append(
            {
                "trial": i + 1,
                "seed": args.seed + i,
                "success": int(m.success),
                "steps_executed": m.steps_executed,
                "retries": m.retries,
                "replans": m.replans,
                "duration_s": round(m.duration_s, 3),
                "fail_reason": m.fail_reason or "",
            }
        )

    out = Path(args.csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    success_rate = successes / max(args.trials, 1)
    print(f"trials={args.trials}")
    print(f"success_rate={success_rate:.3f}")
    print(f"avg_retries={total_retries / max(args.trials, 1):.2f}")
    print(f"avg_replans={total_replans / max(args.trials, 1):.2f}")
    print(f"csv={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
