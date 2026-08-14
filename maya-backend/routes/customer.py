from flask import Blueprint, request, jsonify
from services.customer_service import check_customer_by_phone

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/api/check-customer', methods=['POST'])
def handle_check_customer():
    """
    API Route: POST /api/check-customer
    
    Accepts JSON body:
    { "phone": "6302465126" }
    
    Identifies customer by phone number and returns identity details without financial data.
    """
    data = request.get_json(silent=True)
    
    if data is None or not isinstance(data, dict):
        return jsonify({
            "customer_found": False,
            "reason": "PHONE_REQUIRED"
        }), 400

    if 'phone' not in data or data.get('phone') is None:
        return jsonify({
            "customer_found": False,
            "reason": "PHONE_REQUIRED"
        }), 400

    phone = data.get('phone')
    call_id = data.get('call_id')

    response_data, status_code = check_customer_by_phone(phone, call_id)
    return jsonify(response_data), status_code

