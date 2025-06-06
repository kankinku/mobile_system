
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Badge } from "@/components/ui/badge";

interface DistanceData {
  time: string;
  current: number;
  initial: number;
  difference: number;
  elapsed: number;
}

const DistanceMonitor = () => {
  const [distanceData, setDistanceData] = useState<DistanceData[]>([]);
  const [currentDistance, setCurrentDistance] = useState(18.77);
  const [status, setStatus] = useState<'stable' | 'changing'>('stable');

  // 시뮬레이션 데이터 생성
  useEffect(() => {
    const generateMockData = () => {
      const now = new Date();
      const mockData: DistanceData[] = [];
      
      for (let i = 0; i < 20; i++) {
        const time = new Date(now.getTime() - (19 - i) * 60000).toLocaleTimeString();
        const current = 18.77 + (Math.random() - 0.5) * 2;
        mockData.push({
          time,
          current,
          initial: 18.77,
          difference: current - 18.77,
          elapsed: i * 60
        });
      }
      
      setDistanceData(mockData);
    };

    generateMockData();
    
    // 실시간 업데이트 시뮬레이션
    const interval = setInterval(() => {
      const newDistance = 18.77 + (Math.random() - 0.5) * 3;
      setCurrentDistance(newDistance);
      setStatus(Math.abs(newDistance - 18.77) > 0.5 ? 'changing' : 'stable');
      
      setDistanceData(prev => {
        const newData = [...prev.slice(1)];
        newData.push({
          time: new Date().toLocaleTimeString(),
          current: newDistance,
          initial: 18.77,
          difference: newDistance - 18.77,
          elapsed: prev.length * 60
        });
        return newData;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      {/* 현재 상태 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-4 bg-muted/50 rounded-lg">
          <div className="text-2xl font-bold text-primary">{currentDistance.toFixed(2)}px</div>
          <div className="text-sm text-muted-foreground">현재 거리</div>
        </div>
        <div className="text-center p-4 bg-muted/50 rounded-lg">
          <Badge variant={status === 'stable' ? 'default' : 'destructive'} className="mb-2">
            {status === 'stable' ? '안정' : '변화'}
          </Badge>
          <div className="text-sm text-muted-foreground">센서 상태</div>
        </div>
      </div>

      {/* 차트 */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={distanceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              labelStyle={{ color: 'hsl(var(--foreground))' }}
              contentStyle={{ 
                backgroundColor: 'hsl(var(--background))', 
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="current" 
              stroke="hsl(var(--primary))" 
              strokeWidth={2}
              dot={{ fill: 'hsl(var(--primary))', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: 'hsl(var(--primary))', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DistanceMonitor;