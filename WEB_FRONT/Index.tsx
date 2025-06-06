
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import DistanceMonitor from "@/components/DistanceMonitor";
import ApiCallsStats from "@/components/ApiCallsStats";
import ScheduleManager from "@/components/ScheduleManager";
import ServerLogs from "@/components/ServerLogs";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2 animate-fade-in">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            IoT 모니터링 대시보드
          </h1>
          <p className="text-muted-foreground text-lg">실시간 센서 데이터 및 시스템 상태 모니터링</p>
        </div>

        {/* Top Row - Distance and API Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="animate-scale-in hover-scale">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                거리 센서 모니터링
              </CardTitle>
              <CardDescription>Raspberry Pi에서 실시간 거리 측정 데이터</CardDescription>
            </CardHeader>
            <CardContent>
              <DistanceMonitor />
            </CardContent>
          </Card>

          <Card className="animate-scale-in hover-scale">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                API 호출 통계
              </CardTitle>
              <CardDescription>웹서버 API 엔드포인트 상태 및 통계</CardDescription>
            </CardHeader>
            <CardContent>
              <ApiCallsStats />
            </CardContent>
          </Card>
        </div>

        {/* Bottom Row - Schedule and Logs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="animate-scale-in hover-scale">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse"></div>
                일정 관리
              </CardTitle>
              <CardDescription>음성 명령으로 추가된 일정 목록</CardDescription>
            </CardHeader>
            <CardContent>
              <ScheduleManager />
            </CardContent>
          </Card>

          <Card className="animate-scale-in hover-scale">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="w-3 h-3 bg-orange-500 rounded-full animate-pulse"></div>
                서버 로그
              </CardTitle>
              <CardDescription>실시간 웹서버 로그 및 상태</CardDescription>
            </CardHeader>
            <CardContent>
              <ServerLogs />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Index;