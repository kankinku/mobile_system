# web_server.py
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
