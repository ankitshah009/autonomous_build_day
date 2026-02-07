# LiveKit Services

## Token server

```bash
cd services/livekit
npm install
export LIVEKIT_API_KEY=devkey
export LIVEKIT_API_SECRET=secret
npm run start:token
```

Health check:
```bash
curl http://127.0.0.1:3000/health
```

Token request:
```bash
curl -X POST http://127.0.0.1:3000/token \
  -H 'content-type: application/json' \
  -d '{"roomName":"track1-room","identity":"judge-dashboard","canPublish":false,"canSubscribe":true}'
```
