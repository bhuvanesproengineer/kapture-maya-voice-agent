# Kapture Finance Assistant — Backend

## 1. Project Overview

* **What the backend does**: The backend for Kapture Finance Assistant provides a secure REST API platform for managing debt collections workflows. It handles customer lookup, multi-stage identity verification via SMS OTP, loan account details retrieval, Promise-to-Pay (PTP) tracking, demo payment link dispatch, call disposition recording, human-agent escalation ticketing, and status reporting.
* **Purpose of the voice assistant**: To automate outbound and inbound collection interactions through an AI voice agent ("Maya"). The backend serves as the backend engine called by the voice agent (via Vapi custom tools) to authenticate callers, present overdue balances, process commitments, and dispatch payment links during live telephone conversations.
* **Short description of the system**: A lightweight Python and Flask REST service integrated with SQLite for data persistence and Twilio for SMS delivery, engineered specifically for tool-calling integration with AI voice platforms.

## 2. Key Features

List of implemented features:

* **Customer Identification**: Lookup customer identities by phone number with automatic normalization (stripping `+91`, `91`, `0`, and special characters) without exposing financial details prior to authentication.
* **Identity Verification & OTP Auth**: Two-stage customer authentication using 4-digit numeric OTPs generated via cryptographically secure randomness (`secrets` module), session expiration (5 minutes), attempt limiting (max 3 attempts), and constant-time string comparison (`secrets.compare_digest`).
* **Voice Conversation Handling**: REST API routes equipped to accept `call_id` metadata from Vapi voice sessions for correlated call tracking.
* **Customer & Account Data Handling**: Controlled retrieval of loan account information (loan type, overdue amount, days past due, payment status) protected behind verified OTP sessions (`verified = 1`).
* **Promise-to-Pay (PTP) Logging**: Recording customer commitments to pay specific overdue amounts by target dates into the database, returning reference numbers (`PTP001`).
* **Payment Link Generation & Dispatch**: Dynamic generation of web payment URLs (`/payment/<account_id>`) dispatched directly to customer mobile devices via Twilio SMS.
* **Demo Payment Gateway UI & Simulation**: HTML/CSS portal with glassmorphism UI for customer payment simulation, updating loan account balances to zero and status to `PAID`.
* **Call Management & Disposition Tracking**: Recording final interaction outcomes and customer intent (`WILL_PAY`, `ALREADY_PAID`, `DISPUTE`, `HARDSHIP`, `DO_NOT_CALL`, `CALLBACK`, `ESCALATION`) with disposition references (`DISP001`).
* **Human-Agent Escalation**: Creation of escalation tickets (`ESC001`) with dispute or hardship reasons for manual agent follow-up.
* **Customer Interaction Status Aggregation**: Admin/demo endpoint (`GET /api/customer-status/<account_id>`) consolidating customer profile, loan status, latest PTP, latest payment, latest disposition, and latest escalation.
* **Logging & Error Handling**: Centralized logger with automatic redaction of sensitive payload attributes (`otp`, `auth_token`, `password`, `secret`).

## 3. System Architecture

The backend architecture connects the Vapi voice AI agent to business logic and data stores:

```
Customer Call → Voice Agent (Vapi) → Flask REST APIs → Business Logic Services → SQLite DB / Twilio SMS → JSON Response / Web Portal
```

### Request and Call Flow Explanation

1. **Call Setup & Identification**: The Vapi Voice Agent handles caller interaction and invokes `POST /api/check-customer` with the caller's phone number. The backend normalizes the phone number, checks `customers` table, and returns customer identity details.
2. **OTP Generation & Verification**: Voice Agent calls `POST /api/send-otp` (or stage 1 of `POST /api/verify-customer`) to generate a 4-digit code and dispatch it via Twilio SMS. The customer speaks the OTP, and the agent calls `POST /api/verify-otp` (or stage 2). Upon successful constant-time matching, the session is flagged as `verified = 1`.
3. **Account Details & Negotiation**: Voice Agent requests account details via `POST /api/get-account-details` passing `verification_id`. The backend checks verification status and returns loan overdue details.
4. **Action Execution**:
   * **PTP**: Agent logs payment commitment via `POST /api/log-promise-to-pay`.
   * **Payment Link**: Agent requests SMS link via `POST /api/send-payment-link`, triggering Twilio SMS containing the payment portal URL.
   * **Escalation**: Agent logs ticket via `POST /api/escalate-to-agent`.
