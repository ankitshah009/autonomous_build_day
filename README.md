# Track-1 Winning Stack (End-to-End)

This repo implements a practical **Track-1 robot autonomy stack** with:
- Closed-loop autonomy: `perceive -> plan -> execute -> verify -> retry -> replan`
- A stochastic `SimRobot` so you can benchmark reliability before hardware
- Trial runner with success-rate metrics
- Judge-facing LiveKit flow:
  - token server
  - robot publisher page (camera + telemetry data channel)
  - judge dashboard page (video + plan/retry/replan panels)

## 1) Python autonomy runtime

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Single demo episode
```bash
python scripts/run_demo.py \
  --seed 7 \
  --goal-target cup \
  --max-retries-step 2 \
  --max-replans 3 \
  --max-ticks 80 \
  --jsonl runs/demo_telemetry.jsonl \
  --http-port 8765
```

Outputs:
- episode summary in terminal
- telemetry stream in `runs/demo_telemetry.jsonl`
- latest telemetry frame at [http://127.0.0.1:8765/latest](http://127.0.0.1:8765/latest)

### Multi-trial reliability run
```bash
python scripts/run_trials.py --trials 20 --seed 42 --csv runs/trials.csv
```

Outputs:
- success rate, avg retries, avg replans
- per-trial CSV in `runs/trials.csv`

## 2) LiveKit token server

The token server mints room JWTs using `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`.

### Setup
```bash
cd services/livekit
npm install
```

### Run
```bash
export LIVEKIT_API_KEY=devkey
export LIVEKIT_API_SECRET=secret
npm run start:token
```

Server endpoint:
- `POST http://127.0.0.1:3000/token`

Request body:
```json
{
  "roomName": "track1-room",
  "identity": "robot-publisher",
  "canPublish": true,
  "canSubscribe": false
}
```

## 3) Start a LiveKit server (local dev)

Use your preferred setup. For local practice, `livekit-server --dev` is the fastest path.

Expected local defaults used by the pages in this repo:
- URL: `ws://127.0.0.1:7880`
- key: `devkey`
- secret: `secret`

## 4) Launch browser pages

Serve the repo root (or `livekit/`) with any static server.

Example:
```bash
python -m http.server 8080
```

Open:
- Robot publisher: [http://127.0.0.1:8080/livekit/robot_publisher.html](http://127.0.0.1:8080/livekit/robot_publisher.html)
- Judge dashboard: [http://127.0.0.1:8080/livekit/judge_dashboard.html](http://127.0.0.1:8080/livekit/judge_dashboard.html)

Robot publisher behavior:
- connects to room
- enables camera + microphone
- polls telemetry from `http://127.0.0.1:8765/latest`
- publishes telemetry on topic `telemetry` at configured rate (default 200ms)

Judge dashboard behavior:
- subscribes to video tracks
- subscribes to telemetry topic
- renders current phase, action, retries/replans, world snapshot, score panels

## Competition-day runbook

1. Start LiveKit server/cloud room.
2. Start token server.
3. Run `scripts/run_demo.py --http-port 8765 --episodes 10`.
4. Open robot publisher page on robot laptop and connect.
5. Open judge dashboard page on judge-facing screen.
6. Trigger randomized trials and narrate:
   - plan progression
   - failures
   - retries
   - replans
   - final success rate

This gives judges visible proof of robust closed-loop autonomy, not just one-off success.

## Repo map

- `autonomy/` core closed-loop runtime
- `scripts/run_demo.py` single/multi-episode demo
- `scripts/run_trials.py` reliability benchmark runner
- `services/livekit/token_server.mjs` JWT minting service
- `livekit/robot_publisher.html` robot-side publisher UI
- `livekit/judge_dashboard.html` judge-facing telemetry/video dashboard
