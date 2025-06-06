# app_server.py
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/api/voice', methods=['POST'])
def receive_voice():
    data = request.get_json()
    print("🎤 [앱서버] 음성 인식 결과 수신:")
    print(f" - 텍스트: {data.get('recognized_text')}")
    print(f" - 타임스탬프: {data.get('timestamp')}")
    print(f" - 출처: {data.get('source')}")
    return jsonify({"status": "ok", "message": "Voice received"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
