
import React, { useState, useEffect } from 'react';
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface LogEntry {
  timestamp: string;
  ip: string;
  method: string;
  endpoint: string;
  status: number;
  type: 'web' | 'distance' | 'voice' | 'schedule';
  message?: string;
}

const ServerLogs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    // 초기 로그 데이터
    const initialLogs: LogEntry[] = [
      {
        timestamp: '00:04:03',
        ip: '192.168.0.152',
        method: 'POST',
        endpoint: '/api/distance',
        status: 200,
        type: 'distance',
        message: '거리 측정 결과 수신: 현재 거리 18.77px'
      },
      {
        timestamp: '00:10:49',
        ip: '192.168.0.147',
        method: 'POST',
        endpoint: '/api',
        status: 404,
        type: 'web'
      },
      {
        timestamp: '00:11:20',
        ip: '192.168.0.147',
        method: 'POST',
        endpoint: '/api',
        status: 404,
        type: 'web'
      },
      {
        timestamp: '00:17:20',
        ip: '192.168.0.147',
        method: 'POST',
        endpoint: '/api/voice-result',
        status: 200,
        type: 'voice',
        message: '일정 추가 수신: 성우, 06:00'
      }
    ];

    setLogs(initialLogs);

    // 실시간 로그 생성 시뮬레이션
    const interval = setInterval(() => {
      const logTypes = [
        { type: 'distance' as const, endpoint: '/api/distance', message: '거리 측정 데이터 수신' },
        { type: 'voice' as const, endpoint: '/api/voice-result', message: '음성 명령 처리 완료' },
        { type: 'web' as const, endpoint: '/api/status', message: '시스템 상태 확인' },
        { type: 'schedule' as const, endpoint: '/api/schedule', message: '일정 데이터 업데이트' }
      ];

      const randomLog = logTypes[Math.floor(Math.random() * logTypes.length)];
      const randomStatus = Math.random() > 0.15 ? 200 : (Math.random() > 0.5 ? 404 : 500);
      const randomIp = `192.168.0.${Math.floor(Math.random() * 255)}`;

      const newLog: LogEntry = {
        timestamp: new Date().toLocaleTimeString(),
        ip: randomIp,
        method: 'POST',
        endpoint: randomLog.endpoint,
        status: randomStatus,
        type: randomLog.type,
        message: randomStatus === 200 ? randomLog.message : undefined
      };

      setLogs(prev => [newLog, ...prev.slice(0, 19)]);
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'default';
    if (status >= 400 && status < 500) return 'secondary';
    return 'destructive';
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'distance': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'voice': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'schedule': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-sm">실시간 서버 로그</h4>
        <Badge variant="outline" className="text-xs">
          {logs.length}개 항목
        </Badge>
      </div>

      <ScrollArea className="h-64">
        <div className="space-y-2">
          {logs.map((log, index) => (
            <div 
              key={index} 
              className="p-3 bg-muted/20 rounded-lg border border-border/30 hover:bg-muted/40 transition-colors duration-200 animate-fade-in"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Badge variant={getStatusColor(log.status)} className="text-xs font-mono">
                    {log.status}
                  </Badge>
                  <span className={`text-xs px-2 py-1 rounded ${getTypeColor(log.type)}`}>
                    {log.type}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground font-mono">
                  {log.timestamp}
                </span>
              </div>
              
              <div className="text-sm font-mono text-muted-foreground mb-1">
                {log.ip} - {log.method} {log.endpoint}
              </div>
              
              {log.message && (
                <div className="text-sm text-foreground bg-background/50 p-2 rounded border-l-2 border-primary">
                  {log.message}
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {logs.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <div className="w-8 h-8 mx-auto mb-2 opacity-50">📊</div>
          <p>로그 데이터를 수집 중입니다...</p>
        </div>
      )}
    </div>
  );
};

export default ServerLogs;
