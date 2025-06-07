from flask import Blueprint, request, jsonify
from app.services.memory_store import schedule_list, server_log
from app.services.logger import log_api

bp = Blueprint('voice_result', __name__, url_prefix='/api')

@bp.route('/voice-result', methods=['POST'])
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

    log_api('/api/voice-result')
    if len(server_log) > 50:
        del server_log[0]

    return jsonify({"status": "ok", "message": "Voice result received"}), 200

@bp.route('/delete', methods=['POST'])
def delete_schedule():
    from app.services.memory_store import schedule_list
    data = request.get_json()
    title = data.get('title')

    if not title:
        return jsonify({'status': 'error', 'message': '제목이 필요합니다.'}), 400

    # 일정 제거
    original_len = len(schedule_list)
    schedule_list[:] = [s for s in schedule_list if s.get('이름') != title and s.get('title') != title]
    
    if len(schedule_list) == original_len:
        return jsonify({'status': 'error', 'message': '일정이 존재하지 않습니다.'}), 404

    from app.services.logger import log_api
    from app.services.memory_store import server_log
    server_log.append(f"일정 삭제됨: {title}")
    log_api('/api/delete')

    return jsonify({'status': 'ok', 'message': f'{title} 삭제됨'}), 200
