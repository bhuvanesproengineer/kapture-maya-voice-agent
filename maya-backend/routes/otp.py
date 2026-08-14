from flask import Blueprint, request, jsonify
from services.otp_service import send_otp_to_customer, verify_otp_session

otp_bp = Blueprint('otp', __name__)

@otp_bp.route('/api/send-otp', methods=['POST'])
def handle_send_otp():
    """
    API Route: POST /api/send-otp (MODULE 2)
    
    Accepts JSON body:
    { "phone": "6302465126" }
    
    Generates OTP, stores session in SQLite, and dispatches Twilio SMS.
    """
    data = request.get_json(silent=True)
    
    if data is None or not isinstance(data, dict):
        return jsonify({
            "otp_sent": False,
            "reason": "PHONE_REQUIRED"
        }), 400

    if 'phone' not in data or data.get('phone') is None:
        return jsonify({
            "otp_sent": False,
            "reason": "PHONE_REQUIRED"
        }), 400

    phone = data.get('phone')
    call_id = data.get('call_id')

    response_data, status_code = send_otp_to_customer(phone, call_id)
    return jsonify(response_data), status_code

@otp_bp.route('/api/verify-otp', methods=['POST'])
def handle_verify_otp():
    """
    API Route: POST /api/verify-otp (MODULE 3)
    
    Accepts JSON body:
    { "verification_id": "VER001", "otp": "6346" }
    
    Verifies the submitted OTP against active SQLite otp_sessions.
    """
    data = request.get_json(silent=True)
    
    if data is None or not isinstance(data, dict):
        return jsonify({
            "verified": False,
            "reason": "INVALID_REQUEST"
        }), 400

    if 'verification_id' not in data or data.get('verification_id') is None or str(data.get('verification_id')).strip() == "":
        return jsonify({
            "verified": False,
            "reason": "VERIFICATION_ID_REQUIRED"
        }), 400

    if 'otp' not in data or data.get('otp') is None or str(data.get('otp')).strip() == "":
        return jsonify({
            "verified": False,
            "reason": "OTP_REQUIRED"
        }), 400

    otp_val = str(data.get('otp')).strip()
    if len(otp_val) != 4 or not otp_val.isdigit():
        return jsonify({
            "verified": False,
            "reason": "INVALID_OTP_FORMAT"
        }), 400

    verification_id = str(data.get('verification_id')).strip()
    call_id = data.get('call_id')

    response_data, status_code = verify_otp_session(verification_id, otp_val, call_id)
    return jsonify(response_data), status_code

