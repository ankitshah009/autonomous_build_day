"use client";

import { useCallback, useState } from "react";
import { LiveKitRoom, RoomAudioRenderer } from "@livekit/components-react";
import "@livekit/components-styles";

import {
  ConnectionBar,
  type ConnectionConfig,
} from "./components/ConnectionBar";
import { DashboardContent } from "./DashboardContent";

export default function JudgeDashboard() {
  const [token, setToken] = useState("");
  const [livekitUrl, setLivekitUrl] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = useCallback(async (config: ConnectionConfig) => {
    setError(null);
    try {
      const response = await fetch(config.tokenServer, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roomName: config.roomName,
          identity: config.identity,
          canPublish: false,
          canSubscribe: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Token request failed (${response.status})`);
      }

      const data = await response.json();
      setToken(data.token);
      setLivekitUrl(config.livekitUrl);
      setIsConnected(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    }
  }, []);

  const handleDisconnect = useCallback(() => {
    setToken("");
    setLivekitUrl("");
    setIsConnected(false);
    setError(null);
  }, []);

  return (
    <div className="min-h-screen grid-overlay">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-mission-border bg-mission-panel/80 backdrop-blur-md">
        <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-accent shadow-[0_0_10px_rgba(59,130,246,0.6)]" />
            <h1 className="text-lg font-semibold tracking-tight">
              Track-1 Mission Control
            </h1>
            <span className="text-xs text-text-muted font-mono">
              AUTONOMOUS ROBOTICS
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-5 space-y-5">
        {/* Connection Bar */}
        <ConnectionBar
          isConnected={isConnected}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
          error={error}
        />

        {/* Dashboard Grid */}
        {isConnected && token ? (
          <LiveKitRoom
            serverUrl={livekitUrl}
            token={token}
            connect={true}
            onDisconnected={handleDisconnect}
          >
            <RoomAudioRenderer />
            <DashboardContent />
          </LiveKitRoom>
        ) : (
          <div className="panel p-16 text-center">
            <div className="text-4xl mb-4 opacity-20">
              &#x25C9;
            </div>
            <p className="text-text-muted text-lg">
              Connect to LiveKit to view real-time telemetry
            </p>
            <p className="text-text-muted/50 text-sm mt-2">
              Ensure the autonomy runtime, token server, and LiveKit server are
              running
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
