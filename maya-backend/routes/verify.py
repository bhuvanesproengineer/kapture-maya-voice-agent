from flask import Blueprint, request, jsonify
from services.verification_service import start_verification, verify_otp_session

verify_bp = Blueprint('verify', __name__)

@verify_bp.route('/api/verify-customer', methods=['POST'])
def verify_customer():
    """
    API Route: POST /api/verify-customer
    
    Supports a two-stage verification flow:
    
    STAGE 1 — Start verification:
    Request: { "phone": "6302465126" }
    
    STAGE 2 — Verify OTP:
    Request: { "verification_id": "VER001", "otp": "4821" }
    """
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({
            "verified": False,
            "reason": "INVALID_JSON"
        }), 400

    verification_id = data.get('verification_id')
    otp = data.get('otp')
    phone = data.get('phone')

    # Stage 2: Verification ID & OTP supplied
    if verification_id is not None or otp is not None:
        if not verification_id or not otp:
            return jsonify({
                "verified": False,
                "reason": "MISSING_VERIFICATION_ID_OR_OTP"
            }), 400
        
        response_data, status_code = verify_otp_session(verification_id, otp)
        return jsonify(response_data), status_code

    # Stage 1: Phone supplied to initiate OTP verification session
    if phone is not None:
        response_data, status_code = start_verification(phone)
        return jsonify(response_data), status_code

    return jsonify({
        "verified": False,
        "reason": "MISSING_PHONE_OR_VERIFICATION_ID"
    }), 400