5. **Call Disposition**: Upon call completion, Agent posts interaction outcome to `POST /api/mark-disposition`.
6. **Data Storage & Response**: SQLite database records all transactions with write-ahead logging (WAL mode), and structured JSON responses guide the voice conversation.

## 4. Technology Stack

* **Runtime**: Python 3.10+
* **Framework**: Flask (v3.0.0+)
* **Language**: Python
* **Database**: SQLite 3 (with WAL mode enabled)
* **Voice/Telephony Provider**: Vapi (via REST custom tools API)
* **AI/LLM Provider**: Integrated via Vapi (Backend serves tool API endpoints)
* **TTS/STT Provider**: Managed via Vapi
* **SMS Provider**: Twilio SMS (`twilio` SDK v9.0.0+)
* **Authentication**: Session-based OTP verification (`otp_sessions` table)
* **Middleware & Libraries**: `Flask-CORS` (v4.0.0+), `gunicorn` (v23.0.0+), `python-dotenv` (v1.0.0+)

## 5. Project Structure

```
maya-backend/
├── app.py                      # Application entry point, CORS setup, Blueprint registration, global error handlers
├── requirements.txt            # Python package dependencies
├── .env                        # Environment variables configuration
├── .gitignore                  # Git ignore directives
├── database/
│   ├── database.db             # SQLite database storage file
│   └── init_db.py              # Database schema initialization and seed data script
├── routes/
│   ├── customer.py             # Route handler for /api/check-customer
│   ├── otp.py                  # Route handlers for /api/send-otp and /api/verify-otp
│   ├── account.py              # Route handler for /api/get-account-details
│   ├── verify.py               # Route handler for 2-stage /api/verify-customer
│   ├── ptp.py                  # Route handler for /api/log-promise-to-pay
│   ├── payment.py              # Route handlers for /api/send-payment-link, /payment/<account_id>, and payment POST
│   ├── disposition.py          # Route handler for /api/mark-disposition
│   ├── escalation.py           # Route handler for /api/escalate-to-agent
│   └── customer_status.py      # Route handler for GET /api/customer-status/<account_id>
├── services/
│   ├── customer_service.py     # Customer lookup and phone normalization business logic
│   ├── otp_service.py          # OTP generation, Twilio SMS sending, constant-time verification logic
│   ├── account_service.py      # Account details retrieval with strict OTP verification checking
│   ├── verification_service.py # 2-stage verification handling with console fallback log
│   ├── ptp_service.py          # Promise-to-pay recording business logic
│   ├── payment_service.py      # Payment link generation, SMS dispatch, and demo payment logic
│   ├── disposition_service.py  # Call disposition recording logic
│   ├── escalation_service.py   # Human agent escalation ticketing logic
│   └── customer_status_service.py # Aggregated customer interaction status lookup
└── utils/
    ├── logger.py               # Structured logger with automatic credential/OTP sanitization
    ├── otp.py                  # Secure OTP & verification ID generators
    └── phone.py                # Phone number normalization and calling format (+91) helper
```

## 6. Environment Variables

All environment variables used by the backend:

| Variable Name | Purpose | Required | Example Placeholder |
| --- | --- | --- | --- |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID for authenticating SMS API requests | Yes (for SMS delivery) | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token for authenticating SMS API requests | Yes (for SMS delivery) | `your_twilio_auth_token_here` |
| `TWILIO_PHONE_NUMBER` | Twilio registered phone number used as SMS sender (`from_`) | Yes (for SMS delivery) | `+18005550199` |
| `PAYMENT_BASE_URL` | Base public URL used to construct payment links sent via SMS | Optional | `https://your-app-name.onrender.com` |
| `BASE_URL` | Fallback base URL for payment links if `PAYMENT_BASE_URL` is omitted | Optional | `https://your-app-name.onrender.com` |

