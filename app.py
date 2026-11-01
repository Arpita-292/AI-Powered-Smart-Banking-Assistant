from flask import Flask, request, jsonify, render_template, session, redirect, url_for, Response
from db_utils import authenticate_user, get_user_account_summary, create_bank_request
from chatbot_logic import process_chat_intent, get_translation, format_text_for_speech, detect_user_language
import os, csv, io, urllib.request, urllib.parse, re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_siri_bank_key')

@app.route('/login')
@app.route('/register')
@app.route('/signup')
@app.route('/')
def index():
    if 'user_id' in session and request.path == '/':
        return redirect(url_for('home'))
    # Clean all visitor registration and chat session state on fresh page load or refresh
    session.pop('reg_flow', None)
    session.pop('chat_history', None)
    session.pop('login_mobile', None)
    session.pop('kyc_otp', None)
    if 'user_id' not in session:
        saved_lang = session.get('language', 'Kannada')
        session.clear()
        session['language'] = saved_lang
    return render_template('login.html', language=session.get('language', 'Kannada'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    # Simulate credit card eligibility: Only CUST1001 gets it for demo
    has_credit_card = (session.get('customer_id') == 'CUST1001')
    return render_template('index.html', 
                          user_name=session.get('user_name'),
                          language=session.get('language', 'Kannada'),
                          has_credit_card=has_credit_card)

@app.route('/pay')
def pay():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('pay.html', 
                          user_name=session.get('user_name'),
                          language=session.get('language', 'Kannada'))

@app.route('/atm-services')
def atm_services():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    # Simulate credit card eligibility: Only CUST1001 gets it for demo
    has_credit_card = (session.get('customer_id') == 'CUST1001')
    return render_template('atm.html', 
                          user_name=session.get('user_name'),
                          language=session.get('language', 'Kannada'),
                          has_credit_card=has_credit_card)

@app.route('/favicon.ico')
def favicon():
    return ('', 204)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    identifier = data.get('identifier')
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({"success": False, "message": "Missing credentials"})
    
    user, msg = authenticate_user(identifier, password)
    if user:
        session.pop('login_identifier', None)
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['language'] = user.get('preferred_language', 'Kannada')
        session['customer_id'] = user['customer_id']
        session['is_admin'] = user['is_admin']
        
        redirect_url = '/admin' if user['is_admin'] else '/home'
        return jsonify({"success": True, "message": "Logged in successfully", "redirect": redirect_url})
    else:
        status_type = "INVALID"
        if "PENDING" in str(msg):
            status_type = "PENDING"
        elif "REJECTED" in str(msg):
            status_type = "REJECTED"
        return jsonify({"success": False, "message": msg, "status_type": status_type}), 401

@app.route('/aadhaar-kyc')
def kyc():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('index'))
    
    summary = get_user_account_summary(session['user_id'])
    kyc_status = None
    rejection_reason = None
    is_retry = (request.args.get('retry', '').lower() in ['true', '1', 'yes']) or session.get('kyc_retry_mode', False)
    if is_retry:
        session['kyc_retry_mode'] = True
    elif summary and 'recent_requests' in summary:
        for req in summary['recent_requests']:
            if req['request_type'] in ['AADHAAR_LINK', 'KYC', 'AADHAAR']:
                kyc_status = req['status']
                rejection_reason = req.get('rejection_reason')
                break
        if not rejection_reason and summary.get('user', {}).get('rejection_reason'):
            rejection_reason = summary['user']['rejection_reason']
        if not kyc_status and summary.get('user', {}).get('status') == 'REJECTED':
            kyc_status = 'REJECTED'

    return render_template('kyc.html', 
                          user_name=session.get('user_name'), 
                          language=session.get('language', 'Kannada'),
                          kyc_status=kyc_status,
                          rejection_reason=rejection_reason)

@app.route('/request-history')
def history():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('index'))
    summary = get_user_account_summary(session['user_id']) or {}
    return render_template('history.html', 
                           user_name=session.get('user_name'), 
                           language=session.get('language', 'Kannada'),
                           summary=summary)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('profile.html', 
                          user_name=session.get('user_name'),
                          language=session.get('language', 'Kannada'))

