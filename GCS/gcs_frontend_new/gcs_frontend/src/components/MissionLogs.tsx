// MissionLogs.tsx
import React from 'react';


import { AlertCircle, Info, AlertTriangle } from 'lucide-react';
export type LogEntry = {
  id: string;
  type: 'detection' | 'command' | 'telemetry' | 'sys';
  severity: 'info' | 'warning' | 'error';
  message: string;
  timestamp: Date;
};
interface MissionLogsProps { logs: LogEntry[]; }

export const MissionLogs: React.FC<MissionLogsProps> = ({ logs }) => {
    const iconTone = (s: LogEntry['severity']) =>
    s === 'error'   ? 'text-rose-400'
  : s === 'warning' ? 'text-amber-400'
  :                   'text-sky-400';


  const textTone = (s: LogEntry['severity']) =>
    s === 'error' ? 'text-zinc-100' : s === 'warning' ? 'text-zinc-300' : 'text-zinc-400';

  const getTypeLabel = (t: LogEntry['type']) =>
    t === 'detection' ? 'DETECT' : t === 'command' ? 'CMD' : t === 'telemetry' ? 'TELEM' : 'SYS';

  const recent = logs.slice(-5);

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-3">
      <h2 className="text-zinc-100 text-sm font-semibold mb-2">Mission Logs</h2>

      <div className="space-y-1.5">
        {recent.map((log) => (
          <div key={log.id} className="flex items-start space-x-2 text-[12px] leading-tight">
            <div className={`flex-shrink-0 mt-0.5 ${iconTone(log.severity)}`}>
              {log.severity === 'error'   ? <AlertCircle className="w-3.5 h-3.5" />
              : log.severity === 'warning'? <AlertTriangle className="w-3.5 h-3.5" />
              :                             <Info className="w-3.5 h-3.5" />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-1.5">
                <span className="text-zinc-500 font-mono text-[11px]">
                  {log.timestamp.toLocaleTimeString()}
                </span>
                <span className="bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded text-[10px] font-mono">
                  {getTypeLabel(log.type)}
                </span>
              </div>
              <p className={`mt-0.5 ${textTone(log.severity)}`}>{log.message}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-2 pt-2 border-t border-zinc-800 flex justify-between">
        <button className="text-zinc-400 hover:text-zinc-200 text-[11px] transition-colors">Clear Logs</button>
        <button className="text-zinc-400 hover:text-zinc-200 text-[11px] transition-colors">Export Logs</button>
      </div>
    </div>
  );
};
