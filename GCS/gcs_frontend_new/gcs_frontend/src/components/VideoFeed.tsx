// src/components/VideoFeed.tsx
import React, { useEffect } from 'react';
import { useDroneData } from '../hooks/useDroneData';

export const VideoFeed: React.FC = () => {
  const { addLog } = useDroneData();

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch('http://localhost:8000/logs');
        const data = await res.json();

        data.forEach((entry: any) => {
          const msg = entry.message || '';
          addLog({
            type: msg.includes('BLIP')
              ? 'detection'
              : msg.includes('YOLO')
              ? 'detection'
              : 'sys',
            severity: msg.toLowerCase().includes('error')
              ? 'error'
              : 'info',
            message: msg,
            timestamp: new Date(entry.timestamp * 1000),
          });
        });
      } catch (err) {
        console.error('Error fetching logs', err);
      }
    };

    const interval = setInterval(fetchLogs, 1000);
    return () => clearInterval(interval);
  }, [addLog]);

  return (
    <div className="w-full h-full flex justify-center items-center bg-black">
      <img
        src="http://localhost:8000/video_feed"
        alt="YOLO + BLIP Stream"
        style={{ maxWidth: '100%', maxHeight: '100%' }}
      />
    </div>
  );
};


export default VideoFeed;
