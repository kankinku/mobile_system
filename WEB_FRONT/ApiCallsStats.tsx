
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Badge } from "@/components/ui/badge";

interface ApiCall {
  endpoint: string;
  status: number;
  method: string;
  time: string;
  ip: string;
}

interface ApiStats {
  endpoint: string;
  total: number;
  success: number;
  error: number;
  successRate: number;
}

const ApiCallsStats = () => {
  const [apiCalls, setApiCalls] = useState<ApiCall[]>([]);
  const [apiStats, setApiStats] = useState<ApiStats[]>([]);

  useEffect(() => {
    // 초기 데이터 설정
    const mockCalls: ApiCall[] = [
      { endpoint: '/api/distance', status: 200, method: 'POST', time: '00:04:03', ip: '192.168.0.152' },
      { endpoint: '/api', status: 404, method: 'POST', time: '00:10:49', ip: '192.168.0.147' },
      { endpoint: '/api', status: 404, method: 'POST', time: '00:11:20', ip: '192.168.0.147' },
      { endpoint: '/api/voice-result', status: 200, method: 'POST', time: '00:17:20', ip: '192.168.0.147' }
    ];

    setApiCalls(mockCalls);

    // 통계 계산
    const statsMap = new Map<string, { total: number; success: number; error: number }>();
    
    mockCalls.forEach(call => {
      const endpoint = call.endpoint;
      if (!statsMap.has(endpoint)) {
        statsMap.set(endpoint, { total: 0, success: 0, error: 0 });
      }
      
      const stat = statsMap.get(endpoint)!;
      stat.total++;
      if (call.status >= 200 && call.status < 300) {
        stat.success++;
      } else {
        stat.error++;
      }
    });

    const stats: ApiStats[] = Array.from(statsMap.entries()).map(([endpoint, stat]) => ({
      endpoint: endpoint.replace('/api/', '').replace('/api', 'root') || 'root',
      total: stat.total,
      success: stat.success,
      error: stat.error,
      successRate: Math.round((stat.success / stat.total) * 100)
    }));

    setApiStats(stats);

    // 실시간 업데이트 시뮬레이션
    const interval = setInterval(() => {
      const endpoints = ['/api/distance', '/api/voice-result', '/api/schedule'];
      const randomEndpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
      const randomStatus = Math.random() > 0.8 ? 404 : 200;
      const randomIp = `192.168.0.${Math.floor(Math.random() * 255)}`;
      
      const newCall: ApiCall = {
        endpoint: randomEndpoint,
        status: randomStatus,
        method: 'POST',
        time: new Date().toLocaleTimeString(),
        ip: randomIp
      };

      setApiCalls(prev => [...prev.slice(-9), newCall]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'hsl(var(--chart-2))';
    if (status >= 400) return 'hsl(var(--destructive))';
    return 'hsl(var(--muted))';
  };

  return (
    <div className="space-y-4">
      {/* 최근 API 호출 */}
      <div className="space-y-2">
        <h4 className="font-semibold text-sm">최근 API 호출</h4>
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {apiCalls.slice(-5).reverse().map((call, index) => (
            <div key={index} className="flex items-center justify-between text-sm p-2 bg-muted/30 rounded">
              <div className="flex items-center gap-2">
                <Badge 
                  variant={call.status >= 200 && call.status < 300 ? 'default' : 'destructive'}
                  className="text-xs"
                >
                  {call.status}
                </Badge>
                <span className="font-mono">{call.endpoint}</span>
              </div>
              <div className="text-muted-foreground text-xs">
                {call.time} - {call.ip}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 엔드포인트별 통계 차트 */}
      <div className="h-48">
        <h4 className="font-semibold text-sm mb-2">엔드포인트별 성공률</h4>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={apiStats}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="endpoint" 
              tick={{ fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--background))', 
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px'
              }}
            />
            <Bar dataKey="success" fill="hsl(var(--chart-2))" name="성공" />
            <Bar dataKey="error" fill="hsl(var(--destructive))" name="실패" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ApiCallsStats;