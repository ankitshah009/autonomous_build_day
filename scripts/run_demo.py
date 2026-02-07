#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy import Goal, ObjClass, PerceptionModule, Planner, SimRobot, StepExecutor, Track1Agent
from autonomy.telemetry import InMemorySink, JsonlSink, MultiSink, StdoutSink, UdpSink
from autonomy.telemetry_http import TelemetryHttpFeed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Track-1 closed-loop autonomy demo")
    parser.add_argument("--seed", type=int, default=7, help="Base random seed")
    parser.add_argument("--goal-target", default="cup", choices=[c.value for c in ObjClass], help="Target object class")
    parser.add_argument("--max-retries-step", type=int, default=2)
    parser.add_argument("--max-replans", type=int, default=3)
    parser.add_argument("--max-ticks", type=int, default=80)
    parser.add_argument("--jsonl", default="runs/demo_telemetry.jsonl", help="Path for telemetry JSONL")
    parser.add_argument("--http-port", type=int, default=0, help="Serve telemetry feed on this port (0 disables)")
    parser.add_argument("--udp", default="", help="Optional UDP host:port sink for bridge processes")
    parser.add_argument("--episodes", type=int, default=1, help="Number of episodes to run")
    parser.add_argument("--verbose", action="store_true", help="Print compact telemetry frames")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    target_class = ObjClass(args.goal_target)
    goal = Goal(goal_type="put_in_bin", target_obj_class=target_class)

    jsonl_sink = JsonlSink(args.jsonl)
    memory_sink = InMemorySink()
    sinks: List[object] = [jsonl_sink, memory_sink]

    if args.verbose:
        sinks.append(StdoutSink())

    if args.udp:
        host, port = args.udp.split(":", maxsplit=1)
        sinks.append(UdpSink(host=host, port=int(port)))

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
            print(f"warning: telemetry feed disabled (could not bind port {args.http_port}: {exc})")
            feed = None

    sink = MultiSink(sinks)

    planner = Planner()
    perception = PerceptionModule()
    robot = SimRobot(seed=args.seed)
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

    successes = 0
    try:
        for idx in range(args.episodes):
            if idx > 0:
                robot.reset(seed=args.seed + idx)

            result = agent.run_episode(goal=goal, max_ticks=args.max_ticks)
            if result.metrics.success:
                successes += 1

            print(
                (
                    f"episode={idx + 1} success={result.metrics.success} "
                    f"steps={result.metrics.steps_executed} retries={result.metrics.retries} "
                    f"replans={result.metrics.replans} duration_s={result.metrics.duration_s:.2f} "
                    f"fail_reason={result.metrics.fail_reason}"
                )
            )

        success_rate = successes / max(args.episodes, 1)
        print(f"summary episodes={args.episodes} success_rate={success_rate:.3f} telemetry={args.jsonl}")

        if feed is not None:
            print(f"telemetry feed active at http://127.0.0.1:{args.http_port}/latest")
            if args.episodes == 1:
                print("sleeping 20s so dashboards can inspect latest frame...")
                time.sleep(20)

    finally:
        sink.close()
        if feed is not None:
            feed.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
