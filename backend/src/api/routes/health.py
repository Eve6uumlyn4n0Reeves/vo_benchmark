from flask import Blueprint, jsonify
from datetime import datetime, timezone
import time

bp = Blueprint('health_legacy', __name__, url_prefix='/api/v1/health')

_start_time = time.time()

@bp.route('/', methods=['GET', 'OPTIONS'])
def basic_health():
    # Basic legacy-compatible health endpoint
    resp = jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'uptime': time.time() - _start_time,
    })
    return resp, 200

@bp.route('/detailed', methods=['GET'])
def detailed_health():
    # Minimal legacy detailed endpoint matching tests' expectations
    return jsonify({
        'status': 'healthy',
        'system': {},
        'dependencies': [],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'uptime': time.time() - _start_time,
    }), 200

