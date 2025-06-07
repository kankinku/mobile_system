from flask import Blueprint, jsonify, send_from_directory, current_app
from app.services.memory_store import distance_state, schedule_list, api_log, server_log

# 📦 /api/state 라우트용 Blueprint
api_bp = Blueprint('api_state', __name__, url_prefix='/api')

@api_bp.route('/state', methods=['GET'])
def get_state():
    return jsonify({
        'distance': distance_state,
        'schedule': schedule_list,
        'api_log': api_log,
        'logs': server_log
    })


# 📦 / (루트) 정적 파일 제공용 Blueprint
web_bp = Blueprint('web_root', __name__, url_prefix='')

@web_bp.route('/')
def root():
    return send_from_directory(current_app.static_folder, 'index.html')
