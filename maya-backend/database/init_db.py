import sqlite3
import os

# Define database file path relative to this script's directory
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

    # 3. Create loan_accounts table (Module — Customer Account Details)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loan_accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            loan_type TEXT NOT NULL,
            overdue_amount REAL NOT NULL,
            days_past_due INTEGER NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    ''')

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

    # 6. Create call_dispositions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS call_dispositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            intent TEXT NOT NULL,
            outcome TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # 7. Create escalations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Seed mock customer data
    cursor.execute('''
        INSERT OR REPLACE INTO customers (customer_id, name, phone, account_id)
        VALUES (?, ?, ?, ?)
    ''', ('CUST001', 'Rahul Sharma', '8500197653', 'ACC001'))

    # Seed mock loan data
    cursor.execute('''
        INSERT OR REPLACE INTO loans (account_id, customer_id, loan_type, overdue_amount, days_past_due)
        VALUES (?, ?, ?, ?, ?)
    ''', ('ACC001', 'CUST001', 'Personal Loan', 8499.0, 12))

    # Seed mock loan_accounts data
    cursor.execute('''
        INSERT OR REPLACE INTO loan_accounts (account_id, customer_id, loan_type, overdue_amount, days_past_due)
        VALUES (?, ?, ?, ?, ?)
    ''', ('ACC001', 'CUST001', 'Personal Loan', 8499.0, 12))

    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at: {DB_PATH}")
    print("Seeded customer: CUST001 (Rahul Sharma, Phone: 8500197653, Account: ACC001)")
    print("Seeded loan_accounts: ACC001 (Personal Loan, Overdue: 8499, DPD: 12)")


if __name__ == '__main__':
    init_db()
