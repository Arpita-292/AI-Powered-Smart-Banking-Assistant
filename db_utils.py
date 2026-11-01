import sqlite3
import os
import random
import re

DB_NAME = os.path.join(os.path.dirname(__file__), 'siri_bank.db')

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create tables with is_admin field
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id VARCHAR(20) UNIQUE NOT NULL,
        phone_number VARCHAR(15) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        preferred_language VARCHAR(20) DEFAULT 'English',
        upi_id VARCHAR(50) UNIQUE,
        aadhaar_number VARCHAR(20) UNIQUE,
        email VARCHAR(100),
        profile_photo TEXT,
        id_proof TEXT,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        rejection_reason TEXT,
        is_admin BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        account_number VARCHAR(20) UNIQUE NOT NULL,
        balance DECIMAL(15, 2) DEFAULT 0.00,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        request_type VARCHAR(50) NOT NULL,
        request_details TEXT,
        status VARCHAR(20) DEFAULT 'PENDING',
        rejection_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        amount DECIMAL(15, 2) NOT NULL,
        transaction_type VARCHAR(20) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount DECIMAL(15, 2) NOT NULL,
        purpose TEXT,
        status VARCHAR(20) DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS standing_instructions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        receiver_account VARCHAR(20) NOT NULL,
        amount DECIMAL(15, 2) NOT NULL,
        day_of_month INTEGER NOT NULL,
        last_executed TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')
    
    # Migration: Check if upi_id exists, add if not
    try:
        cursor.execute("SELECT upi_id FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN upi_id VARCHAR(50)")
        # Optionally populate existing users if they have none
        cursor.execute("SELECT id, full_name FROM users")
        users = cursor.fetchall()
        for u in users:
            # u[0] is id, u[1] is full_name
            upi = f"{u[1].split()[0].lower()}{u[0]}@siri"
            cursor.execute("UPDATE users SET upi_id = ? WHERE id = ?", (upi, u[0]))

    # Migration: Check if aadhaar_number exists, add if not
    try:
        cursor.execute("SELECT aadhaar_number FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN aadhaar_number VARCHAR(20)")

    # Migration: Check if rejection_reason exists in requests, add if not
    try:
        cursor.execute("SELECT rejection_reason FROM requests LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE requests ADD COLUMN rejection_reason TEXT")

    # Migration: Check if status exists in users, add if not
    try:
        cursor.execute("SELECT status FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE'")
        cursor.execute("UPDATE users SET status = 'ACTIVE' WHERE status IS NULL")

    # Migration: Check if email exists in users, add if not
    try:
        cursor.execute("SELECT email FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100)")

    # Migration: Check if profile_photo exists in users, add if not
    try:
        cursor.execute("SELECT profile_photo FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")

    # Migration: Check if id_proof exists in users, add if not
    try:
        cursor.execute("SELECT id_proof FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN id_proof TEXT")

    # Migration: Set default users password to '123456'
    cursor.execute("UPDATE users SET password_hash = '123456' WHERE is_admin = 0 AND (password_hash = 'password123' OR customer_id IN ('CUST1001', 'CUST1002', 'CUST1003', 'CUST1004'))")
    
    # Check if dummy data exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Create Admin
        cursor.execute('''
        INSERT INTO users (customer_id, phone_number, password_hash, full_name, is_admin, upi_id) 
        VALUES ('ADMIN001', '0000000000', 'admin123', 'System Administrator', 1, 'admin@siri')
        ''')
        admin_id = cursor.lastrowid
        
        # Create Dummy Account for system deposits/withdrawals tracking (optional, using admin ID)
        cursor.execute('''
        INSERT INTO accounts (user_id, account_number, balance, status)
        VALUES (?, 'SYSTEM000', 999999999.00, 'ACTIVE')
        ''', (admin_id,))
        
        # Create 4 dummy users
        names = ["Arpitha", "Chaithanya", "Harshitha", "Jyothi"]
                 
        for i in range(4):
            customer_id = f"CUST100{i+1}"
            phone = f"987654321{i}"
            name = names[i]
            upi = f"{name.split()[0].lower()}{i+1}@siri"
            aadhaar = f"12345678900{i+1}"
            # insert user
            cursor.execute('''
            INSERT INTO users (customer_id, phone_number, password_hash, full_name, preferred_language, upi_id, aadhaar_number)
            VALUES (?, ?, '123456', ?, 'English', ?, ?)
            ''', (customer_id, phone, name, upi, aadhaar))
            user_id = cursor.lastrowid
            
            # insert account
            acc_num = f"ACC{80000 + i}"
            balance = round(random.uniform(5000, 150000), 2)
            cursor.execute('''
            INSERT INTO accounts (user_id, account_number, balance, status)
            VALUES (?, ?, ?, 'ACTIVE')
            ''', (user_id, acc_num, balance))
            pass
        
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as err:
        print(f"Error connecting to DB: {err}")
        return None