@app.route('/presentation')
def presentation_view():
    return render_template('pitch.html')

from db_utils import (
    get_all_users_and_requests, update_request_status, execute_transfer,
    create_new_user, admin_execute_financial_op, get_system_analytics,
    apply_for_loan, get_all_loans, admin_process_loan,
    save_standing_instruction, execute_all_standing_instructions,
    get_standing_instructions, get_suggested_payees, get_user_by_phone,
    register_user, get_user_registrations, admin_approve_user, admin_reject_user,
    get_registration_status
)

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    data = get_all_users_and_requests()
    data['loans'] = get_all_loans()
    data['registrations'] = get_user_registrations()
    data['pending_registrations_count'] = sum(1 for r in data['registrations'] if r.get('status') == 'PENDING')
    # Exclude admin accounts (is_admin = 1) from customer count
    data['customer_count'] = sum(1 for u in data['users'] if not u.get('is_admin'))
    data['analytics'] = get_system_analytics()
    return render_template('admin.html', user_name=session.get('user_name'), data=data)

from email_service import (
    send_registration_received_email, send_account_approval_email,
    send_account_rejection_email, send_transaction_email
)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json or {}
    full_name = data.get('full_name')
    phone_number = data.get('phone_number')
    password = data.get('password')
    aadhaar_number = data.get('aadhaar_number')
    email = data.get('email')
    profile_photo = data.get('profile_photo')
    id_proof = data.get('id_proof')
    preferred_language = data.get('preferred_language', 'Kannada')
    
    success, result = register_user(
        full_name, phone_number, password, aadhaar_number,
        email=email, profile_photo=profile_photo, id_proof=id_proof,
        preferred_language=preferred_language
    )
    if success:
        if email:
            send_registration_received_email(email, full_name, result['customer_id'], phone_number)
        return jsonify({
            "success": True,
            "message": result['message'],
            "customer_id": result['customer_id'],
            "status": result['status']
        })
    else:
        return jsonify({"success": False, "message": str(result)}), 400

@app.route('/api/registration_status', methods=['GET'])
def api_registration_status():
    identifier = request.args.get('identifier', '').strip()
    if not identifier:
        return jsonify({"success": False, "message": "Please provide a Phone or Aadhaar or Customer ID"}), 400
    info = get_registration_status(identifier)
    if info:
        return jsonify({"success": True, "data": info})
    return jsonify({"success": False, "message": "No registration record found for this identifier."}), 404

@app.route('/api/admin/registrations', methods=['GET'])
def api_admin_registrations():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    regs = get_user_registrations()
    return jsonify({"success": True, "registrations": regs})

@app.route('/api/admin/approve_user', methods=['POST'])
def api_admin_approve_user():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400
    success, msg, user_payload = admin_approve_user(user_id)
    if success and user_payload and user_payload.get('email'):
        send_account_approval_email(
            user_payload['email'],
            user_payload['full_name'],
            user_payload['customer_id'],
            user_payload['account_number'],
            user_payload['upi_id']
        )
    return jsonify({"success": success, "message": msg, "user": user_payload})

@app.route('/api/admin/reject_user', methods=['POST'])
def api_admin_reject_user():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    user_id = data.get('user_id')
    reason = data.get('reason', 'Verification rejected by administrator.')
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400
    success, msg, user_payload = admin_reject_user(user_id, reason)
    if success and user_payload and user_payload.get('email'):
        send_account_rejection_email(
            user_payload['email'],
            user_payload['full_name'],
            user_payload.get('rejection_reason', reason)
        )
    return jsonify({"success": success, "message": msg, "user": user_payload})

