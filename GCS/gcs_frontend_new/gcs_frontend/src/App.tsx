// App.tsx
import React from 'react';
import { TopBar } from './components/TopBar';
import { VideoFeed } from './components/VideoFeed';
import { TelemetryPanel } from './components/TelemetryPanel';
import { MissionLogs } from './components/MissionLogs';
import { useDroneData } from './hooks/useDroneData';

function App() {
  const {
    droneStatus,
    telemetry,
    videoFeed,
    logs,
    executeCommand,
  } = useDroneData();

  return (
    <div className="h-screen bg-zinc-950 text-white flex flex-col">
      <TopBar droneStatus={droneStatus} />

      <div className="p-6 flex-1">
        <div className="grid h-full grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left: Telemetry */}
          <div className="lg:col-span-1 min-h-0 overflow-auto">
            <TelemetryPanel telemetry={telemetry} droneStatus={droneStatus} />
          </div>

          {/* Center: Video */}
          <div className="lg:col-span-2 min-h-0 overflow-hidden">
            <VideoFeed  />
          </div>

          {/* Right: Control panel + compact logs */}
          <div className="lg:col-span-1 min-h-0 flex flex-col gap-4">
            {/* Compact logs, no internal scroll */}
            <div className="shrink-0">
              <MissionLogs logs={logs} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
