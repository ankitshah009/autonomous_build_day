"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RoomEvent } from "livekit-client";
import { useRoomContext } from "@livekit/components-react";
import type { TelemetryData } from "../types";

/**
 * Subscribes to the "telemetry" data channel in the current LiveKit room
 * and returns the latest parsed TelemetryData frame.
 */
export function useTelemetry(): TelemetryData | null {
  const room = useRoomContext();
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const decoder = useRef(new TextDecoder());

  const handleData = useCallback(
    (
      payload: Uint8Array,
      _participant: unknown,
      _kind: unknown,
      topic?: string,
    ) => {
      if (topic !== "telemetry") return;
      try {
        const parsed: TelemetryData = JSON.parse(
          decoder.current.decode(payload),
        );
        setTelemetry(parsed);
      } catch {
        // Ignore malformed telemetry packets.
      }
    },
    [],
  );

  useEffect(() => {
    room.on(RoomEvent.DataReceived, handleData);
    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [room, handleData]);

  return telemetry;
}
