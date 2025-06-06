from flask import Flask, request, jsonify, send_from_directory
import time
import os
import sqlite3
import json

app = Flask(__name__, static_folder='WEB_STATIC', static_url_path='')

# ---------------------------
# SQLite 데이터베이스 설정
# ---------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), 'web_server.db')
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS distance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        current_distance REAL,
        initial_distance REAL,
        distance_difference REAL,
        elapsed_time REAL,
        source TEXT,
        timestamp REAL
    )
''')
cur.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        timestamp REAL
    )
''')
conn.commit()

def load_initial_state():
    """서버 재시작 시 DB에서 최근 데이터 로드"""
    cur.execute(
        'SELECT current_distance, initial_distance, distance_difference, '
        'elapsed_time, source, timestamp '
        'FROM distance_logs ORDER BY timestamp DESC LIMIT 1'
    )
    row = cur.fetchone()
    if row:
        distance_state.update({
            'current_distance': row[0],
            'initial_distance': row[1],
            'distance_difference': row[2],
            'elapsed_time': row[3],
            'source': row[4],
            'timestamp': row[5]
        })
    cur.execute('SELECT data FROM schedules ORDER BY timestamp DESC LIMIT 10')
    rows = cur.fetchall()
    schedule_list[:] = [json.loads(r[0]) for r in rows]

load_initial_state()

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
    # DB에서 최신 값 조회
    cur.execute(
        'SELECT current_distance, initial_distance, distance_difference, '
        'elapsed_time, source, timestamp '
        'FROM distance_logs ORDER BY timestamp DESC LIMIT 1'
    )
    row = cur.fetchone()
    latest_distance = distance_state
    if row:
        latest_distance = {
            'current_distance': row[0],
            'initial_distance': row[1],
            'distance_difference': row[2],
            'elapsed_time': row[3],
            'source': row[4],
            'timestamp': row[5]
        }
    cur.execute('SELECT data FROM schedules ORDER BY timestamp DESC LIMIT 10')
    rows = cur.fetchall()
    schedules = [json.loads(r[0]) for r in rows]

    return jsonify({
        'distance': latest_distance,
        'api_log': api_log,
        'schedule': schedules,
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

    # DB 저장
    cur.execute(
        'INSERT INTO distance_logs (current_distance, initial_distance, '
        'distance_difference, elapsed_time, source, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
        (
            distance_state.get('current_distance'),
            distance_state.get('initial_distance'),
            distance_state.get('distance_difference'),
            distance_state.get('elapsed_time'),
            distance_state.get('source'),
            distance_state.get('timestamp')
        )
    )
    conn.commit()

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
        item = data.get("data")
        schedule_list.append(item)
        cur.execute(
            'INSERT INTO schedules (data, timestamp) VALUES (?, ?)',
            (json.dumps(item, ensure_ascii=False), time.time())
        )
        conn.commit()
        server_log.append("schedule added")

    elif data_type == "view":
        print("[웹서버] 일정 조회 결과 수신:")
        for entry in data.get("data", []):
            print(entry)
        schedule_list[:] = data.get("data", [])
        for entry in data.get("data", []):
            cur.execute(
                'INSERT INTO schedules (data, timestamp) VALUES (?, ?)',
                (json.dumps(entry, ensure_ascii=False), time.time())
            )
        conn.commit()
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