def authenticate_user(identifier, password):
    conn = get_db_connection()
    if not conn:
        return None, "Database error"
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, customer_id, full_name, preferred_language, phone_number, is_admin, status, rejection_reason
        FROM users 
        WHERE (phone_number = ? OR customer_id = ? OR aadhaar_number = ?) AND password_hash = ?
    """, (identifier, identifier, identifier, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        u_dict = dict(user)
        u_status = u_dict.get('status', 'ACTIVE')
        if u_status == 'PENDING':
            return None, "PENDING: Your registration is currently pending admin approval."
        elif u_status == 'REJECTED':
            reason = u_dict.get('rejection_reason') or "Details could not be verified by bank."
            return None, f"REJECTED: Your registration was rejected: {reason}"
        return u_dict, "Success"
    return None, "Invalid credentials"

def get_user_account_summary(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT account_number, balance, status FROM accounts WHERE user_id = ?", (user_id,))
    accounts = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, full_name, customer_id, upi_id, aadhaar_number, phone_number, email, profile_photo, id_proof, status, rejection_reason FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    user_info = dict(user_row) if user_row else {}

    cursor.execute("SELECT id, request_type, request_details, status, rejection_reason, created_at FROM requests WHERE user_id = ? ORDER BY created_at DESC, id DESC", (user_id,))
    requests = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT id, amount, purpose, status, created_at FROM loans WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    loans = [dict(row) for row in cursor.fetchall()]

    cursor.execute('''
        SELECT 
            t.id, t.amount, t.transaction_type, t.description, t.created_at,
            t.sender_id, t.receiver_id,
            su.full_name as sender_name, ru.full_name as receiver_name
        FROM transactions t
        LEFT JOIN users su ON t.sender_id = su.id
        LEFT JOIN users ru ON t.receiver_id = ru.id
        WHERE t.sender_id = ? OR t.receiver_id = ?
        ORDER BY t.created_at DESC LIMIT 100
    ''', (user_id, user_id))
    transactions = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return {"accounts": accounts, "recent_requests": requests, "loans": loans, "transactions": transactions, "user": user_info}

def execute_transfer(sender_id, receiver_account_num, amount):
    conn = get_db_connection()
    if not conn: return False, "Database error"
    
    receiver_account_num = str(receiver_account_num).strip().upper()
    
    if amount <= 0:
        return False, "Transfer amount must be greater than zero."
        
    try:
        cursor = conn.cursor()
        # 1. Fetch sender account details and email
        cursor.execute("""
            SELECT a.id, a.account_number, a.balance, a.status, u.full_name, u.email 
            FROM accounts a
            JOIN users u ON u.id = a.user_id
            WHERE a.user_id = ?
        """, (sender_id,))
        sender_acc = cursor.fetchone()
        
        if not sender_acc: return False, "Sender account not found."
        if sender_acc['status'] != 'ACTIVE': return False, f"Sender account is {sender_acc['status'].lower()}."
        if sender_acc['balance'] < amount: return False, "Insufficient funds."
        
        # Edge Case: Prevent sending to self
        if sender_acc['account_number'] == receiver_account_num:
            return False, "Cannot transfer funds to the same account."
            
        # 2. Fetch receiver account details and email
        cursor.execute("""
            SELECT a.id, a.user_id, a.account_number, a.balance, a.status, u.full_name, u.email 
            FROM accounts a
            JOIN users u ON u.id = a.user_id
            WHERE a.account_number = ?
        """, (receiver_account_num,))
        recv_acc = cursor.fetchone()
        
        if not recv_acc: return False, "Invalid payee account number."
        if recv_acc['status'] != 'ACTIVE': return False, "Receiver account is currently inactive."
        
        # 3. Deduct from sender
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, sender_acc['id']))
        # 4. Add to receiver
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, recv_acc['id']))
        
        # 5. Log transaction
        cursor.execute('''
            INSERT INTO transactions (sender_id, receiver_id, amount, transaction_type, description)
            VALUES (?, ?, ?, 'TRANSFER', 'Fund transfer via QuickPay')
        ''', (sender_id, recv_acc['user_id'], amount))
        
        conn.commit()

        # Send Real-Time Transaction Emails
        try:
            from email_service import send_transaction_email
            sender_new_bal = float(sender_acc['balance']) - float(amount)
            recv_new_bal = float(recv_acc['balance']) + float(amount)
            if sender_acc['email']:
                send_transaction_email(
                    to_email=sender_acc['email'],
                    full_name=sender_acc['full_name'],
                    tx_type='DEBIT',
                    amount=amount,
                    balance=sender_new_bal,
                    counterpart_info=f"{recv_acc['full_name']} ({receiver_account_num})",
                    description="Fund transfer via QuickPay"
                )
            if recv_acc['email']:
                send_transaction_email(
                    to_email=recv_acc['email'],
                    full_name=recv_acc['full_name'],
                    tx_type='CREDIT',
                    amount=amount,
                    balance=recv_new_bal,
                    counterpart_info=f"{sender_acc['full_name']} ({sender_acc['account_number']})",
                    description="Fund transfer received"
                )
        except Exception as mail_err:
            print(f"[Email Error in transfer]: {mail_err}")

        return True, "Transfer successful"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def create_new_user(full_name, phone, initial_deposit=0, aadhaar_number=None):
    conn = get_db_connection()
    if not conn: return False, "Database error"
    
    try:
        cursor = conn.cursor()
        
        # Generate predictable customer id (max existing + 1)
        cursor.execute("SELECT COUNT(id) FROM users")
        count = cursor.fetchone()[0]
        customer_id = f"CUST10{str(count + 10).zfill(2)}"
        
        cursor.execute('''
            INSERT INTO users (customer_id, phone_number, password_hash, full_name, preferred_language, aadhaar_number)
            VALUES (?, ?, '123456', ?, 'English', ?)
        ''', (customer_id, phone, full_name, aadhaar_number))
        
        user_id = cursor.lastrowid
        acc_num = f"ACC{80000 + count + 10}"
        
        cursor.execute('''
            INSERT INTO accounts (user_id, account_number, balance, status)
            VALUES (?, ?, ?, 'ACTIVE')
        ''', (user_id, acc_num, initial_deposit))
        
        if initial_deposit > 0:
            cursor.execute('''
            INSERT INTO transactions (receiver_id, amount, transaction_type, description)
            VALUES (?, ?, 'DEPOSIT', 'Account Opening Deposit')
            ''', (user_id, initial_deposit))
            
        conn.commit()
        return True, "Account created successfully"
    except sqlite3.IntegrityError:
        return False, "Phone number, ID, or Aadhaar already registered"
    finally:
        conn.close()

def admin_execute_financial_op(account_number, ifsc_code, op_type, amount, narration):
    conn = get_db_connection()
    if not conn: return False, "Database error"
    
    account_number = str(account_number).strip().upper()
    ifsc_code = str(ifsc_code).strip().upper()
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.user_id, a.balance, u.full_name, u.email 
            FROM accounts a
            JOIN users u ON u.id = a.user_id
            WHERE a.account_number = ?
        """, (account_number,))
        acc = cursor.fetchone()
        if not acc: return False, "Target Bank Account not found"
        
        user_id = acc['user_id']
        desc = f"Teller {op_type.capitalize()} - {narration} (IFSC: {ifsc_code})"
        new_balance = float(acc['balance']) + (amount if op_type == 'deposit' else -amount)
        
        if op_type == 'withdraw':
            if acc['balance'] < amount: return False, "Insufficient funds"
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, acc['id']))
            cursor.execute('''
            INSERT INTO transactions (sender_id, amount, transaction_type, description)
            VALUES (?, ?, 'WITHDRAWAL', ?)
            ''', (user_id, amount, desc))
        else: # deposit
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, acc['id']))
            cursor.execute('''
            INSERT INTO transactions (receiver_id, amount, transaction_type, description)
            VALUES (?, ?, 'DEPOSIT', ?)
            ''', (user_id, amount, desc))
            
        conn.commit()
        txn_id = cursor.lastrowid

        # Send Teller Transaction Email
        try:
            from email_service import send_transaction_email
            if acc['email']:
                send_transaction_email(
                    to_email=acc['email'],
                    full_name=acc['full_name'],
                    tx_type='DEPOSIT' if op_type == 'deposit' else 'WITHDRAWAL',
                    amount=amount,
                    balance=new_balance,
                    counterpart_info=f"SIRI BANK Branch Teller ({ifsc_code})",
                    description=desc
                )
        except Exception as mail_err:
            print(f"[Email Error in teller op]: {mail_err}")

        return True, {"msg": "Operation successful", "txn_id": f"TXN-{txn_id}", "balance": new_balance}
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def create_bank_request(user_id, request_type, request_details, status='PENDING', rejection_reason=None):
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    cursor.execute("INSERT INTO requests (user_id, request_type, request_details, status, rejection_reason) VALUES (?, ?, ?, ?, ?)",
                   (user_id, request_type, request_details, status, rejection_reason))
    conn.commit()
    req_id = cursor.lastrowid

    # Send Notification Email for Card or KYC Request (PENDING)
    try:
        cursor.execute("SELECT full_name, email, aadhaar_number FROM users WHERE id = ?", (user_id,))
        u = cursor.fetchone()
        if u and u['email'] and status == 'PENDING':
            from email_service import send_card_application_received_email, send_kyc_submission_received_email
            if request_type == 'ATM_CARD':
                send_card_application_received_email(u['email'], u['full_name'], request_details)
            elif request_type in ['AADHAAR_LINK', 'KYC']:
                send_kyc_submission_received_email(u['email'], u['full_name'], u['aadhaar_number'])
    except Exception as mail_err:
        print(f"[Email Error in create_bank_request]: {mail_err}")

    cursor.close()
    conn.close()
    return req_id > 0

