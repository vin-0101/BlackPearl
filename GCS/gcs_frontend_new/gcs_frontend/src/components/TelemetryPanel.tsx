import React from 'react';
import { Telemetry, DroneStatus } from '../types';
import { Navigation, Activity, Battery, Wifi, Gauge } from 'lucide-react';

interface TelemetryPanelProps {
  telemetry: Telemetry;
  droneStatus: DroneStatus;
}
const valueTone = (pct: number) => {
  if (pct >= 70) return 'text-zinc-100';
  if (pct >= 40) return 'text-zinc-300';
  return 'text-zinc-500';
};

export const TelemetryPanel: React.FC<TelemetryPanelProps> = ({ telemetry, droneStatus }) => {
  const statusTone = (s: string) =>
    ['Hovering', 'Moving', 'Ascending', 'Descending', 'Takeoff'].includes(s)
      ? 'text-zinc-200'
      : s === 'Landing'
      ? 'text-zinc-400'
      : 'text-zinc-500';

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 space-y-6">
      <h2 className="text-zinc-100 text-lg font-semibold mb-4 flex items-center">
        <Activity   className="w-5 h-5 mr-2 text-sky-400" />
        <Navigation className="w-4 h-4 mr-2 text-indigo-400" />
        <Gauge      className="w-4 h-4 mr-2 text-cyan-400" />
        <Battery    className="w-4 h-4 mr-2 text-emerald-400" />
        <Wifi       className="w-4 h-4 mr-2 text-sky-400" />

        Telemetry
      </h2>

      {/* Altitude */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-zinc-400 text-sm">Altitude</span>
          <span className="text-zinc-100 font-mono text-lg">{telemetry.altitude.toFixed(1)}m</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-zinc-500 text-xs">LiDAR</span>
          <span className="text-zinc-300 font-mono text-sm">{telemetry.lidarReading.toFixed(1)}m</span>
        </div>
      </div>

      <div className="border-t border-zinc-800 pt-4">
        {/* GPS */}
        <div className="space-y-3">
          <div className="flex items-center mb-2">
            <Navigation className="w-4 h-4 mr-2 text-zinc-400" />
            <span className="text-zinc-400 text-sm">GPS Coordinates</span>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-zinc-500 text-xs">Latitude</span>
              <span className="text-zinc-200 font-mono text-sm">{telemetry.gpsLat.toFixed(6)}°</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500 text-xs">Longitude</span>
              <span className="text-zinc-200 font-mono text-sm">{telemetry.gpsLon.toFixed(6)}°</span>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-zinc-800 pt-4">
        {/* Speed */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Gauge className="w-4 h-4 mr-2 text-zinc-400" />
            <span className="text-zinc-400 text-sm">Speed</span>
          </div>
          <span className="text-zinc-100 font-mono text-lg">{telemetry.speed.toFixed(1)} m/s</span>
        </div>

        {/* Battery */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Battery className="w-4 h-4 mr-2 text-zinc-400" />
            <span className="text-zinc-400 text-sm">Battery</span>
          </div>
          <span className={`font-mono text-lg ${valueTone(telemetry.battery)}`}>
            {telemetry.battery.toFixed(0)}%
          </span>
        </div>

        {/* Signal */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Wifi className="w-4 h-4 mr-2 text-zinc-400" />
            <span className="text-zinc-400 text-sm">Signal</span>
          </div>
          <span className={`font-mono text-lg ${valueTone(telemetry.signalStrength)}`}>
            {telemetry.signalStrength.toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="border-t border-zinc-800 pt-4">
        {/* Status */}
        <div className="flex items-center justify-between">
          <span className="text-zinc-400 text-sm">Status</span>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full bg-gradient-to-b from-white to-zinc-500 opacity-70 ${!droneStatus.isFlying && 'opacity-40'}`}></div>
            <span className={`font-medium ${statusTone(droneStatus.status)}`}>{droneStatus.status}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
