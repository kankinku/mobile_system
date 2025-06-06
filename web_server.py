from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/api/distance', methods=['POST'])
def receive_distance():
    data = request.get_json()
    print("📏 [웹서버] 거리 측정 결과 수신:")
    print(f" - 현재 거리: {data.get('current_distance'):.2f}px")
    print(f" - 초기 거리: {data.get('initial_distance'):.2f}px")
    print(f" - 차이: {data.get('distance_difference'):.2f}px")
    print(f" - 경과 시간: {data.get('elapsed_time'):.2f}s")
    print(f" - 출처: {data.get('source')}")
    return jsonify({"status": "ok", "message": "Distance received"}), 200

@app.route('/api/voice-result', methods=['POST'])
def receive_voice_result():
    data = request.get_json()
    data_type = data.get("type")

    if data_type == "add":
        print("[웹서버] 일정 추가 수신:")
        print(data.get("data"))

    elif data_type == "view":
        print("[웹서버] 일정 조회 결과 수신:")
        for entry in data.get("data", []):
            print(entry)

    elif data_type == "exit":
        print("[웹서버] 종료 명령 수신:")
        print(data.get("message"))

    else:
        print("[웹서버] 알 수 없는 타입의 데이터 수신:", data)

    return jsonify({"status": "ok", "message": "Voice result received"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
