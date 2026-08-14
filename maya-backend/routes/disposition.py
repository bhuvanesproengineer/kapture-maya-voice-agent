from flask import Blueprint, request, jsonify
from services.disposition_service import mark_disposition

disposition_bp = Blueprint('disposition', __name__)

@disposition_bp.route('/api/mark-disposition', methods=['POST'])
def handle_mark_disposition():
    """
    API Route: POST /api/mark-disposition
    
    Request:
    {
        "account_id": "ACC001",
        "intent": "WILL_PAY",
        "outcome": "PTP_CREATED"
    }
    """
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({
            "success": False,
            "reason": "INVALID_JSON"
        }), 400

    account_id = data.get('account_id')
    intent = data.get('intent')
    outcome = data.get('outcome')
    call_id = data.get('call_id')

    response_data, status_code = mark_disposition(account_id, intent, outcome, call_id)
    return jsonify(response_data), status_code

