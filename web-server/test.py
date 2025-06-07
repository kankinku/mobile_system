import requests
import json

BASE = "http://localhost:3000"

# 1. 거리 데이터 전송
distance_payload = {
    "current_distance": 110.5,
    "initial_distance": 100.0,
    "distance_difference": 10.5,
    "elapsed_time": 3.2,
    "source": "test-script"
}

res1 = requests.post(f"{BASE}/api/distance", json=distance_payload)
print("📏 거리 응답:", res1.status_code, res1.json())

# 2. 일정 추가 전송
schedule_payload = {
    "type": "add",
    "data": {
        "title": "회의",
        "time": "2025-06-08 14:00",
        "location": "회의실 A"
    }
}

res2 = requests.post(f"{BASE}/api/voice-result", json=schedule_payload)
print("🗓️ 일정 응답:", res2.status_code, res2.json())

# 3. 서버 상태 확인
res3 = requests.get(f"{BASE}/api/state")
print("\n📊 서버 상태:")
print(json.dumps(res3.json(), indent=2, ensure_ascii=False))
