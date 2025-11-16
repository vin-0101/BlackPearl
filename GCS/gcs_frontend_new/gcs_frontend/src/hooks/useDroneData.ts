// src/hooks/useDroneData.ts
import { useCallback, useMemo, useState } from 'react';
import { DroneStatus, Telemetry, VideoFeedData, LogEntry } from '../types';

export function useDroneData() {
  const [droneStatus] = useState<DroneStatus>({
    armed: false,
    mode: 'Manual',
    isConnected: false,
    isFlying: false,
    status: 'Idle',
  });

  const [telemetry] = useState<Telemetry>({
    altitude: 0,
    lidarReading: 0,
    gpsLat: 0,
    gpsLon: 0,
    gpsSat: 0,
    gpsFix: false,
    speed: 0,
    battery: 100,
    signalStrength: 100,
  });

  const [videoFeed] = useState<VideoFeedData>({
    url: 'http://localhost:8000/video_feed',
  });

  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = useCallback((entry: Omit<LogEntry, 'id'>) => {
    setLogs((prev) => [
      ...prev,
      {
        id: (Date.now() + Math.floor(Math.random() * 1000)).toString(),
        ...entry,
      },
    ]);
  }, []);

  const clearLogs = useCallback(() => setLogs([]), []);

  const executeCommand = useCallback(async (cmd: string) => {
    addLog({
      type: 'command',
      severity: 'info',
      message: `Executed command: ${cmd}`,
      timestamp: new Date(),
    });
    return { ok: true };
  }, [addLog]);

  return useMemo(
    () => ({
      droneStatus,
      telemetry,
      videoFeed,
      logs,
      addLog,
      clearLogs,
      executeCommand,
    }),
    [droneStatus, telemetry, videoFeed, logs, addLog, clearLogs, executeCommand]
  );
}
