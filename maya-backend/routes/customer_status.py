from flask import Blueprint, jsonify
from services.customer_status_service import get_customer_status

customer_status_bp = Blueprint('customer_status', __name__)

@customer_status_bp.route('/api/customer-status/<account_id>', methods=['GET'])
def handle_get_customer_status(account_id):
    """
    Read-only testing/demo API route: GET /api/customer-status/<account_id>
    Returns combined customer, loan account, PTP, payment, disposition, and escalation details.
    """
    response_data, status_code = get_customer_status(account_id)
    return jsonify(response_data), status_code