@app.route('/api/admin/user/<int:user_id>/documents', methods=['GET'])
def api_admin_user_documents(user_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    from db_utils import get_db_connection
    conn = get_db_connection()
    user_row = conn.execute("""
        SELECT u.id, u.customer_id, u.full_name, u.phone_number, u.aadhaar_number, u.email,
               u.profile_photo, u.id_proof, u.status, u.created_at, u.rejection_reason
        FROM users u WHERE u.id = ?
    """, (user_id,)).fetchone()
    conn.close()
    if not user_row:
        return jsonify({"success": False, "message": "User not found"}), 404
    return jsonify({"success": True, "user": dict(user_row)})

@app.route('/api/admin/update_request', methods=['POST'])
def admin_update_request():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    success = update_request_status(data.get('request_id'), data.get('status'), data.get('rejection_reason'))
    return jsonify({"success": success})

@app.route('/api/admin/analytics', methods=['GET'])
def admin_analytics():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_system_analytics())

@app.route('/api/admin/create_user', methods=['POST'])
def admin_create_user():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    success, msg = create_new_user(data.get('full_name'), data.get('phone_number'), float(data.get('initial_deposit', 0)), data.get('aadhaar_number'))
    return jsonify({"success": success, "message": msg})

@app.route('/api/admin/transaction', methods=['POST'])
def admin_transaction():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    success, result = admin_execute_financial_op(
        data.get('account_number'),
        data.get('ifsc_code', 'UNKNOWN'),
        data.get('op_type'),
        float(data.get('amount', 0)),
        data.get('narration', '')
    )
    if success:
        return jsonify({"success": True, "message": result['msg'], "txn_id": result['txn_id'], "balance": result['balance']})
    else:
        return jsonify({"success": False, "message": result})

@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    success, msg = execute_transfer(session['user_id'], data.get('receiver_account'), float(data.get('amount')))
    return jsonify({"success": success, "message": msg})

@app.route('/api/transfer/phone', methods=['POST'])
def api_transfer_phone():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    phone = data.get('phone_number')
    amount = data.get('amount')
    
    if not phone or not amount:
        return jsonify({"success": False, "message": "Missing phone number or amount"})
        
    user_info = get_user_by_phone(phone)
    if not user_info:
        return jsonify({"success": False, "message": "Phone number not registered with SIRI BANK"})
        
    success, msg = execute_transfer(session['user_id'], user_info['account_number'], float(amount))
    return jsonify({"success": success, "message": msg, "receiver_name": user_info['full_name']})

@app.route('/api/user/lookup-phone', methods=['GET'])
def api_lookup_phone():
    phone = (request.args.get('phone') or '').strip()
    if not phone or len(phone) < 10:
        return jsonify({"found": False, "message": "Enter 10-digit number"})
    
    clean_phone = re.sub(r'\D', '', phone)
    if clean_phone.startswith('91') and len(clean_phone) == 12:
        clean_phone = clean_phone[2:]
    
    user_info = get_user_by_phone(clean_phone)
    if user_info:
        return jsonify({
            "found": True,
            "name": user_info['full_name'],
            "account_number": user_info['account_number'],
            "phone": clean_phone
        })
    return jsonify({
        "found": False,
        "message": "No registered SIRI BANK user found with this mobile number"
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True, "redirect": "/"})

@app.route('/api/chat/clear', methods=['POST'])
def api_chat_clear():
    session.pop('chat_history', None)
    session.pop('reg_flow', None)
    session.pop('kyc_otp', None)
    return jsonify({"success": True, "message": "Chat history cleared successfully"})

@app.route('/api/user/set_language', methods=['POST'])
def api_set_language():
    data = request.json or {}
    lang = data.get('language')
    if lang in ['Kannada', 'English']:
        session['language'] = lang
        if 'user_id' in session:
            try:
                conn = get_db_connection()
                conn.execute("UPDATE users SET preferred_language = ? WHERE id = ?", (lang, session['user_id']))
                conn.commit()
                conn.close()
            except Exception:
                pass
        return jsonify({"success": True, "language": lang})
    return jsonify({"success": False, "message": "Invalid language"}), 400

