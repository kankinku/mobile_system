from flask import Flask, request, jsonify
from openai import OpenAI
import mysql.connector
import requests
import threading
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========== 설정 ==========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '0000'),
    'database': os.getenv('DB_NAME', 'appointment_db'),
    'charset': 'utf8mb4'
}

# ========== 시스템 클래스 ==========
class GPT:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def chat(self, system_prompt, user_input, max_tokens=500):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0
        )
        return response.choices[0].message.content.strip()

class Database:
    def __init__(self):
        self.config = DB_CONFIG
        self.init_database()

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                function_type VARCHAR(255),
                name VARCHAR(255),
                start_time VARCHAR(10),
                end_time VARCHAR(10),
                items TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        conn.commit()
        cursor.close()
        conn.close()

    def insert_appointment(self, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (function_type, name, start_time, end_time, items)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            data.get("사용기능"),
            data.get("이름"),
            data.get("시간"),
            data.get("목표시간"),
            data.get("준비물")
        ))
        conn.commit()
        cursor.close()
        conn.close()

    def get_today_appointments(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT function_type, name, start_time, end_time, items 
            FROM appointments
            WHERE DATE(created_at) = %s
            ORDER BY start_time
        ''', (today,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

class Weather:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"

    def get_weather_description(self, code):
        codes = {
            0: "맑음", 1: "대체로 맑음", 2: "부분적으로 흐림", 3: "흐림",
            45: "안개", 48: "서리 안개", 51: "가벼운 이슬비", 53: "보통 이슬비",
            55: "강한 이슬비", 61: "약한 비", 63: "보통 비", 65: "강한 비",
            71: "약한 눈", 73: "보통 눈", 75: "강한 눈", 80: "약한 소나기",
            81: "보통 소나기", 82: "강한 소나기", 95: "뇌우", 96: "약한 우박을 동반한 뇌우",
            99: "강한 우박을 동반한 뇌우"
        }
        return codes.get(code, "알 수 없는 날씨")

    def get_weather_info(self):
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "latitude": 37.5665,
                "longitude": 126.9780,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "Asia/Seoul"
            }
            response = requests.get(url, params=params)
            data = response.json()
            current = data["current"]
            desc = self.get_weather_description(current["weather_code"])
            return f"{desc}, 기온 {current['temperature_2m']}°C, 습도 {current['relative_humidity_2m']}%, 풍속 {current['wind_speed_10m']}km/h"
        except:
            return "맑은 날씨, 기온 20°C"

# ========== Flask 앱서버 ==========
app = Flask(__name__)
db = Database()
gpt = GPT(api_key=OPENAI_API_KEY)
weather = Weather()

@app.route('/api/voice', methods=['POST'])
def handle_voice():
    data = request.get_json()
    if not data or 'recognized_text' not in data:
        return jsonify({"status": "error", "message": "recognized_text 필요"}), 400

    user_input = data['recognized_text']
    print(f"\n🎤 수신된 음성: {user_input}")
    threading.Thread(target=process_input, args=(user_input,), daemon=True).start()
    return jsonify({"status": "ok", "message": "처리 중"}), 200

def process_input(user_input):
    try:
        intent_prompt = """사용자의 입력을 분석하여 다음 중 하나로 분류:
1. add_appointment
2. view_summary
3. cleanup_appointments
4. reset_database
5. exit
JSON으로 반환: {"intent": "...", "confidence": 0.9, "extracted_data": "..."}"""
        intent_result = gpt.chat(intent_prompt, user_input)
        intent_data = json.loads(intent_result)
        intent = intent_data.get("intent")
        print(f"🧠 의도: {intent} ({intent_data.get('confidence')})")

        if intent == "add_appointment":
            classification_prompt = f"""입력을 다음과 같이 분류:
{{
    "사용기능": "기능명",
    "이름": "이름",
    "시간": "HH:MM",
    "목표시간": "HH:MM",
    "준비물": "필요 준비물"
}}
현재 날씨: {weather.get_weather_info()}"""
            classified = gpt.chat(classification_prompt, user_input)
            data = json.loads(classified)
            db.insert_appointment(data)
            print("✅ 일정이 저장되었습니다.")
            print(json.dumps(data, indent=2, ensure_ascii=False))

        elif intent == "view_summary":
            rows = db.get_today_appointments()
            if not rows:
                print("📋 오늘은 일정이 없습니다.")
                return
            print("📋 오늘의 일정:")
            for i, row in enumerate(rows, 1):
                function_type, name, start, end, items = row
                print(f"{i}. {name} ({start}{' ~ ' + end if end else ''}) - 준비물: {items or '없음'}")

        elif intent == "cleanup_appointments":
            print("🧹 정리 기능은 추후 구현 가능")

        elif intent == "reset_database":
            db.init_database()
            print("🗑️ 데이터베이스가 초기화되었습니다.")

        elif intent == "exit":
            print("📡 라즈베리파이에 음성 인식 종료 신호 전송 중...")
            try:
                rpi_ip = os.getenv("RASPBERRY_PI_IP", "192.168.0.50")
                rpi_port = os.getenv("RASPBERRY_PI_PORT", "5000")
                requests.post(f"http://{rpi_ip}:{rpi_port}/voice-stop", timeout=3)
                print("✅ 라즈베리파이에 음성 인식 종료 요청 전송 완료")
            except Exception as e:
                print(f"❌ 종료 신호 전송 실패: {e}")
                print("✅ 라즈베리파이에 종료 요청 전송 완료")
            except Exception as e:
                print(f"❌ 종료 신호 전송 실패: {e}")

        else:
            print("❓ 의도 분석 실패")

    except Exception as e:
        print(f"❌ 처리 오류: {e}")

if __name__ == '__main__':
    import signal
    import sys

    def shutdown_handler(sig, frame):
        print("🛑 서버가 라즈베리파이 종료 신호를 받아 종료됩니다.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    @app.route('/shutdown-server', methods=['POST'])
    def shutdown_server():
        print("📴 라즈베리파이로부터 서버 종료 신호 수신")
        shutdown_handler(None, None)
        return "서버 종료됨", 200

    port = int(os.getenv("APP_SERVER_PORT", 8080))
    app.run(host='0.0.0.0', port=port)
