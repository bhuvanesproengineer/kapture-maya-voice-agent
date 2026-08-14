from flask import Blueprint, request, jsonify
from services.ptp_service import log_promise_to_pay

ptp_bp = Blueprint('ptp', __name__)

@ptp_bp.route('/api/log-promise-to-pay', methods=['POST'])
def handle_log_promise_to_pay():
    """
    API Route: POST /api/log-promise-to-pay
    
    Request:
    {
        "account_id": "ACC001",
        "amount": 8499,
        "ptp_date": "2026-08-15"
    }
    """
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({
            "success": False,
            "reason": "INVALID_JSON"
        }), 400

    account_id = data.get('account_id')
    amount = data.get('amount')
    ptp_date = data.get('ptp_date')

    response_data, status_code = log_promise_to_pay(account_id, amount, ptp_date)
    return jsonify(response_data), status_code
