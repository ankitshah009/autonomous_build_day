"use client";

import { useState } from "react";

interface ConnectionBarProps {
  isConnected: boolean;
  onConnect: (config: ConnectionConfig) => void;
  onDisconnect: () => void;
  error?: string | null;
}

export interface ConnectionConfig {
  livekitUrl: string;
  tokenServer: string;
  roomName: string;
  identity: string;
}

export function ConnectionBar({
  isConnected,
  onConnect,
  onDisconnect,
  error,
}: ConnectionBarProps) {
  const [livekitUrl, setLivekitUrl] = useState(
    process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://127.0.0.1:7880"
  );
  const [tokenServer, setTokenServer] = useState(
    process.env.NEXT_PUBLIC_TOKEN_SERVER || "http://127.0.0.1:3001/token"
  );
  const [roomName, setRoomName] = useState(
    process.env.NEXT_PUBLIC_ROOM_NAME || "track1-room"
  );
  const [identity] = useState("judge-dashboard");

  return (
    <div className="panel px-5 py-3">
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className={`status-dot ${isConnected ? "status-dot-ok" : "status-dot-warn"}`}
          />
          <span className="text-sm font-medium">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>

        {!isConnected && (
          <>
            <label className="flex flex-col gap-1 text-[10px] text-text-muted uppercase tracking-wider">
              LiveKit URL
              <input
                value={livekitUrl}
                onChange={(e) => setLivekitUrl(e.target.value)}
                className="bg-white/5 border border-mission-border rounded px-2 py-1.5 text-sm text-text-primary font-mono w-52"
              />
            </label>
            <label className="flex flex-col gap-1 text-[10px] text-text-muted uppercase tracking-wider">
              Token Server
              <input
                value={tokenServer}
                onChange={(e) => setTokenServer(e.target.value)}
                className="bg-white/5 border border-mission-border rounded px-2 py-1.5 text-sm text-text-primary font-mono w-60"
              />
            </label>
            <label className="flex flex-col gap-1 text-[10px] text-text-muted uppercase tracking-wider">
              Room
              <input
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                className="bg-white/5 border border-mission-border rounded px-2 py-1.5 text-sm text-text-primary font-mono w-32"
              />
            </label>
          </>
        )}

        <div className="flex-1" />

        {isConnected ? (
          <button
            onClick={onDisconnect}
            className="px-4 py-1.5 text-sm rounded-lg bg-white/5 hover:bg-white/10 text-text-muted transition-colors cursor-pointer"
          >
            Disconnect
          </button>
        ) : (
          <button
            onClick={() =>
              onConnect({ livekitUrl, tokenServer, roomName, identity })
            }
            className="px-5 py-1.5 text-sm rounded-lg bg-accent hover:bg-accent/80 text-white font-medium transition-colors cursor-pointer"
          >
            Connect
          </button>
        )}
      </div>

      {error && (
        <div className="mt-2 text-xs text-error font-mono">{error}</div>
      )}
    </div>
  );
}