# ADMIN QUERIES
def get_all_users_and_requests():
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.id as req_id, r.user_id, u.customer_id, u.full_name, u.email, u.phone_number,
               u.profile_photo, u.id_proof,
               r.request_type, r.request_details, r.status, r.rejection_reason, r.created_at
        FROM requests r
        JOIN users u ON u.id = r.user_id
        ORDER BY r.created_at DESC, r.id DESC
    """)
    requests = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT u.id, u.customer_id, u.full_name, u.phone_number, u.aadhaar_number, u.email,
               u.profile_photo, u.id_proof,
               u.is_admin, a.account_number, a.balance
        FROM users u
        LEFT JOIN accounts a ON a.user_id = u.id
    """)
    users = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return {"requests": requests, "users": users}

def get_system_analytics():
    conn = get_db_connection()
    if not conn: return {}
    cursor = conn.cursor()
    
    # 1. Total Liquidity
    cursor.execute("SELECT SUM(balance) as total_liquidity FROM accounts WHERE status = 'ACTIVE'")
    row_liq = cursor.fetchone()
    liquidity = row_liq['total_liquidity'] if row_liq and row_liq['total_liquidity'] is not None else 1000000.0
    
    # 2. Transaction Stats by Type
    cursor.execute("SELECT transaction_type, COUNT(*) as count, SUM(amount) as total FROM transactions GROUP BY transaction_type")
    tx_stats = [dict(row) for row in cursor.fetchall()]
    if not tx_stats:
        tx_stats = [
            {"transaction_type": "DEPOSIT", "count": 28, "total": 145000.0},
            {"transaction_type": "TRANSFER", "count": 42, "total": 98500.0},
            {"transaction_type": "WITHDRAWAL", "count": 14, "total": 32000.0}
        ]
    
    # 3. 7-Day Rolling Volume
    import datetime
    today = datetime.date.today()
    dates_7 = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    
    cursor.execute('''
        SELECT DATE(created_at) as tx_date, SUM(amount) as daily_volume 
        FROM transactions 
        GROUP BY DATE(created_at) 
        ORDER BY tx_date DESC LIMIT 7
    ''')
    real_volume_map = {dict(row)['tx_date']: float(dict(row)['daily_volume']) for row in cursor.fetchall()}
    
    # Baseline demo curve if no transactions yet
    base_curve = [42000.0, 68500.0, 53000.0, 89400.0, 74200.0, 95000.0, 115000.0]
    daily_volume = []
    for idx, d_str in enumerate(dates_7):
        day_label = datetime.datetime.strptime(d_str, '%Y-%m-%d').strftime('%a (%d %b)')
        vol = real_volume_map.get(d_str, base_curve[idx % len(base_curve)])
        daily_volume.append({"tx_date": d_str, "label": day_label, "daily_volume": vol})
        
    # 4. KYC Status Breakdown
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM requests 
        WHERE request_type IN ('KYC', 'AADHAAR_LINK', 'AADHAAR') 
        GROUP BY status
    """)
    kyc_rows = {dict(row)['status']: dict(row)['count'] for row in cursor.fetchall()}
    kyc_stats = {
        "APPROVED": kyc_rows.get('APPROVED', 16),
        "PENDING": kyc_rows.get('PENDING', 4),
        "REJECTED": kyc_rows.get('REJECTED', 2)
    }
    
    # 5. Registrations Breakdown from users table
    cursor.execute("SELECT status, COUNT(*) as count FROM users WHERE is_admin = 0 GROUP BY status")
    reg_rows = {dict(row)['status']: dict(row)['count'] for row in cursor.fetchall()}
    reg_stats = {
        "ACTIVE": reg_rows.get('ACTIVE', 4),
        "PENDING": reg_rows.get('PENDING', 0),
        "REJECTED": reg_rows.get('REJECTED', 0)
    }
    
    cursor.close()
    conn.close()
    return {
        "liquidity": float(liquidity),
        "tx_stats": tx_stats,
        "daily_volume": daily_volume,
        "kyc_stats": kyc_stats,
        "reg_stats": reg_stats
    }

def update_request_status(request_id, status, rejection_reason=None):
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()

    # Fetch request and user details for notification
    cursor.execute("""
        SELECT r.id, r.user_id, r.request_type, r.request_details, u.full_name, u.email, u.aadhaar_number
        FROM requests r
        JOIN users u ON u.id = r.user_id
        WHERE r.id = ?
    """, (request_id,))
    req_row = cursor.fetchone()

    clean_reason = (rejection_reason or '').strip()
    if status == 'REJECTED':
        if not clean_reason:
            clean_reason = "Verification rejected by bank administrator."
        cursor.execute("UPDATE requests SET status = ?, rejection_reason = ? WHERE id = ?", (status, clean_reason, request_id))
        # Sync rejection reason to user row
        if req_row and req_row['request_type'] in ['AADHAAR_LINK', 'KYC']:
            cursor.execute("UPDATE users SET rejection_reason = ? WHERE id = ?", (clean_reason, req_row['user_id']))
    else:
        cursor.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
        if status == 'APPROVED' and req_row and req_row['request_type'] in ['AADHAAR_LINK', 'KYC']:
            cursor.execute("UPDATE users SET rejection_reason = NULL WHERE id = ?", (req_row['user_id'],))
            
    conn.commit()

    # Send Notification Email on Approval or Rejection
    if req_row and req_row['email']:
        try:
            from email_service import (
                send_card_approval_email, send_card_rejection_email,
                send_kyc_approval_email, send_kyc_rejection_email
            )
            rtype = req_row['request_type']
            u_email = req_row['email']
            u_name = req_row['full_name']
            r_details = req_row['request_details'] or "Standard Request"

            if status == 'APPROVED':
                if rtype == 'ATM_CARD':
                    send_card_approval_email(u_email, u_name, r_details)
                elif rtype in ['AADHAAR_LINK', 'KYC']:
                    send_kyc_approval_email(u_email, u_name)
            elif status == 'REJECTED':
                if rtype == 'ATM_CARD':
                    send_card_rejection_email(u_email, u_name, clean_reason)
                elif rtype in ['AADHAAR_LINK', 'KYC']:
                    send_kyc_rejection_email(u_email, u_name, clean_reason)
        except Exception as mail_err:
            print(f"[Email Error in update_request_status]: {mail_err}")

    conn.close()
    return True

def apply_for_loan(user_id, amount, purpose):
    conn = get_db_connection()
    if not conn: return False, "Database error"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO loans (user_id, amount, purpose) VALUES (?, ?, ?)", (user_id, amount, purpose))
        conn.commit()
        return True, "Loan application submitted. Under review."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_all_loans():
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.id, u.customer_id, u.full_name, l.amount, l.purpose, l.status, l.created_at
            FROM loans l
            JOIN users u ON u.id = l.user_id
            ORDER BY l.created_at DESC
        """)
        loans = [dict(row) for row in cursor.fetchall()]
        return loans
    finally:
        conn.close()

