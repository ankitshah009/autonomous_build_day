import cors from "cors";
import express from "express";
import { AccessToken } from "livekit-server-sdk";

const app = express();
app.use(cors());
app.use(express.json());

const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;
const PORT = Number(process.env.PORT || 3000);

if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
  console.error("Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET");
  process.exit(1);
}

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.post("/token", async (req, res) => {
  const { roomName, identity, canPublish = true, canSubscribe = true } = req.body || {};
  if (!roomName || !identity) {
    res.status(400).json({ error: "roomName and identity are required" });
    return;
  }

  const token = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, { identity });
  token.addGrant({
    roomJoin: true,
    room: roomName,
    canPublish,
    canSubscribe,
    canPublishData: true,
  });

  const jwt = await token.toJwt();
  res.json({ token: jwt });
});

app.listen(PORT, () => {
  console.log(`token server listening on :${PORT}`);
});
