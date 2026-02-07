# Track-1 Winning Stack (End-to-End)

Full-stack autonomy for the Track-1 robot competition — from perception to execution, with a polished judge-facing dashboard and support for simulation, real hardware (SO-ARM100), and neural policies (ACT / GR00T N1.6).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMY RUNTIME                         │
│                                                             │
│  PerceptionProvider ──► PerceptionModule ──► Planner        │
│  (Sim / Camera+YOLO)     (temporal smooth)    (symbolic)    │
│                                                ↓            │
│  PolicyRouter ◄── ACT / GR00T / Symbolic ──► Executor       │
│       ↓                                        ↓            │
│  RobotInterface ◄── SimRobot / LeRobotAdapter               │
│       ↓                                                     │
│  TelemetrySink ──► HTTP Feed ──► robot_publisher.html        │
│                                        ↓                    │
│                                   LiveKit Room              │
│                                        ↓                    │
│                              Next.js Dashboard              │
└─────────────────────────────────────────────────────────────┘
```

**Closed-loop**: `perceive → plan → execute → verify → retry → replan`

## Quick Start (Simulation)

```bash
# 1) Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) Token server
cd services/livekit && npm install && cd ../..
export LIVEKIT_API_KEY=API4DMWY4jSEmer
export LIVEKIT_API_SECRET=JWbzTgL0ZuIycEG30kRvyVa0ohF5mH8GOtKBinblxhN
cd services/livekit && npm run start:token &
cd ../..

# 3) Autonomy runtime (with telemetry feed)
python scripts/run_demo.py --http-port 8765 --episodes 5 --verbose

# 4) Robot publisher (open in browser)
python3 -m http.server 8080 &
# Open http://127.0.0.1:8080/livekit/robot_publisher.html

# 5) Judge dashboard
cd web && npm install && npm run dev
# Open http://127.0.0.1:3000
```

Or use the all-in-one launcher:

```bash
./scripts/start_competition.sh simulation 5
```

## Run Modes

| Mode | Command | What it does |
|------|---------|--------------|
| Simulation | `./scripts/start_competition.sh simulation 5` | SimRobot + symbolic planner |
| Real (symbolic) | `./scripts/start_competition.sh real 3` | SO-ARM100 + symbolic planner |
| Real (ACT) | `./scripts/start_competition.sh act 3` | SO-ARM100 + LeRobot ACT policy |
| Real (GR00T) | `./scripts/start_competition.sh groot 1` | SO-ARM100 + GR00T N1.6 inference |

## Judge Dashboard

Mission control themed Next.js 16 app with real-time LiveKit integration.

**Panels:**
- **Video Feed** — live camera stream from the robot
- **Status Panel** — current phase, action, retries, errors
- **Plan Timeline** — step-by-step progress with checkmarks
- **Scoreboard** — success rate, retries, replans, duration
- **Robot State Gauges** — battery, temperature, gripper, joints
- **World Snapshot** — detected objects with confidence bars

```bash
cd web && npm run dev     # Development at http://localhost:3000
cd web && npm run build   # Production build
```

Environment variables (set in `web/.env.local`):
```
NEXT_PUBLIC_LIVEKIT_URL=ws://127.0.0.1:7880
NEXT_PUBLIC_TOKEN_SERVER=http://127.0.0.1:3000/token
NEXT_PUBLIC_ROOM_NAME=track1-room
```

## Real Hardware (SO-ARM100)

### Direct runner

```bash
python scripts/run_real_robot.py \
  --policy symbolic \
  --robot-port /dev/ttyACM0 \
  --camera-wrist 0 \
  --camera-front 2 \
  --http-port 8765 \
  --episodes 3
```

### Policy options

```bash
# ACT policy (requires trained checkpoint)
python scripts/run_real_robot.py --policy act --checkpoint checkpoints/act_so100

# GR00T N1.6 (requires running inference server)
python scripts/run_real_robot.py --policy groot --groot-server localhost:5555
```

## GR00T N1.6 Pipeline

End-to-end workflow from data collection to deployment:

### 1. Collect teleoperation data

```bash
./scripts/groot/collect_data.sh \
  --port /dev/ttyACM0 \
  --dataset my_task_data \
  --episodes 50 \
  --task "pick up the cup and place it in the bin"
