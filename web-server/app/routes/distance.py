from flask import Blueprint, request, jsonify
from app.services.memory_store import distance_state, server_log
from app.services.logger import log_api
import time

bp = Blueprint('distance', __name__, url_prefix='/api')

@bp.route('/distance', methods=['POST'])
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
    msg = (
        f"{distance_state.get('current_distance'):.2f}px "
        f"(Δ{distance_state.get('distance_difference'):.2f}px)"
    )
    server_log.append(f"distance: {msg}")
    log_api('/api/distance')

    return jsonify({"status": "ok"}), 200
