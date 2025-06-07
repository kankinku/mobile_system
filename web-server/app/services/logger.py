from app.services.memory_store import api_log
import time

def log_api(endpoint, status=200):
    api_log.append({'endpoint': endpoint, 'status': status, 'timestamp': time.time()})
    if len(api_log) > 20:
        del api_log[0]