*Note: If Twilio environment variables are unconfigured, SMS dispatch logs an error, while `start_verification` outputs generated OTPs to the server console for testing.*

## 7. Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bhuvanesproengineer/kapture-maya-voice-agent.git
   cd kapture-maya-voice-agent
   ```

2. **Navigate to backend directory**:
   ```bash
   cd maya-backend
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**:
   Create a `.env` file inside the `maya-backend/` directory.

5. **Configure required environment variables**:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
   TWILIO_PHONE_NUMBER=+18005550199
   PAYMENT_BASE_URL=http://localhost:5000
   ```

6. **Initialize Database and Seed Data**:
   ```bash
   python database/init_db.py
   ```

## 8. Running the Backend

* **Development Server**:
  ```bash
  python app.py
  ```
  Runs the Flask development server on `http://0.0.0.0:5000` with `debug=True`.

* **Production Server**:
  ```bash
  gunicorn app:app --bind 0.0.0.0:5000
  ```

* **Application Port**: `5000`

## 9. API Documentation

| Method | Endpoint | Purpose | Authentication | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/` | System health check | None | None | `{"message": "...", "status": "ok"}` |
| `GET` | `/api/health` | System health check | None | None | `{"message": "...", "status": "ok"}` |
| `POST` | `/api/check-customer` | Identify customer by phone number | None | `{"phone": "8500197653"}` | `{"customer_found": true, "customer_id": "CUST001", "customer_name": "Rahul Sharma", ...}` |
| `POST` | `/api/send-otp` | Generate OTP and send via Twilio SMS | None | `{"phone": "8500197653"}` | `{"otp_sent": true, "verification_id": "VER001"}` |
| `POST` | `/api/verify-otp` | Validate 4-digit OTP against session | Verification ID | `{"verification_id": "VER001", "otp": "6346"}` | `{"verified": true, "customer_id": "CUST001", "account_id": "ACC001"}` |
| `POST` | `/api/get-account-details` | Fetch customer loan account details | Verified Session (`verified=1`) | `{"verification_id": "VER001"}` | `{"success": true, "customer": {...}, "account": {...}}` |
| `POST` | `/api/verify-customer` | 2-Stage Verification (Start/Verify) | None | `{"phone": "..."}` OR `{"verification_id": "...", "otp": "..."}` | `{"customer_found": true, ...}` OR `{"verified": true, ...}` |
| `POST` | `/api/log-promise-to-pay` | Log customer Promise-to-Pay (PTP) | None | `{"account_id": "ACC001", "amount": 8499, "ptp_date": "2026-08-20"}` | `{"success": true, "reference": "PTP001"}` |
| `POST` | `/api/send-payment-link` | Generate & send payment link via SMS | None | `{"account_id": "ACC001", "phone": "8500197653"}` | `{"success": true, "link": "...", "sms_sent": true}` |
| `GET` | `/payment/<account_id>` | Render demo payment portal UI | None | None | HTML Web Page |
| `POST` | `/payment/<account_id>/pay` | Process demo payment simulation | None | Form Submit | 302 Redirect to `/payment/<account_id>` |
| `POST` | `/api/mark-disposition` | Record call intent & outcome | None | `{"account_id": "ACC001", "intent": "WILL_PAY", "outcome": "PTP_CREATED"}` | `{"success": true, "disposition_id": "DISP001"}` |
| `POST` | `/api/escalate-to-agent` | Create agent escalation ticket | None | `{"account_id": "ACC001", "reason": "CUSTOMER_DISPUTE"}` | `{"success": true, "ticket_id": "ESC001"}` |
| `GET` | `/api/customer-status/<account_id>` | Read-only aggregated status lookup | None | None | `{"success": true, "customer": {...}, "account": {...}, ...}` |

### Request and Response Examples

#### 1. Check Customer (`POST /api/check-customer`)
* **Request**:
  ```json
  {
    "phone": "8500197653",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "customer_found": true,
    "customer_id": "CUST001",
    "customer_name": "Rahul Sharma",
    "phone": "8500197653",
    "calling_phone": "+918500197653"
  }
  ```

#### 2. Send OTP (`POST /api/send-otp`)
* **Request**:
  ```json
  {
    "phone": "8500197653",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "otp_sent": true,
    "verification_id": "VER001"
  }
  ```

#### 3. Verify OTP (`POST /api/verify-otp`)
* **Request**:
  ```json
  {
    "verification_id": "VER001",
    "otp": "6346",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "verified": true,
    "customer_id": "CUST001",
    "account_id": "ACC001"
  }
  ```

#### 4. Get Account Details (`POST /api/get-account-details`)
* **Request**:
  ```json
  {
    "verification_id": "VER001",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "customer": {
      "name": "Rahul Sharma"
    },
    "account": {
      "account_id": "ACC001",
      "loan_type": "Personal Loan",
      "overdue_amount": 8499.0,
      "days_past_due": 12,
      "payment_status": "PENDING"
    }
  }
  ```

#### 5. Log Promise to Pay (`POST /api/log-promise-to-pay`)
* **Request**:
  ```json
  {
    "account_id": "ACC001",
    "amount": 8499.0,
    "ptp_date": "2026-08-20",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "reference": "PTP001"
  }
  ```

#### 6. Send Payment Link (`POST /api/send-payment-link`)
* **Request**:
  ```json
  {
    "account_id": "ACC001",
    "phone": "8500197653",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "account_id": "ACC001",
    "link": "http://localhost:5000/payment/ACC001",
    "sms_sent": true
  }
  ```

#### 7. Mark Disposition (`POST /api/mark-disposition`)
* **Request**:
  ```json
  {
    "account_id": "ACC001",
    "intent": "WILL_PAY",
    "outcome": "PTP_CREATED",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "disposition_id": "DISP001"
  }
  ```

#### 8. Escalate to Agent (`POST /api/escalate-to-agent`)
* **Request**:
  ```json
  {
    "account_id": "ACC001",
    "reason": "CUSTOMER_DISPUTE",
    "call_id": "call_abc123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "ticket_id": "ESC001"
  }
  ```

## 10. Voice Call Flow

1. **Call Initiated & Customer Identification**:
   * Incoming/outbound voice call managed by Vapi voice agent.
   * Vapi calls `POST /api/check-customer` with caller phone number.
   * Backend normalizes phone number and confirms customer identity.
2. **Identity Verification (OTP Flow)**:
   * Voice agent initiates verification via `POST /api/send-otp`.
   * Backend generates 4-digit OTP, stores session in `otp_sessions`, and dispatches Twilio SMS.
   * Customer recites OTP; voice agent sends code to `POST /api/verify-otp`.
   * Backend performs constant-time validation (`secrets.compare_digest`) and sets session `verified = 1`.
3. **Account Information Presentation**:
   * Voice agent requests financial details via `POST /api/get-account-details` passing `verification_id`.
   * Backend checks that `verified == 1` and returns overdue balance, loan type, and days past due.
4. **Resolution Branching**:
   * **Promise to Pay**: Agent posts commitment details to `POST /api/log-promise-to-pay`; backend stores record in `payment_promises` and returns `PTP001`.
   * **Payment Link Dispatch**: Agent requests link via `POST /api/send-payment-link`; backend generates link and dispatches Twilio SMS. Customer completes demo payment.
   * **Escalation**: Agent logs escalation via `POST /api/escalate-to-agent`; backend creates ticket `ESC001` in `escalations` table.
5. **Call Disposition & Completion**:
   * Voice agent logs call intent and outcome via `POST /api/mark-disposition`.
   * Backend saves record in `call_dispositions` and completes interaction logging.

## 11. Authentication & Security

* **Authentication**: Session-based verification via `otp_sessions`. Access to loan details via `POST /api/get-account-details` strictly validates that `verified == 1` (returns HTTP 403 Forbidden if unverified).
* **Authorization**: Tool-calling API endpoints rely on verification session tokens (`verification_id`) to isolate financial data.
* **API Key Handling**: Twilio credentials (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`) are loaded securely from environment variables using `python-dotenv`.
* **Environment Variables**: `.env` file is excluded from version control via `.gitignore`.
* **Input Validation**: Phone input is normalized (extracting 10-digit clean numbers and removing country codes `+91`/`91`/`0`). OTP payloads are format-checked (4-digit numeric). PTP amounts are verified positive numbers.
* **Timing Attack Prevention**: OTP comparison uses `secrets.compare_digest(clean_otp, stored_otp)` for constant-time evaluation.
* **Session Expiry & Rate Limiting**: OTP sessions expire after 5 minutes (`OTP_EXPIRY_MINUTES = 5`). Attempts are capped at 3 (`MAX_ATTEMPTS = 3`); exceeded attempts block the session.
* **Sensitive Data Redaction**: The logger utility (`utils/logger.py`) automatically strips sensitive keys (`otp`, `auth_token`, `password`, `secret`) from log details.

