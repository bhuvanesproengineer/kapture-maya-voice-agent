from flask import Blueprint, request, jsonify
from services.account_service import get_account_details_by_verification

account_bp = Blueprint('account', __name__)

@account_bp.route('/api/get-account-details', methods=['POST'])
def handle_get_account_details():
    """
    API Route: POST /api/get-account-details
    
    Accepts JSON body:
    { "verification_id": "VER001" }
    
    Returns loan account details for authenticated customer sessions.
    """
    data = request.get_json(silent=True)
    
    if data is None or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "reason": "VERIFICATION_ID_REQUIRED"
        }), 400

    if 'verification_id' not in data or data.get('verification_id') is None or str(data.get('verification_id')).strip() == "":
        return jsonify({
            "success": False,
            "reason": "VERIFICATION_ID_REQUIRED"
        }), 400

    verification_id = data.get('verification_id')

    response_data, status_code = get_account_details_by_verification(verification_id)
    return jsonify(response_data), status_code
