
import React, { useState, useEffect } from 'react';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, User, Package } from 'lucide-react';

interface Schedule {
  사용기능: string;
  이름: string;
  시간: string;
  목표시간: string;
  준비물: string;
  timestamp: string;
}

const ScheduleManager = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);

  useEffect(() => {
    // 초기 일정 데이터
    const initialSchedule: Schedule = {
      사용기능: '일정 공유',
      이름: '성우',
      시간: '06:00',
      목표시간: '06:00',
      준비물: '없음',
      timestamp: new Date().toISOString()
    };

    setSchedules([initialSchedule]);

    // 새로운 일정 추가 시뮬레이션
    const interval = setInterval(() => {
      const names = ['지민', '하은', '도현', '서연', '준호'];
      const times = ['07:00', '08:30', '09:15', '10:00', '14:30'];
      const items = ['없음', '노트북', '서류', '발표자료', '회의자료'];
      
      const newSchedule: Schedule = {
        사용기능: '일정 공유',
        이름: names[Math.floor(Math.random() * names.length)],
        시간: times[Math.floor(Math.random() * times.length)],
        목표시간: times[Math.floor(Math.random() * times.length)],
        준비물: items[Math.floor(Math.random() * items.length)],
        timestamp: new Date().toISOString()
      };

      setSchedules(prev => [newSchedule, ...prev.slice(0, 4)]);
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (timeString: string) => {
    return timeString;
  };

  const getTimeBadgeVariant = (time: string) => {
    const hour = parseInt(time.split(':')[0]);
    if (hour < 9) return 'default';
    if (hour < 12) return 'secondary';
    return 'outline';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-sm">음성 명령 일정 목록</h4>
        <Badge variant="secondary" className="text-xs">
          총 {schedules.length}개
        </Badge>
      </div>

      <div className="space-y-3 max-h-64 overflow-y-auto">
        {schedules.map((schedule, index) => (
          <div 
            key={index} 
            className="p-3 bg-gradient-to-r from-muted/30 to-muted/10 rounded-lg border border-border/50 hover:shadow-md transition-all duration-200 animate-fade-in"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-primary" />
                <span className="font-medium">{schedule.이름}</span>
              </div>
              <Badge variant={getTimeBadgeVariant(schedule.시간)} className="text-xs">
                {schedule.사용기능}
              </Badge>
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-muted-foreground" />
                <span className="text-muted-foreground">시간:</span>
                <span className="font-mono">{formatTime(schedule.시간)}</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-muted-foreground" />
                <span className="text-muted-foreground">목표:</span>
                <span className="font-mono">{formatTime(schedule.목표시간)}</span>
              </div>
            </div>
            
            <div className="flex items-center gap-1 mt-2 text-sm">
              <Package className="w-3 h-3 text-muted-foreground" />
              <span className="text-muted-foreground">준비물:</span>
              <span className={schedule.준비물 === '없음' ? 'text-muted-foreground' : 'text-foreground font-medium'}>
                {schedule.준비물}
              </span>
            </div>
            
            <div className="text-xs text-muted-foreground mt-2">
              추가됨: {new Date(schedule.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>

      {schedules.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>아직 등록된 일정이 없습니다.</p>
        </div>
      )}
    </div>
  );
};

export default ScheduleManager;