## 12. Database

* **Database Technology**: SQLite 3 (`database/database.db`) configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and `busy_timeout=30000`.
* **Database Connection**: Connection helper function with `row_factory = sqlite3.Row`.
* **Tables and Schema**:
  * `customers`: `customer_id` (PK, TEXT), `name` (TEXT), `phone` (TEXT UNIQUE), `account_id` (TEXT)
  * `loans`: `account_id` (PK, TEXT), `customer_id` (FK), `loan_type` (TEXT), `overdue_amount` (REAL), `days_past_due` (INTEGER)
  * `loan_accounts`: `account_id` (PK, TEXT), `customer_id` (FK), `loan_type` (TEXT), `overdue_amount` (REAL), `days_past_due` (INTEGER), `payment_status` (TEXT DEFAULT 'PENDING')
  * `otp_sessions`: `id` (PK AUTOINCREMENT), `verification_id` (TEXT UNIQUE), `customer_id` (FK), `phone` (TEXT), `otp` (TEXT), `attempts` (INTEGER), `expires_at` (TEXT ISO), `verified` (INTEGER 0/1)
  * `payment_promises`: `id` (PK AUTOINCREMENT), `account_id` (TEXT), `amount` (REAL), `ptp_date` (TEXT), `created_at` (TEXT ISO)
  * `payments`: `id` (PK AUTOINCREMENT), `account_id` (TEXT), `amount` (REAL), `status` (TEXT), `payment_method` (TEXT DEFAULT 'DEMO_PAYMENT'), `paid_at` (TEXT ISO)
  * `call_dispositions`: `id` (PK AUTOINCREMENT), `account_id` (TEXT), `intent` (TEXT), `outcome` (TEXT), `call_id` (TEXT), `created_at` (TEXT ISO)
  * `escalations`: `id` (PK AUTOINCREMENT), `account_id` (TEXT), `reason` (TEXT), `ticket_id` (TEXT), `call_id` (TEXT), `created_at` (TEXT ISO)