@app.route('/api/user/summary', methods=['GET'])
def api_user_summary():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    summary = get_user_account_summary(session['user_id'])
    if summary:
        return jsonify(summary)
    return jsonify({"error": "Failed to load summary"}), 500

@app.route('/api/user/upcoming', methods=['GET'])
def api_user_upcoming():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_standing_instructions(session['user_id']))

@app.route('/api/user/payees', methods=['GET'])
def api_user_payees():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_suggested_payees(session['user_id']))

@app.route('/api/user/statement/download', methods=['GET'])
def api_download_statement():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    summary = get_user_account_summary(session['user_id'])
    if not summary or 'transactions' not in summary:
        return "Failed to load ledger", 500
        
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Transaction ID', 'Date', 'Type', 'Description', 'Amount', 'Sender', 'Receiver'])
    
    for tx in summary['transactions']:
        cw.writerow([
            f"TXN-{tx['id']}",
            tx['created_at'],
            tx['transaction_type'],
            tx['description'],
            tx['amount'],
            tx['sender_name'] if tx['sender_name'] else 'SYSTEM',
            tx['receiver_name'] if tx['receiver_name'] else 'SYSTEM'
        ])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=account_statement.csv"}
    )

@app.route('/api/user/kyc/submit', methods=['POST'])
def api_submit_kyc():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    d = request.json or {}
    rtype = d.get('request_type', 'AADHAAR_LINK')
    details = d.get('details', 'Completed Aadhaar KYC via multi-step wizard')
    
    if rtype == 'AADHAAR_LINK':
        submitted_aadhaar = d.get('aadhaar_number')
        if submitted_aadhaar:
            submitted_aadhaar = "".join(c for c in str(submitted_aadhaar) if c.isdigit())
            
        from db_utils import get_db_connection
        conn = get_db_connection()
        user_row = conn.execute("SELECT aadhaar_number FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        
        registered_aadhaar = user_row['aadhaar_number'] if user_row else None
        if registered_aadhaar:
            registered_aadhaar = "".join(c for c in str(registered_aadhaar) if c.isdigit())
            
        if registered_aadhaar and submitted_aadhaar and submitted_aadhaar != registered_aadhaar:
            session.pop('kyc_retry_mode', None)
            create_bank_request(
                session['user_id'],
                rtype,
                details,
                status='REJECTED',
                rejection_reason='Automated Rejection: Submitted Aadhaar number does not match the registered Aadhaar number on profile.'
            )
            return jsonify({"success": True, "message": "KYC process completed. Auto-verification failed.", "auto_rejected": True})
            
        if not registered_aadhaar and submitted_aadhaar:
            conn = get_db_connection()
            conn.execute("UPDATE users SET aadhaar_number = ? WHERE id = ?", (submitted_aadhaar, session['user_id']))
            conn.commit()
            conn.close()

    session.pop('kyc_retry_mode', None)
    create_bank_request(session['user_id'], rtype, details, status='PENDING')
    return jsonify({"success": True, "message": "Request Submitted Successfully"})

@app.route('/api/user/kyc/generate-otp', methods=['POST'])
def generate_kyc_otp():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    import random
    otp = str(random.randint(100000, 999999))
    session['kyc_otp'] = otp
    return jsonify({"success": True, "message": "OTP generated successfully", "otp": otp})

@app.route('/api/user/kyc/verify-otp', methods=['POST'])
def verify_kyc_otp():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    data = request.json
    entered_otp = data.get('otp')
    stored_otp = session.get('kyc_otp')
    if not entered_otp or entered_otp != stored_otp:
        return jsonify({"success": False, "message": "Invalid OTP code entered"})
    session.pop('kyc_otp', None)
    return jsonify({"success": True, "message": "OTP verified successfully"})

@app.route('/api/user/loan', methods=['POST'])
def api_user_loan():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    success, msg = apply_for_loan(session['user_id'], float(d.get('amount')), d.get('purpose'))
    return jsonify({"success": success, "message": msg})

@app.route('/api/admin/loan_action', methods=['POST'])
def api_admin_loan_action():
    if not session.get('is_admin'): return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    success, msg = admin_process_loan(d.get('loan_id'), d.get('action'))
    return jsonify({"success": success, "message": msg})

@app.route('/api/standing_instruction', methods=['POST'])
def api_standing_instruction():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    success, msg = save_standing_instruction(session['user_id'], d.get('receiver_account'), d.get('amount'), d.get('day_of_month', 1))
    return jsonify({"success": success, "message": msg})

@app.route('/api/admin/run_cron', methods=['POST'])
def api_admin_run_cron():
    if not session.get('is_admin'): return jsonify({"error": "Unauthorized"}), 401
    executed, msg = execute_all_standing_instructions()
    return jsonify({"success": True, "message": msg, "count": executed})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    client_history = data.get('history') or []
    session_history = session.get('chat_history', [])
    conversation_history = client_history if client_history else session_history

    current_page = data.get('page') or ''
    current_tab = data.get('tab') or ''
    if 'user_id' in session:
        if current_tab in ['login', 'register'] or not current_tab:
            if 'kyc' in current_page: current_tab = 'kyc'
            elif 'pay' in current_page: current_tab = 'pay'
            elif 'atm' in current_page: current_tab = 'atm'
            elif 'history' in current_page: current_tab = 'history'
            else: current_tab = 'dashboard'

    # Dynamic automatic language detection based on user input
    detected_lang = detect_user_language(user_message)
    language = detected_lang or data.get('language') or session.get('language', 'Kannada')
    if language not in ['Kannada', 'English']:
        language = 'Kannada'

    if 'user_id' in session:
        session['language'] = language
        
    user_state = {
        'current_page': current_page,
        'current_tab': current_tab
    }

    # Step-by-step registration flow state tracking
    form_state = data.get('form_state') or {}
    # Only reset registration flow if visitor on registration tab with empty client history
    if not client_history and 'user_id' not in session and current_tab == 'register':
        session.pop('reg_flow', None)
        session.pop('chat_history', None)
        session_history = []
        conversation_history = []
        reg_flow = {}
    else:
        reg_flow = session.get('reg_flow', {}).copy() if isinstance(session.get('reg_flow'), dict) else {}

    if isinstance(form_state, dict):
        for k in ['name', 'email', 'phone', 'aadhaar', 'password', 'photo', 'id_proof']:
            val = form_state.get(k)
            if val and (isinstance(val, str) or isinstance(val, bool)) and str(val).strip():
                reg_flow[k] = val if isinstance(val, bool) else val.strip()
    session['reg_flow'] = reg_flow
    user_state['reg_flow'] = reg_flow

    # Login Flow State Tracking
    login_ident = ''
    if isinstance(form_state, dict) and form_state.get('identifier'):
        login_ident = str(form_state.get('identifier')).strip()
    if not login_ident:
        login_ident = session.get('login_identifier', '')
    user_state['login_identifier'] = login_ident

    # KYC Flow State Tracking
    kyc_flow = session.get('kyc_flow', {}).copy() if isinstance(session.get('kyc_flow'), dict) else {}
    if isinstance(form_state, dict):
        if form_state.get('kyc_name'): kyc_flow['name'] = form_state['kyc_name']
        if form_state.get('kyc_dob'): kyc_flow['dob'] = form_state['kyc_dob']
        if form_state.get('kyc_aadhaar'): kyc_flow['aadhaar'] = form_state['kyc_aadhaar']
    user_state['kyc_flow'] = kyc_flow

    if 'user_id' in session:
        user_state['is_visitor'] = False
        user_state['user_id'] = session['user_id']
        summary = get_user_account_summary(session['user_id'])
        if summary and summary.get("accounts"):
            acc = summary["accounts"][0]
            user_state['account_number'] = acc['account_number']
            user_state['balance'] = str(acc['balance'])
        if summary and summary.get("user"):
            user_state['user_name'] = summary["user"].get('full_name')
            user_state['upi_id'] = summary["user"].get('upi_id')
            user_state['aadhaar_number'] = summary["user"].get('aadhaar_number')
            user_state['phone_number'] = summary["user"].get('phone_number')

        # Check KYC status and rejection reason from recent requests
        kyc_status = None
        kyc_rejection_reason = None
        if summary and summary.get('recent_requests'):
            for req in summary['recent_requests']:
                if req.get('request_type') in ['AADHAAR_LINK', 'KYC', 'AADHAAR']:
                    kyc_status = req.get('status')
                    kyc_rejection_reason = req.get('rejection_reason')
                    break
        if not kyc_rejection_reason and summary and summary.get('user', {}).get('rejection_reason'):
            kyc_rejection_reason = summary['user']['rejection_reason']
        if not kyc_status and summary and summary.get('user', {}).get('status') == 'REJECTED':
            kyc_status = 'REJECTED'
        user_state['kyc_status'] = kyc_status
        user_state['kyc_rejection_reason'] = kyc_rejection_reason
        user_state['kyc_retry_mode'] = session.get('kyc_retry_mode', False)
            
        # Prune any stale visitor login turns from conversation history
        clean_history = []
        for turn in conversation_history:
            content = (turn.get('content') or '').lower()
            if not any(w in content for w in ['ready to log in', 'noted your mobile number as', 'login form. please provide']):
                clean_history.append(turn)
        conversation_history = clean_history
    else:
        user_state['is_visitor'] = True
        user_state['user_name'] = 'Visitor'
        
    # Feed last bot message for contextual detection
    last_bot_msg = ''
    for turn in reversed(conversation_history):
        if turn.get('role') == 'assistant':
            last_bot_msg = turn.get('content', '')
            break
    user_state['last_bot_message'] = last_bot_msg

    # Process intent using conversational Gemini with multi-turn memory
    response_data = process_chat_intent(
        user_message, 
        user_state, 
        language=language, 
        conversation_history=conversation_history
    )
    
    final_lang = response_data.get('switch_language') or language
    session['language'] = final_lang
    if 'user_id' in session:
        try:
            with get_db_connection() as conn:
                conn.execute("UPDATE users SET preferred_language = ? WHERE id = ?", (final_lang, session['user_id']))
                conn.commit()
        except Exception:
            pass

    # Update session reg_flow state
    if response_data.get('reg_flow'):
        session['reg_flow'] = response_data.get('reg_flow')
    elif response_data.get('action') in ['SUBMIT_FORM', 'CANCEL_SUBMIT', 'RESET_FORM'] or response_data.get('reg_flow') == {}:
        session.pop('reg_flow', None)

    # Update session kyc_flow state
    if response_data.get('kyc_flow'):
        session['kyc_flow'] = response_data.get('kyc_flow')
    elif response_data.get('action') in ['RESET_KYC', 'KYC_RETRY'] or response_data.get('kyc_flow') == {}:
        session.pop('kyc_flow', None)

    # Update session login_identifier state
    if response_data.get('fields', {}).get('identifier'):
        session['login_identifier'] = response_data['fields']['identifier']
    elif response_data.get('action') == 'SUBMIT_FORM' and response_data.get('target_form') == 'login':
        session.pop('login_identifier', None)

    # Persist kyc_retry_mode if reset or retry initiated
    if response_data.get('action') in ['RESET_KYC', 'KYC_RETRY'] or response_data.get('intent') in ['KYC_RETRY', 'KYC_REJECTED_EXPLAIN']:
        session['kyc_retry_mode'] = True
    elif response_data.get('action') == 'SUBMIT_FORM' and response_data.get('target_form') == 'kyc':
        session.pop('kyc_retry_mode', None)

    # Handle DB actions based on intent if user is logged in
    if 'user_id' in session:
        if response_data.get('action') == 'CREATE_REQUEST_ATM':
            create_bank_request(session['user_id'], 'ATM_CARD', 'Requested Visa Debit Card via Assistant')
        elif response_data.get('action') == 'CREATE_REQUEST_AADHAAR':
            create_bank_request(session['user_id'], 'AADHAAR_LINK', 'Requested Aadhaar Linking via Assistant')

    # Update session memory (maintain last 10 dialogue turns)
    session_history.append({"role": "user", "content": user_message})
    session_history.append({"role": "assistant", "content": response_data.get('reply', '')})
    session['chat_history'] = session_history[-10:]

    return jsonify({
        "reply": response_data.get('reply'),
        "intent": response_data.get('intent'),
        "action": response_data.get('action'),
        "mode": response_data.get('mode'),
        "tool": response_data.get('tool'),
        "target_form": response_data.get('target_form'),
        "fields": response_data.get('fields', {}),
        "reg_flow": session.get('reg_flow', {}),
        "kyc_flow": session.get('kyc_flow', {}),
        "redirect": response_data.get('redirect'),
        "switch_language": final_lang,
        "history": session['chat_history']
    })

_tts_audio_cache = {}

@app.route('/api/tts')
def api_tts():
    text = request.args.get('text', '')
    lang_param = request.args.get('lang', 'Kannada')
    
    if not text:
        return Response("No text provided", status=400)
        
    lang_map = {
        'English': 'en',
        'Kannada': 'kn',
        'en': 'en',
        'kn': 'kn'
    }
    lang_code = lang_map.get(lang_param, 'kn')

    # Format numbers naturally for speech: account numbers digit-by-digit, amounts in words
    spoken_text = format_text_for_speech(text, lang_param)
    clean_text = spoken_text.strip()[:1500]
    if not clean_text:
        clean_text = text.strip()[:500]

    # Auto-align language based on script to prevent accent distortion or bilingual mixup
    has_kannada = bool(re.search(r'[\u0C80-\u0CFF]', clean_text))
    if has_kannada:
        lang_code = 'kn'
    elif re.search(r'[A-Za-z]', clean_text):
        lang_code = 'en'
    else:
        lang_code = 'kn' if lang_param == 'Kannada' else 'en'

    cache_key = (lang_code, clean_text)
    if cache_key in _tts_audio_cache:
        return Response(_tts_audio_cache[cache_key], mimetype='audio/mpeg')

    # Fast direct Google Translate TTS endpoint (sub-100ms response)
    try:
        if len(clean_text) <= 180:
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(clean_text)}&tl={lang_code}&client=tw-ob"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                audio_data = resp.read()
            if len(_tts_audio_cache) > 500:
                _tts_audio_cache.clear()
            _tts_audio_cache[cache_key] = audio_data
            return Response(audio_data, mimetype='audio/mpeg')
    except Exception:
        pass

    # Try gTTS library for multi-sentence responses
    try:
        from gtts import gTTS
        import io
        fp = io.BytesIO()
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        tts.write_to_fp(fp)
        audio_data = fp.getvalue()
        if len(_tts_audio_cache) > 500:
            _tts_audio_cache.clear()
        _tts_audio_cache[cache_key] = audio_data
        return Response(audio_data, mimetype='audio/mpeg')
    except Exception as e:
        print("gTTS generation notice:", e)

    # Multi-chunk Google Translate TTS fallback for long text
    try:
        chunks = []
        sentences = re.split(r'([.!?\n\u0964]+)', clean_text)
        curr = ""
        for part in sentences:
            if len(curr) + len(part) < 150:
                curr += part
            else:
                if curr.strip(): chunks.append(curr.strip())
                curr = part
        if curr.strip(): chunks.append(curr.strip())
        if not chunks: chunks = [clean_text[:150]]

        audio_parts = []
        for chunk in chunks:
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(chunk)}&tl={lang_code}&client=tw-ob"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                audio_parts.append(resp.read())

        full_audio = b''.join(audio_parts)
        if len(_tts_audio_cache) > 500:
            _tts_audio_cache.clear()
        _tts_audio_cache[cache_key] = full_audio
        return Response(full_audio, mimetype='audio/mpeg')
    except Exception as e:
        print("TTS Fallback Error:", e)
        return Response("TTS Generation Failed", status=500)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
