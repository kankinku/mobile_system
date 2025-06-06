from flask import Flask, request, jsonify, send_from_directory
import time
import os

app = Flask(__name__, static_folder='WEB_STATIC', static_url_path='')

# 최근 데이터 저장용 간단한 메모리 버퍼
distance_state = {}
api_log = []
schedule_list = []
server_log = []

def log_api(endpoint, status=200):
    """API 호출 내역 기록"""
    api_log.append({'endpoint': endpoint, 'status': status, 'timestamp': time.time()})
    if len(api_log) > 20:
        del api_log[0]


@app.route('/api/state', methods=['GET'])
def state():
    """현재 저장된 데이터 반환"""
    return jsonify({
        'distance': distance_state,
        'api_log': api_log,
        'schedule': schedule_list,
        'logs': server_log
    })


@app.route('/')
def root():
    """정적 대시보드 제공"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/distance', methods=['POST'])
def receive_distance():
    data = request.get_json()
    distance_state.update({
        'current_distance': data.get('current_distance'),
        'initial_distance': data.get('initial_distance'),
        'distance_difference': data.get('distance_difference'),
        'elapsed_time': data.get('elapsed_time'),
        'source': data.get('source'),
        'timestamp': time.time()
    })

    log_api('distance')
    msg = (
        f"{distance_state.get('current_distance'):.2f}px "
        f"(Δ{distance_state.get('distance_difference'):.2f}px)"
    )
    server_log.append(f"distance: {msg}")
    if len(server_log) > 50:
        del server_log[0]

    print("📏 [웹서버] 거리 측정 결과 수신:")
    print(f" - 현재 거리: {distance_state.get('current_distance'):.2f}px")
    print(f" - 초기 거리: {distance_state.get('initial_distance'):.2f}px")
    print(f" - 차이: {distance_state.get('distance_difference'):.2f}px")
    print(f" - 경과 시간: {distance_state.get('elapsed_time'):.2f}s")
    print(f" - 출처: {distance_state.get('source')}")

    return jsonify({"status": "ok", "message": "Distance received"}), 200

@app.route('/api/voice-result', methods=['POST'])
def receive_voice_result():
    data = request.get_json()
    data_type = data.get("type")

    if data_type == "add":
        print("[웹서버] 일정 추가 수신:")
        print(data.get("data"))
        schedule_list.append(data.get("data"))
        server_log.append("schedule added")

    elif data_type == "view":
        print("[웹서버] 일정 조회 결과 수신:")
        for entry in data.get("data", []):
            print(entry)
        schedule_list[:] = data.get("data", [])
        server_log.append("schedule view")

    elif data_type == "exit":
        print("[웹서버] 종료 명령 수신:")
        print(data.get("message"))
        server_log.append("exit")

    else:
        print("[웹서버] 알 수 없는 타입의 데이터 수신:", data)
        server_log.append("unknown data")

    log_api('voice-result')
    if len(server_log) > 50:
        del server_log[0]

    return jsonify({"status": "ok", "message": "Voice result received"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

