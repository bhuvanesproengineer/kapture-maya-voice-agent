from flask import Blueprint, request, jsonify
from services.escalation_service import escalate_to_agent

escalation_bp = Blueprint('escalation', __name__)

@escalation_bp.route('/api/escalate-to-agent', methods=['POST'])
def handle_escalate_to_agent():
    """
    API Route: POST /api/escalate-to-agent
    
    Request:
    {
        "account_id": "ACC001",
        "reason": "CUSTOMER_DISPUTE"
    }
    """
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({
            "success": False,
            "reason": "INVALID_JSON"
        }), 400

    account_id = data.get('account_id')
    reason = data.get('reason')
    call_id = data.get('call_id')

    response_data, status_code = escalate_to_agent(account_id, reason, call_id)
    return jsonify(response_data), status_code

