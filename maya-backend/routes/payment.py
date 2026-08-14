from flask import Blueprint, request, jsonify, render_template_string, redirect, url_for
from services.payment_service import send_payment_link, get_payment_page_data, process_demo_payment

payment_bp = Blueprint('payment', __name__)

PAYMENT_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kapture Finance - Demo Payment Gateway</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        body { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; padding: 20px; }
        .card { background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 32px; width: 100%; max-width: 440px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
        .header { text-align: center; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 16px; }
        .logo { font-size: 20px; font-weight: 700; color: #818cf8; letter-spacing: -0.5px; }
        .subtitle { font-size: 13px; color: #94a3b8; margin-top: 4px; }
        .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
        .label { color: #94a3b8; }
        .value { font-weight: 600; color: #f1f5f9; }
        .amount-box { background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 16px; margin: 20px 0; text-align: center; }
        .amount-label { font-size: 12px; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.5px; }
        .amount-val { font-size: 28px; font-weight: 800; color: #38bdf8; margin-top: 4px; }
        .status-container { text-align: center; margin: 20px 0; }
        .badge-paid { background: #059669; color: #ecfdf5; padding: 10px 20px; border-radius: 30px; font-size: 15px; font-weight: 700; display: inline-block; box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3); }
        .btn-pay { width: 100%; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; border: none; padding: 14px; border-radius: 10px; font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4); }
        .btn-pay:hover { transform: translateY(-2px); box-shadow: 0 15px 20px -3px rgba(99, 102, 241, 0.5); }
        .demo-tag { font-size: 11px; color: #64748b; text-align: center; margin-top: 16px; }
        .success-icon { font-size: 48px; color: #10b981; margin-bottom: 12px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="logo">KAPTURE FINANCE</div>
            <div class="subtitle">Secure Collections Payment Portal</div>
        </div>

        {% if is_paid %}
        <div style="text-align: center;">
            <div class="success-icon">✓</div>
            <div class="badge-paid">Payment Successful</div>
            <p style="color: #94a3b8; font-size: 14px; margin-top: 12px;">Thank you! Your payment for account <strong>{{ account_id }}</strong> has been recorded.</p>
        </div>
        {% else %}
        <div class="detail-row">
            <span class="label">Customer Name</span>
            <span class="value">{{ customer_name }}</span>
        </div>
        <div class="detail-row">
            <span class="label">Account Number</span>
            <span class="value">{{ account_id }}</span>
        </div>
        <div class="detail-row">
            <span class="label">Loan Type</span>
            <span class="value">{{ loan_type }}</span>
        </div>
        <div class="detail-row">
            <span class="label">Days Past Due</span>
            <span class="value">{{ days_past_due }} Days</span>
        </div>

        <div class="amount-box">
            <div class="amount-label">Overdue Amount Due</div>
            <div class="amount-val">₹{{ "%.2f"|format(overdue_amount) }}</div>
        </div>

        <form action="/payment/{{ account_id }}/pay" method="POST">
            <button type="submit" class="btn-pay">Pay Now (Demo)</button>
        </form>
        {% endif %}

        <div class="demo-tag">Prototype Demo Only — No Real Money Transacted</div>
    </div>
</body>
</html>
"""

@payment_bp.route('/api/send-payment-link', methods=['POST'])
def handle_send_payment_link():
    """
    API Route: POST /api/send-payment-link
    """
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({
            "success": False,
            "reason": "INVALID_JSON"
        }), 400

    account_id = data.get('account_id')
    phone = data.get('phone')
    call_id = data.get('call_id')

    response_data, status_code = send_payment_link(account_id, phone, call_id)
    return jsonify(response_data), status_code

@payment_bp.route('/payment/<account_id>', methods=['GET'])
def render_payment_page(account_id):
    """
    GET /payment/<account_id>
    Displays account payment details with demo Pay Now button.
    """
    data = get_payment_page_data(account_id)
    
    if not data:
        return f"<h3>Account {account_id} Not Found</h3>", 404

    is_paid = (data['payment_status'] == 'PAID' or data['overdue_amount'] <= 0)

    return render_template_string(
        PAYMENT_PAGE_HTML,
        account_id=data['account_id'],
        customer_name=data['customer_name'],
        loan_type=data['loan_type'],
        overdue_amount=data['overdue_amount'],
        days_past_due=data['days_past_due'],
        is_paid=is_paid
    ), 200

@payment_bp.route('/payment/<account_id>/pay', methods=['POST'])
def handle_demo_pay(account_id):
    """
    POST /payment/<account_id>/pay
    Processes demo payment, marks payment status as PAID in SQLite, and displays success UI.
    """
    success, msg = process_demo_payment(account_id)
    if not success:
        return f"<h3>Error: {msg}</h3>", 400

    return redirect(url_for('payment.render_payment_page', account_id=account_id))