def admin_process_loan(loan_id, action):
    conn = get_db_connection()
    if not conn: return False, "Database error"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
        loan = cursor.fetchone()
        if not loan or loan['status'] != 'PENDING':
            return False, "Loan not found or already processed"
            
        cursor.execute("UPDATE loans SET status = ? WHERE id = ?", (action, loan_id))
        
        if action == 'APPROVED':
            user_id = loan['user_id']
            amount = loan['amount']
            cursor.execute("SELECT id FROM accounts WHERE user_id = ?", (user_id,))
            acc = cursor.fetchone()
            if acc:
                cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, acc['id']))
                cursor.execute("""
                    INSERT INTO transactions (sender_id, receiver_id, amount, transaction_type, description)
                    VALUES (NULL, ?, ?, 'DEPOSIT', 'LOAN DISBURSEMENT - ' || ?)
                """, (user_id, amount, loan['purpose']))
        
        conn.commit()
        return True, f"Loan {action.lower()} successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def save_standing_instruction(user_id, receiver_account, amount, day_of_month):
    conn = get_db_connection()
    if not conn: return False, "Database error"
    
    receiver_account = str(receiver_account).strip().upper()
    try:
        amount = float(amount)
        day_of_month = int(day_of_month)
    except Exception: return False, "Invalid input formats"

    if amount <= 0: return False, "Amount must be greater than zero."
    if day_of_month < 1 or day_of_month > 28: return False, "Execution day must be between 1 and 28."
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (receiver_account,))
        if not cursor.fetchone(): return False, "Invalid payee account number."
        
        cursor.execute("""
            INSERT INTO standing_instructions (user_id, receiver_account, amount, day_of_month)
            VALUES (?, ?, ?, ?)
        """, (user_id, receiver_account, amount, day_of_month))
        conn.commit()
        return True, "Recurring instruction saved."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def execute_all_standing_instructions():
    conn = get_db_connection()
    if not conn: return 0, "Database error"
    
    executed_count = 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM standing_instructions")
        instructions = cursor.fetchall()
        
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for ins in instructions:
            # We bypass the 'day_of_month' check for demonstration and just execute all of them 
            # to simulate the passage of time accurately for the mock.
            success, msg = execute_transfer(ins['user_id'], ins['receiver_account'], ins['amount'])
            if success:
                cursor.execute("UPDATE standing_instructions SET last_executed = ? WHERE id = ?", (now_str, ins['id']))
                executed_count += 1
                
        conn.commit()
        return executed_count, f"Processed {executed_count} recurring transfers."
    except Exception as e:
        conn.rollback()
        return 0, str(e)
    finally:
        conn.close()

