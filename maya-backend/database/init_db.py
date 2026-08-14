import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def init_db():
    """
    Initialize SQLite database and set up schemas required for Maya collections backend.
    """
    os.makedirs(BASE_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            account_id TEXT NOT NULL
        )
    ''')

    # 2. Create loans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            loan_type TEXT,
            overdue_amount REAL,
            days_past_due INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    ''')

    # 3. Create loan_accounts table (with payment_status)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loan_accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            loan_type TEXT NOT NULL,
            overdue_amount REAL NOT NULL,
            days_past_due INTEGER NOT NULL,
            payment_status TEXT DEFAULT 'PENDING',
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    ''')

    # Safely add payment_status if table previously existed without it
    try:
        cursor.execute("ALTER TABLE loan_accounts ADD COLUMN payment_status TEXT DEFAULT 'PENDING'")
    except sqlite3.OperationalError:
        pass

    # 4. Create otp_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verification_id TEXT UNIQUE NOT NULL,
            customer_id TEXT NOT NULL,
            phone TEXT NOT NULL,
            otp TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            expires_at TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    ''')

    # 5. Create payment_promises table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_promises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            amount REAL NOT NULL,
            ptp_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # 6. Create payments table (Demo Payments)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            payment_method TEXT DEFAULT 'DEMO_PAYMENT',
            paid_at TEXT NOT NULL
        )
    ''')

    # 7. Create call_dispositions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS call_dispositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            intent TEXT NOT NULL,
            outcome TEXT NOT NULL,
            call_id TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    try:
        cursor.execute("ALTER TABLE call_dispositions ADD COLUMN call_id TEXT")
    except sqlite3.OperationalError:
        pass

    # 8. Create escalations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            call_id TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    try:
        cursor.execute("ALTER TABLE escalations ADD COLUMN call_id TEXT")
    except sqlite3.OperationalError:
        pass

    # Seed Customer 1 (CUST001 - Rahul Sharma)
    cursor.execute('''
        INSERT OR REPLACE INTO customers (customer_id, name, phone, account_id)
        VALUES (?, ?, ?, ?)
    ''', ('CUST001', 'Rahul Sharma', '8500197653', 'ACC001'))

    cursor.execute('''
        INSERT OR REPLACE INTO loans (account_id, customer_id, loan_type, overdue_amount, days_past_due)
        VALUES (?, ?, ?, ?, ?)
    ''', ('ACC001', 'CUST001', 'Personal Loan', 8499.0, 12))

    cursor.execute('''
        INSERT OR REPLACE INTO loan_accounts (account_id, customer_id, loan_type, overdue_amount, days_past_due, payment_status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('ACC001', 'CUST001', 'Personal Loan', 8499.0, 12, 'PENDING'))

    # Seed Customer 2 (CUST002 - Priya Reddy)
    cursor.execute('''
        INSERT OR REPLACE INTO customers (customer_id, name, phone, account_id)
        VALUES (?, ?, ?, ?)
    ''', ('CUST002', 'Priya Reddy', '6302465126', 'ACC002'))

    cursor.execute('''
        INSERT OR REPLACE INTO loans (account_id, customer_id, loan_type, overdue_amount, days_past_due)
        VALUES (?, ?, ?, ?, ?)
    ''', ('ACC002', 'CUST002', 'Personal Loan', 6500.0, 15))

    cursor.execute('''
        INSERT OR REPLACE INTO loan_accounts (account_id, customer_id, loan_type, overdue_amount, days_past_due, payment_status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('ACC002', 'CUST002', 'Personal Loan', 6500.0, 15, 'PENDING'))

    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at: {DB_PATH}")
    print("Seeded CUST001: Rahul Sharma (Phone: 8500197653, Account: ACC001, Overdue: 8499, DPD: 12, Status: PENDING)")
    print("Seeded CUST002: Priya Reddy (Phone: 6302465126, Account: ACC002, Overdue: 6500, DPD: 15, Status: PENDING)")

if __name__ == '__main__':
    init_db()
