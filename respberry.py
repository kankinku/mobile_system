import os
import warnings
import logging
import cv2
import time
import requests
import mediapipe as mp
import numpy as np
import threading
import speech_recognition as sr
from collections import deque
from flask import Flask, request, jsonify

# python-dotenv 설치 확인 및 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다. pip install python-dotenv로 설치하세요.")
    print("기본값을 사용합니다.")

# 환경 설정 및 경고 억제
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['DISPLAY'] = ''
warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('mediapipe').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

class VoiceStopGestureRecognizer:
    def __init__(self):
        """
        HTTP 음성 중지 신호 제스처 인식기
        - left_hand: 음성인식 루프 시작 → HTTP /voice-stop 신호로 종료
        - right_hand: 거리측정 → 웹서버
        """
        # 환경변수에서 서버 설정 읽기[1]
        self.app_server_ip = os.getenv('APP_SERVER_IP', '192.168.1.100')
        self.web_server_ip = os.getenv('WEB_SERVER_IP', '192.168.1.101')
        self.app_server_port = os.getenv('APP_SERVER_PORT', '8080')
        self.web_server_port = os.getenv('WEB_SERVER_PORT', '3000')

        # 라즈베리 파이 HTTP 서버 설정
        self.rpi_port = int(os.getenv('RASPBERRY_PI_PORT', '5000'))

        # 서버 URL 생성[1]
        self.app_server_url = f"http://{self.app_server_ip}:{self.app_server_port}/api"
        self.web_server_url = f"http://{self.web_server_ip}:{self.web_server_port}/api"

        self.POSE_DIR = "stored_poses"

        # MediaPipe 초기화[2][3]
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.4,
            model_complexity=0
        )

        # 음성 인식 초기화[4]
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.setup_microphone()

        # 모드 관리 (motion/voice)
        self.mode = 'motion'
        self.voice_loop_active = False
        self.voice_stop_signal_received = False
        self.voice_loop_thread = None

        # 상태 관리
        self.running = False
        self.measurement_lock = threading.Lock()

        # 거리 측정 변수[2]
        self.measuring_active = False
        self.measuring_start_time = 0
        self.measuring_duration = 5.0
        self.initial_distance = None
        self.last_print_time = 0
        self.last_send_time = 0
        self.print_interval = 1.0
        self.send_interval = 0.1

        # 제스처 감지[2]
        self.gesture_buffer = deque(maxlen=3)
        self.last_gesture_time = {}
        self.gesture_cooldown = 1.5

        # Flask 앱 초기화
        self.flask_app = Flask(__name__)
        self.setup_flask_routes()

        self.saved_poses = self.load_poses()
        self.print_initialization_status()

    def print_initialization_status(self):
        """초기화 상태 출력"""
        print("=" * 60)
        print("🤖 HTTP 음성 중지 신호 제스처 인식기 초기화 완료")
        print(f"📱 앱서버 (음성): {self.app_server_url}")
        print(f"🌐 웹서버 (거리): {self.web_server_url}")
        print(f"🔌 라즈베리파이 HTTP 서버: 포트 {self.rpi_port}")
        print(f"📁 저장된 포즈: {list(self.saved_poses.keys())}")
        print(f"🎤 마이크 상태: {'✅ 준비됨' if self.microphone else '❌ 오류'}")
        print("🔄 left_hand: 음성 루프 시작 (HTTP /voice-stop 신호로 종료)")
        print("📏 right_hand: 5초간 거리측정")
        print("=" * 60)
        time.sleep(0.3)  # 사용자 인터페이스 타이밍 선호사항 반영[8]

    def setup_flask_routes(self):
        """Flask HTTP 엔드포인트 설정"""
        @self.flask_app.route('/voice-stop', methods=['POST'])
        def voice_stop():
            """음성 인식 중지 신호 수신"""
            try:
                print("📡 HTTP 음성 인식 중지 신호 수신")
                time.sleep(0.2)  # 출력 간격 조절[8]
                self.voice_stop_signal_received = True
                self.voice_loop_active = False
                print("✅ 음성 인식 중지 신호 처리 완료")
                return jsonify({"status": "success", "message": "Voice recognition stopped"}), 200
            except Exception as e:
                print(f"❌ 음성 중지 신호 처리 오류: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.flask_app.route('/status', methods=['GET'])
        def get_status():
            """현재 상태 확인"""
            return jsonify({
                "mode": self.mode,
                "voice_loop_active": self.voice_loop_active,
                "measuring_active": self.measuring_active,
                "running": self.running
            }), 200

    def start_flask_server(self):
        """Flask 서버 시작 (백그라운드)"""
        def run_flask():
            # Flask 로그 억제
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            self.flask_app.run(host='0.0.0.0', port=self.rpi_port, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print(f"🔌 Flask HTTP 서버 시작됨 (포트: {self.rpi_port})")
        time.sleep(0.3)

    def setup_microphone(self):
        """USB 마이크 설정[4]"""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            usb_mic_index = None

            for i, name in enumerate(mic_list):
                if name and any(keyword in name.lower() for keyword in
                               ['usb', 'composite', 'hw:2,0', 'card 2']):
                    usb_mic_index = i
                    break

            self.microphone = sr.Microphone(device_index=usb_mic_index) if usb_mic_index is not None else sr.Microphone()

            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

        except Exception:
            self.microphone = sr.Microphone()

    def extract_landmarks(self, frame):
        """손 랜드마크 추출[2]"""
        try:
            small_frame = cv2.resize(frame, (320, 240))
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                landmarks = np.array([[lm.x * frame.shape[1], lm.y * frame.shape[0]]
                                    for lm in hand_landmarks.landmark])
                return landmarks
        except Exception:
            pass
        return None

    def calculate_distance(self, p1, p2):
        """거리 계산[2]"""
        try:
            return np.linalg.norm(np.array(p1) - np.array(p2))
        except Exception:
            return 0.0

    def pose_similarity(self, pose1, pose2):
        """포즈 유사도 계산[2]"""
        try:
            if pose1 is None or pose2 is None or len(pose1) != 21:
                return float('inf')

            norm_pose1 = pose1 - pose1[0]
            norm_pose2 = pose2 - pose2[0]

            key_points = [4, 8, 12, 16, 20]
            distances = [self.calculate_distance(norm_pose1[i], norm_pose2[i])
                        for i in key_points]
            return np.mean(distances)
        except Exception:
            return float('inf')

    def recognize_gesture(self, landmarks):
        """제스처 인식[2]"""
        if landmarks is None:
            self.gesture_buffer.append(None)
            return None

        best_match = None
        min_similarity = float('inf')

        for name, ref_pose in self.saved_poses.items():
            similarity = self.pose_similarity(ref_pose, landmarks)
            if similarity < min_similarity and similarity < 25:
                min_similarity = similarity
                best_match = name

        self.gesture_buffer.append(best_match)

        if len(self.gesture_buffer) >= 2:
            recent = list(self.gesture_buffer)[-2:]
            if all(g == best_match and g is not None for g in recent):
                return best_match

        return None

    def is_gesture_allowed(self, gesture_name):
        """제스처 쿨다운 확인"""
        current_time = time.time()
        return (gesture_name not in self.last_gesture_time or
                current_time - self.last_gesture_time[gesture_name] >= self.gesture_cooldown)

    def execute_gesture(self, gesture_name):
        """제스처 실행"""
        if not self.is_gesture_allowed(gesture_name):
            return

        self.last_gesture_time[gesture_name] = time.time()

        if gesture_name == "left_hand":
            print("🎤 left_hand 제스처 감지 - 음성 루프 시작")
            time.sleep(0.2)
            self.start_voice_loop()
        elif gesture_name == "right_hand":
            print("📏 right_hand 제스처 감지 - 5초간 거리 측정 시작")
            time.sleep(0.2)
            self.start_distance_measurement()

    def start_voice_loop(self):
        """음성 인식 루프 시작 - HTTP /voice-stop 신호까지 반복"""
        if self.voice_loop_active:
            print("🎤 이미 음성 루프가 실행 중입니다.")
            return

        self.mode = 'voice'
        self.voice_loop_active = True
        self.voice_stop_signal_received = False

        print("🔄 음성 루프 모드 시작 - HTTP /voice-stop 신호까지 반복")
        time.sleep(0.3)
        self.voice_loop_thread = threading.Thread(target=self._voice_loop_thread, daemon=True)
        self.voice_loop_thread.start()

    def _voice_loop_thread(self):
        """음성 인식 루프 스레드[4]"""
        loop_count = 0

        while self.voice_loop_active and not self.voice_stop_signal_received:
            loop_count += 1
            print(f"🎤 음성 인식 시작 (루프 {loop_count}회)")
            time.sleep(0.2)

            try:
                with self.microphone as source:
                    print("🎤 음성 입력 대기 중... (5초 타임아웃)")
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)

                print("🔄 음성 처리 중...")
                text = self.recognizer.recognize_google(audio, language='ko-KR')
                print(f"✅ 인식된 텍스트: '{text}'")
                time.sleep(0.2)

                # 앱서버로 음성인식 결과 전송
                self.send_voice_to_app_server(text)

            except sr.WaitTimeoutError:
                print("⏰ 음성 입력 타임아웃 - 다시 시도")
            except sr.UnknownValueError:
                print("❌ 음성을 인식할 수 없습니다 - 다시 시도")
            except Exception as e:
                print(f"❌ 음성 인식 오류: {e} - 다시 시도")

            # HTTP 중지 신호 체크
            if self.voice_stop_signal_received:
                print("📡 HTTP 음성 중지 신호 확인, 루프 종료")
                break

            # 루프 간격
            time.sleep(1)

        # 음성 루프 종료 시 모션 인식 모드로 복귀
        self.voice_loop_active = False
        self.mode = 'motion'
        print("🔄 음성 루프 종료 - 모션 인식 모드로 복귀")
        time.sleep(0.3)

    def send_voice_to_app_server(self, text):
        """음성 인식 결과를 앱서버로 전송[1]"""
        def send_async():
            try:
                response = requests.post(
                    f"{self.app_server_url}/voice",
                    json={
                        "recognized_text": text,
                        "timestamp": time.time(),
                        "source": "raspberry_pi",
                        "loop_mode": True
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"📤 앱서버 전송 완료: {text}")
                else:
                    print(f"⚠️ 앱서버 응답 오류: {response.status_code}")
            except Exception as e:
                print(f"❌ 앱서버 전송 실패: {e}")

        threading.Thread(target=send_async, daemon=True).start()

    def start_distance_measurement(self):
        """거리 측정 시작[2]"""
        with self.measurement_lock:
            self.measuring_active = True
            self.measuring_start_time = time.time()
            self.initial_distance = None
            self.last_print_time = 0
            self.last_send_time = 0

    def process_timed_distance_measurement(self, landmarks):
        """시간 기반 거리 측정 처리[2]"""
        if not self.measuring_active:
            return

        current_time = time.time()
        elapsed = current_time - self.measuring_start_time

        if elapsed > self.measuring_duration:
            with self.measurement_lock:
                self.measuring_active = False
            print("📐 5초 경과 - 거리 측정 완료")
            time.sleep(0.2)
            return

        if landmarks is None:
            return

        try:
            with self.measurement_lock:
                thumb_tip = landmarks[4]
                index_tip = landmarks[8]
                current_distance = self.calculate_distance(thumb_tip, index_tip)

                if self.initial_distance is None:
                    self.initial_distance = current_distance
                    print(f"📏 초기 거리 설정: {self.initial_distance:.2f}px")

                distance_diff = current_distance - self.initial_distance

                if current_time - self.last_print_time >= self.print_interval:
                    remaining_time = self.measuring_duration - elapsed
                    print(f"📊 초기: {self.initial_distance:.2f}px | 현재: {current_distance:.2f}px | 차이: {distance_diff:.2f}px | 남은시간: {remaining_time:.1f}s")
                    self.last_print_time = current_time

                if current_time - self.last_send_time >= self.send_interval:
                    self.send_distance_to_web_server(distance_diff, current_distance, self.initial_distance, elapsed)
                    self.last_send_time = current_time

        except Exception as e:
            print(f"❌ 거리 측정 오류: {e}")

    def send_distance_to_web_server(self, distance_diff, current_distance, initial_distance, elapsed_time):
        """거리 측정 결과를 웹서버로 전송[1]"""
        def send_async():
            try:
                response = requests.post(
                    f"{self.web_server_url}/distance",
                    json={
                        "distance_difference": distance_diff,
                        "current_distance": current_distance,
                        "initial_distance": initial_distance,
                        "elapsed_time": elapsed_time,
                        "timestamp": time.time(),
                        "source": "raspberry_pi",
                        "unit": "pixels"
                    },
                    timeout=2
                )
                if response.status_code != 200:
                    print(f"⚠️ 웹서버 응답 오류: {response.status_code}")
            except Exception:
                pass

        threading.Thread(target=send_async, daemon=True).start()

    def load_poses(self):
        """저장된 포즈 로드"""
        saved = {}
        if not os.path.exists(self.POSE_DIR):
            return saved

        for file in os.listdir(self.POSE_DIR):
            if file.endswith("_pose.npy") and file.startswith(("left_hand", "right_hand")):
                name = file.replace("_pose.npy", "")
                try:
                    pose = np.load(os.path.join(self.POSE_DIR, file))
                    if pose.shape == (21, 2):
                        saved[name] = pose
                except Exception:
                    pass
        return saved

    def run(self):
        """메인 실행 - Flask 서버와 제스처 인식 동시 실행[3]"""
        # Flask 서버 시작
        self.start_flask_server()

        # 카메라 초기화[3]
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        cap.set(cv2.CAP_PROP_FPS, 15)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print("❌ 카메라를 열 수 없습니다.")
            return

        self.running = True
        frame_count = 0
        current_gesture = None

        print("\n🎥 HTTP 음성 중지 신호 + 제스처 인식 시작 - Ctrl+C로 종료")
        print("📋 현재 모드: 모션 인식")
        time.sleep(0.3)

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # 모션 인식 모드에서만 제스처 감지
                if self.mode == 'motion' and frame_count % 3 == 0:
                    landmarks = self.extract_landmarks(frame)
                    detected_gesture = self.recognize_gesture(landmarks)

                    if detected_gesture and detected_gesture != current_gesture:
                        current_gesture = detected_gesture
                        print(f"🎯 제스처 감지: {detected_gesture}")
                        time.sleep(0.2)
                        self.execute_gesture(detected_gesture)

                    # 거리 측정 처리
                    self.process_timed_distance_measurement(landmarks)

                    if detected_gesture is None:
                        current_gesture = None

                # 음성 모드 상태 확인
                elif self.mode == 'voice':
                    if not self.voice_loop_active:
                        self.mode = 'motion'
                        print("📋 현재 모드: 모션 인식")
                        time.sleep(0.2)

                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 중단됨")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            self.stop()
            cap.release()

    def stop(self):
        """시스템 정지"""
        self.running = False
        self.voice_loop_active = False
        self.voice_stop_signal_received = True

        with self.measurement_lock:
            self.measuring_active = False

        self.hands.close()
        print("🔚 HTTP 음성 중지 신호 + 제스처 인식기 종료")

# 메인 실행
if __name__ == "__main__":
    recognizer = VoiceStopGestureRecognizer()

    try:
        recognizer.run()
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
    finally:
        recognizer.stop()
