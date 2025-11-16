

export interface Detection {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
}


// src/types/index.ts

export type DroneStatus = {
  armed: boolean;
  mode: 'Manual' | 'Semi-Auto' | 'Full Auto';
  isConnected: boolean;
  isFlying: boolean;
  status: string;
};

export type Telemetry = {
  altitude: number;
  lidarReading: number;
  gpsLat: number;
  gpsLon: number;
  gpsSat: number;
  gpsFix: boolean;
  speed: number;
  battery: number;
  signalStrength: number;
};

export type VideoFeedData = {
  url?: string;
};

export type LogEntry = {
  id: string;
  type: 'detection' | 'command' | 'telemetry' | 'sys';
  severity: 'info' | 'warning' | 'error';
  message: string;
  timestamp: Date;
};

