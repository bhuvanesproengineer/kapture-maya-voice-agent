from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from routes.customer import customer_bp
from routes.otp import otp_bp
from routes.account import account_bp
from routes.verify import verify_bp
from routes.ptp import ptp_bp
from routes.payment import payment_bp
from routes.disposition import disposition_bp
from routes.escalation import escalation_bp

# Initialize Flask Application
app = Flask(__name__)

# Enable CORS for external API consumers (e.g. Vapi custom tools)
CORS(app)

# Register Blueprints for all business endpoints
app.register_blueprint(customer_bp)
app.register_blueprint(otp_bp)
app.register_blueprint(account_bp)
app.register_blueprint(verify_bp)
app.register_blueprint(ptp_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(disposition_bp)
app.register_blueprint(escalation_bp)

# Global JSON error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "BAD_REQUEST", "message": str(e.description if hasattr(e, 'description') else e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "NOT_FOUND", "message": "The requested endpoint or resource was not found."}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}), 500

if __name__ == '__main__':
    print("Starting Kapture Finance Maya Collections Backend API Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
# Reloaded for Customer Account Details module
