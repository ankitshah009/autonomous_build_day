"use client";

import {
  useTracks,
  VideoTrack,
} from "@livekit/components-react";
import { Track } from "livekit-client";

export function VideoFeed() {
  const tracks = useTracks([Track.Source.Camera], { onlySubscribed: true });

  if (tracks.length === 0) {
    return (
      <div className="panel p-5">
        <div className="panel-header">Camera Feed</div>
        <div className="aspect-video bg-black/60 rounded-lg flex items-center justify-center border border-mission-border">
          <div className="text-center">
            <div className="text-text-muted text-sm">
              Waiting for video stream...
            </div>
            <div className="text-text-muted/50 text-xs mt-1">
              Robot publisher must be connected
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="panel p-5">
      <div className="panel-header flex items-center gap-2">
        Camera Feed
        <span className="status-dot status-dot-ok" />
      </div>
      <div className="video-container space-y-3">
        {tracks.map((trackRef) => (
          <VideoTrack
            key={trackRef.publication?.trackSid}
            trackRef={trackRef}
          />
        ))}
      </div>
    </div>
  );
}