* **Seeded Test Accounts**:
  * `CUST001` — Rahul Sharma (Phone: `8500197653`, Account: `ACC001`, Overdue: ₹8,499.00, DPD: 12)
  * `CUST002` — Priya Reddy (Phone: `6302465126`, Account: `ACC002`, Overdue: ₹6,500.00, DPD: 15)

## 13. External Services & Integrations

* **Twilio SMS API** (`twilio.rest.Client`): Used by `send_otp_to_customer` and `send_payment_link` to send SMS messages to customer mobile numbers formatted as `+91XXXXXXXXXX`. Communicates via HTTP POST requests authenticated with `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`.
* **Vapi Voice AI Platform**: Integrates with the backend by sending custom tool HTTP POST requests to `/api/*` endpoints during live voice calls.

## 14. Error Handling & Logging

* **Error Handling**: Standardized HTTP error handlers in `app.py`:
  * `400 Bad Request`: `{"error": "BAD_REQUEST", "message": "..."}`
  * `404 Not Found`: `{"error": "NOT_FOUND", "message": "The requested endpoint or resource was not found."}`
  * `500 Internal Server Error`: `{"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}`
* **Validation**: Input payload checks across routes and services for missing fields, malformed phone numbers, invalid OTP formats, and zero/negative payment amounts.
* **Logging**: Configured via `utils/logger.py` with timestamped formatting `[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s`. Offers `log_api_call` and `log_error` methods with automatic key sanitization.
* **Voice-Call Failure Handling**: Structured error responses containing machine-readable reason strings (`PHONE_REQUIRED`, `CUSTOMER_NOT_FOUND`, `OTP_DELIVERY_FAILED`, `MAX_ATTEMPTS_EXCEEDED`, `CUSTOMER_NOT_VERIFIED`) allowing the Vapi voice agent to deliver natural language fallback prompts. Automatically cleans up failed OTP sessions upon SMS delivery failures.

