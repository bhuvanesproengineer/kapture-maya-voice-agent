from flask import Blueprint, request, jsonify
from services.payment_service import send_payment_link

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/api/send-payment-link', methods=['POST'])
def handle_send_payment_link():
    """
    API Route: POST /api/send-payment-link
    
    Request:
    {
        "account_id": "ACC001",
        "phone": "6302465126"
    }
    """
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({
            "success": False,
            "reason": "INVALID_JSON"
        }), 400

    account_id = data.get('account_id')
    phone = data.get('phone')

    response_data, status_code = send_payment_link(account_id, phone)
    return jsonify(response_data), status_code
