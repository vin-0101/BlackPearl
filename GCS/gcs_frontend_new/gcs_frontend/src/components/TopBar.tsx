  // TopBar.tsx
  // …imports unchanged…
  import React from 'react';


  import { DroneStatus } from '../hooks/useDroneData';

  import {  Settings, User } from 'lucide-react';

  interface TopBarProps {
    droneStatus: DroneStatus;
  }
  export const TopBar: React.FC<TopBarProps> = ({ droneStatus }) => {
    return (
      <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-bold text-zinc-100">Drone GCS</h1>
          <div className="text-zinc-500">|</div>
          <span className="text-zinc-300">Drone ID: DRN-001</span>
        </div>

        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            {droneStatus.isConnected ? (
              <>
                <div className="w-2 h-2 rounded-full bg-gradient-to-b from-white to-zinc-500 opacity-70"></div>
                <span className="text-zinc-300 font-medium">Connected</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-zinc-700"></div>
                <span className="text-zinc-500 font-medium">Disconnected</span>
              </>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button className="p-2 text-zinc-400 hover:bg-zinc-800 rounded-lg transition-colors">
              <Settings className="w-5 h-5 text-sky-400" />
            </button>
            <button className="p-2 text-zinc-400 hover:bg-zinc-800 rounded-lg transition-colors">
              <User className="w-5 h-5 text-indigo-400" />
            </button>

          </div>
        </div>
      </div>
    );
  };