def get_standing_instructions(user_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT si.id, si.receiver_account, si.amount, si.day_of_month, si.last_executed,
                   a.account_number as my_account
            FROM standing_instructions si
            JOIN accounts a ON si.user_id = a.user_id
            WHERE si.user_id = ?
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_suggested_payees(user_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        # 1. Get real recent payees from transaction history
        cursor.execute("""
            SELECT DISTINCT u.id, u.full_name, u.upi_id, u.phone_number, a.account_number, MAX(t.created_at) as last_paid
            FROM transactions t
            JOIN users u ON t.receiver_id = u.id
            JOIN accounts a ON a.user_id = u.id
            WHERE t.sender_id = ? AND u.id != ? AND u.is_admin = 0
            GROUP BY u.id
            ORDER BY last_paid DESC
            LIMIT 5
        """, (user_id, user_id))
        real_payees = [dict(row) for row in cursor.fetchall()]
        
        # 2. If fewer than 5, fill with other registered users
        if len(real_payees) < 5:
            exclude_ids = [p['id'] for p in real_payees] + [user_id]
            placeholders = ','.join(['?'] * len(exclude_ids))
            cursor.execute(f"""
                SELECT u.id, u.full_name, u.upi_id, u.phone_number, a.account_number
                FROM users u
                JOIN accounts a ON a.user_id = u.id
                WHERE u.id NOT IN ({placeholders}) AND u.is_admin = 0
                LIMIT ?
            """, exclude_ids + [5 - len(real_payees)])
            others = [dict(row) for row in cursor.fetchall()]
            real_payees.extend(others)
            
        return real_payees
    finally:
        conn.close()

def get_user_by_phone(phone_number):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.full_name, a.account_number 
            FROM users u
            JOIN accounts a ON u.id = a.user_id
            WHERE u.phone_number = ?
        """, (phone_number,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

# SELF-REGISTRATION & ADMIN USER APPROVAL WORKFLOW
def register_user(full_name, phone_number, password, aadhaar_number, email=None, profile_photo=None, id_proof=None, preferred_language='Kannada'):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection error"
    try:
        cursor = conn.cursor()
        full_name = (full_name or '').strip()
        phone_number = "".join(c for c in str(phone_number) if c.isdigit())
        aadhaar_number = "".join(c for c in str(aadhaar_number) if c.isdigit())
        password = str(password or '').strip()
        email = str(email or '').strip() if email else None

        if not full_name:
            return False, "Full Name is required."
        if len(phone_number) < 10:
            return False, "Phone number must be at least 10 digits."
        if len(aadhaar_number) < 12:
            return False, "Aadhaar number must be 12 digits."
        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters."

        # Check for existing phone
        cursor.execute("SELECT id FROM users WHERE phone_number = ?", (phone_number,))
        if cursor.fetchone():
            return False, "Phone number is already registered."

        # Check for existing Aadhaar
        cursor.execute("SELECT id FROM users WHERE aadhaar_number = ?", (aadhaar_number,))
        if cursor.fetchone():
            return False, "Aadhaar number is already registered."

        # Generate Customer ID
        cursor.execute("SELECT COUNT(id) FROM users")
        count = cursor.fetchone()[0]
        customer_id = f"CUST10{str(count + 11).zfill(2)}"

        cursor.execute('''
            INSERT INTO users (customer_id, phone_number, password_hash, full_name, preferred_language, aadhaar_number, email, profile_photo, id_proof, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
        ''', (customer_id, phone_number, password, full_name, preferred_language, aadhaar_number, email, profile_photo, id_proof))
        
        user_id = cursor.lastrowid
        conn.commit()
        return True, {
            "customer_id": customer_id,
            "user_id": user_id,
            "full_name": full_name,
            "phone_number": phone_number,
            "email": email,
            "status": "PENDING",
            "message": "Registration submitted successfully! Pending admin approval."
        }
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_user_registrations():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.customer_id, u.full_name, u.phone_number, u.aadhaar_number, u.email,
                   u.profile_photo, u.id_proof,
                   u.preferred_language, u.status, u.rejection_reason, u.created_at,
                   a.account_number, a.balance
            FROM users u
            LEFT JOIN accounts a ON a.user_id = u.id
            WHERE u.is_admin = 0
            ORDER BY 
                CASE WHEN u.status = 'PENDING' THEN 0 WHEN u.status = 'REJECTED' THEN 2 ELSE 1 END,
                u.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_registration_status(identifier):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, customer_id, full_name, phone_number, aadhaar_number, status, rejection_reason, created_at
            FROM users
            WHERE phone_number = ? OR customer_id = ? OR aadhaar_number = ?
        """, (identifier, identifier, identifier))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def admin_approve_user(user_id):
    conn = get_db_connection()
    if not conn:
        return False, "Database error", None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_id, full_name, phone_number, email, status FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return False, "User not found", None

        first_name = user['full_name'].split()[0].lower()
        clean_first = re.sub(r'[^a-zA-Z0-9]', '', first_name) or 'user'
        upi_id = f"{clean_first}{user_id}@siri"

        # Update user status to ACTIVE and set upi_id
        cursor.execute("UPDATE users SET status = 'ACTIVE', upi_id = ?, rejection_reason = NULL WHERE id = ?", (upi_id, user_id))

        # Check existing account
        cursor.execute("SELECT id, account_number FROM accounts WHERE user_id = ?", (user_id,))
        acc = cursor.fetchone()
        if not acc:
            cursor.execute("SELECT COUNT(id) FROM accounts")
            acc_count = cursor.fetchone()[0]
            new_acc_num = f"ACC{80000 + acc_count + 1}"
            cursor.execute('''
                INSERT INTO accounts (user_id, account_number, balance, status)
                VALUES (?, ?, 1000.00, 'ACTIVE')
            ''', (user_id, new_acc_num))
            cursor.execute('''
                INSERT INTO transactions (receiver_id, amount, transaction_type, description)
                VALUES (?, 1000.00, 'DEPOSIT', 'Welcome Opening Balance Credit')
            ''', (user_id,))
        else:
            new_acc_num = acc['account_number']
            cursor.execute("UPDATE accounts SET status = 'ACTIVE' WHERE user_id = ?", (user_id,))

        conn.commit()
        user_payload = {
            "user_id": user_id,
            "customer_id": user['customer_id'],
            "full_name": user['full_name'],
            "email": user['email'],
            "phone_number": user['phone_number'],
            "account_number": new_acc_num,
            "upi_id": upi_id
        }
        return True, "User registration approved successfully. Account is now ACTIVE.", user_payload
    except Exception as e:
        conn.rollback()
        return False, str(e), None
    finally:
        conn.close()

def admin_reject_user(user_id, reason):
    conn = get_db_connection()
    if not conn:
        return False, "Database error", None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_id, full_name, phone_number, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return False, "User not found", None

        reason = (reason or "Details could not be verified by the bank.").strip()
        cursor.execute("UPDATE users SET status = 'REJECTED', rejection_reason = ? WHERE id = ?", (reason, user_id))
        cursor.execute("UPDATE accounts SET status = 'INACTIVE' WHERE user_id = ?", (user_id,))
        conn.commit()
        user_payload = {
            "user_id": user_id,
            "full_name": user['full_name'],
            "email": user['email'],
            "phone_number": user['phone_number'],
            "rejection_reason": reason
        }
        return True, "User registration has been marked as REJECTED.", user_payload
    except Exception as e:
        conn.rollback()
        return False, str(e), None
    finally:
        conn.close()