## 15. Deployment

* **Backend Hosting**: Configured for WSGI deployment (e.g. Render, Heroku) via `gunicorn`. Fallback host URL configured in code: `https://kapture-maya-voice-agent.onrender.com`.
* **Required Environment Variables**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `PAYMENT_BASE_URL` (or `BASE_URL`).
* **Build and Start Commands**:
  * Dependencies: `pip install -r requirements.txt`
  * Database Initialization: `python database/init_db.py`
  * Start Server: `gunicorn app:app --bind 0.0.0.0:5000`
* **Production Configuration**: CORS enabled for external tool origin access, SQLite configured with WAL mode (`PRAGMA journal_mode=WAL`) and 30-second connection timeout for concurrent operations.

## 16. Testing

* **Automated Tests**: Not implemented in the current codebase (no `unittest` or `pytest` automated test suite files exist).
* **Manual / Integration Testing Methods**:
  * **Read-only Aggregation API**: Endpoint `GET /api/customer-status/<account_id>` (e.g., `/api/customer-status/ACC001`) returns unified customer details, loan balance, latest PTP, payment, disposition, and escalation records.
  * **Interactive Demo Payment Portal**: Web interface at `GET /payment/<account_id>` and `POST /payment/<account_id>/pay` to test payment state updates.
  * **Server Console Log Inspection**: `start_verification` logs generated OTPs to the stdout console for testing without live SMS dispatch.
  * **REST Client Testing**: API testing via Postman or cURL targeting endpoints (`/api/check-customer`, `/api/send-otp`, `/api/verify-otp`, `/api/get-account-details`).

## 17. Known Limitations

* **Single-File SQLite Database**: Uses a local SQLite file (`database.db`), which is effective for prototypes but not designed for multi-region horizontal scaling or high concurrent write throughput.
* **Tool Session Authorization**: Endpoint authorization relies on `verification_id` lookup without JWT signatures or HTTP Bearer tokens.
* **Mock Payment Gateway**: Payment portal is a prototype demo page that updates database records to `PAID` without processing real credit card or UPI transactions through a payment aggregator.
* **Lack of Automated Test Suite**: Codebase does not currently include unit or integration test coverage scripts.

## 18. Future Improvements

* **Real Payment Aggregator Integration**: Connect Razorpay or Stripe API webhooks to process real financial transactions.
* **Vapi Request Signature Verification**: Validate Vapi webhook header signatures to restrict API access exclusively to verified Vapi voice servers.
* **Database Migration to PostgreSQL**: Replace local SQLite with managed PostgreSQL for enterprise multi-node deployment.
* **Automated Test Suite**: Implement `pytest` test cases covering route handlers, business logic services, and database utility functions.
* **Redis Session Store**: Migrate OTP session storage to Redis for fast in-memory expiration and distributed locking.

## 19. API / Developer Notes

* **Phone Number Handling**: Pass phone inputs as 10-digit numbers or international strings (e.g. `+918500197653`). `utils/phone.py` automatically strips country code `+91`/`91` and leading zeroes `0`.
* **Call ID Context**: Pass an optional `call_id` parameter in API request bodies to correlate log traces with Vapi voice session IDs.
* **Twilio Fallback Behavior**: Omitting Twilio credentials causes `send-otp` to return HTTP 500 `OTP_DELIVERY_FAILED` while `verify-customer` outputs the generated OTP to the server console log for local development.
* **Database Setup**: Execute `python database/init_db.py` before running the application to set up database schemas and populate seed customer records (`CUST001` and `CUST002`).

## 20. License

No license has currently been specified in the repository.