```

### 2. Prepare dataset for GR00T

```bash
python scripts/groot/prepare_data.py \
  --dataset-path data/my_task_data \
  --embodiment so100
```

### 3. Fine-tune GR00T N1.6

```bash
./scripts/groot/finetune.sh \
  --dataset data/my_task_data \
  --output checkpoints/groot_so100 \
  --steps 10000
```

### 4. Deploy

```bash
# Start inference server + robot client
./scripts/groot/deploy.sh both \
  --checkpoint checkpoints/groot_so100 \
  --port /dev/ttyACM0 \
  --task "pick up the cup and place it in the bin"
```

## Simulation Demo

### Single episode

```bash
python scripts/run_demo.py \
  --seed 7 \
  --goal-target cup \
  --max-retries-step 2 \
  --max-replans 3 \
  --http-port 8765
```

### Multi-trial reliability benchmark

```bash
python scripts/run_trials.py --trials 20 --seed 42 --csv runs/trials.csv
```

## Token Server

Mints LiveKit room JWTs.

```bash
cd services/livekit && npm install
export LIVEKIT_API_KEY=API4DMWY4jSEmer
export LIVEKIT_API_SECRET=JWbzTgL0ZuIycEG30kRvyVa0ohF5mH8GOtKBinblxhN
npm run start:token
```

Endpoint: `POST http://127.0.0.1:3000/token`

## Competition Day Checklist

1. **Verify hardware**: SO-ARM100 powered, USB connected, cameras visible
2. **Start LiveKit**: local `livekit-server --dev` or cloud instance
3. **Launch stack**: `./scripts/start_competition.sh <mode> <episodes>`
4. **Open robot publisher**: connect camera + telemetry to LiveKit room
5. **Open judge dashboard**: show on judge-facing display
6. **Run episodes**: demonstrate closed-loop autonomy with retries/replans
7. **Narrate**: explain plan progression, failure handling, success rate

## Repo Map

```
autonomy/                     Core closed-loop runtime
├── agent.py                  Track1Agent episode runner
├── planner.py                Symbolic plan builder
├── perception.py             Temporal-smoothed perception
├── perception_providers.py   Pluggable perception backends (Sim/Camera/YOLO)
├── executor.py               Step executor → robot actions
├── sim_robot.py              Stochastic simulation robot
├── robot_interface.py        Protocol for swappable robot backends
├── lerobot_adapter.py        SO-ARM100 via LeRobot SDK
├── policy_router.py          ACT / GR00T / Symbolic policy routing
├── groot_client.py           GR00T N1.6 inference client
├── telemetry.py              Telemetry sinks (JSONL, UDP, stdout, multi)
├── telemetry_http.py         HTTP telemetry feed server
└── types.py                  Core data types

web/                          Next.js 16 judge dashboard
├── app/
│   ├── page.tsx              Main dashboard with LiveKit connection
│   ├── DashboardContent.tsx  Dashboard grid layout
│   ├── types.ts              TypeScript telemetry types
│   ├── globals.css           Mission control dark theme
│   ├── hooks/
│   │   └── useTelemetry.ts   LiveKit data channel subscription
│   └── components/
│       ├── ConnectionBar.tsx  LiveKit connection controls
│       ├── VideoFeed.tsx      Live video from robot
│       ├── StatusPanel.tsx    Phase / action / errors
│       ├── PlanTimeline.tsx   Step progress visualization
│       ├── Scoreboard.tsx     Success metrics
│       ├── RobotStateGauges.tsx  Battery / temp / joints
│       └── WorldSnapshot.tsx  Detected objects list
└── .env.local                LiveKit connection config

scripts/
├── run_demo.py               Simulation demo runner
├── run_trials.py             Reliability benchmark
├── run_real_robot.py         Real hardware runner (all policies)
├── start_competition.sh      All-in-one competition launcher
└── groot/
    ├── collect_data.sh       Teleoperation data collection
    ├── prepare_data.py       Dataset preparation for GR00T
    ├── finetune.sh           GR00T N1.6 fine-tuning
    └── deploy.sh             GR00T deployment (server + client)

services/livekit/
├── token_server.mjs          JWT minting server
└── package.json

livekit/
├── robot_publisher.html      Robot-side LiveKit publisher
└── judge_dashboard.html      Legacy HTML dashboard
```
