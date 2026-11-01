import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com').strip()
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '').strip()
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '').replace(' ', '').strip()
SMTP_SENDER_NAME = os.environ.get('SMTP_SENDER_NAME', 'SIRI BANK').strip().strip('"').strip("'")

def is_smtp_configured():
    """Checks if valid SMTP credentials exist."""
    return bool(SMTP_USER and SMTP_PASSWORD)

def _send_email_thread(to_email, subject, html_content, text_content=None):
    """Internal worker thread function to send emails without blocking the web request."""
    if not to_email or '@' not in str(to_email):
        print(f"[Email Notice] Invalid recipient email address: {to_email}")
        return False

    to_email = str(to_email).strip()
    
    if not is_smtp_configured():
        print(f"\n=======================================================")
        print(f"📧 [REAL EMAIL SIMULATION / SMTP PENDING CONFIGURATION]")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Status: Ready for SMTP delivery. (Add SMTP_USER & SMTP_PASSWORD in .env for live transport)")
        print(f"=======================================================\n")
        return True

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_SENDER_NAME} <{SMTP_USER}>"
        msg['To'] = to_email
        msg['Reply-To'] = "support@siribank.in"
        msg['X-Mailer'] = "SIRI-BANK-AI-Core/2026"

        if text_content:
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part1)

        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())
        server.quit()

        print(f"[SUCCESS] [REAL EMAIL SENT VIA SMTP] To: {to_email} | Subject: {subject}")
        return True
    except Exception as e:
        print(f"[ERROR] [EMAIL DELIVERY FAILED] To: {to_email} | Error: {e}")
        return False

def send_real_email(to_email, subject, html_content, text_content=None, async_send=True):
    """
    Sends an email using configured SMTP.
    Runs asynchronously in background thread by default so user requests never lag.
    """
    if not to_email:
        return False
    
    if async_send:
        t = threading.Thread(target=_send_email_thread, args=(to_email, subject, html_content, text_content))
        t.daemon = True
        t.start()
        return True
    else:
        return _send_email_thread(to_email, subject, html_content, text_content)

# ─────────────────────────────────────────────────────────────────────────────
# ULTRA-REALISTIC BANKING EMAIL TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

def get_base_email_template(title, headline, body_html, badge_text="OFFICIAL NOTIFICATION"):
    """Returns an ultra-realistic, responsive HTML email template styled like leading banks."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 0; color: #0f172a; -webkit-font-smoothing: antialiased; }}
            .wrapper {{ width: 100%; background-color: #f8fafc; padding: 30px 10px; box-sizing: border-box; }}
            .email-container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
            .brand-bar {{ background: linear-gradient(135deg, #4f46e5 0%, #1e1b4b 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
            .brand-logo {{ font-size: 24px; font-weight: 900; letter-spacing: 1.5px; margin: 0; text-transform: uppercase; }}
            .brand-tagline {{ font-size: 11px; opacity: 0.85; letter-spacing: 0.8px; margin: 4px 0 0; text-transform: uppercase; font-weight: 600; }}
            .badge {{ display: inline-block; background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; margin-bottom: 10px; letter-spacing: 0.5px; }}
            .content {{ padding: 30px 24px; line-height: 1.6; font-size: 14.5px; color: #334155; }}
            .headline {{ font-size: 19px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 12px; }}
            .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 18px 0; }}
            .card-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #edf2f7; font-size: 13.5px; }}
            .card-row:last-child {{ border-bottom: none; padding-bottom: 0; }}
            .card-label {{ color: #64748b; font-weight: 600; }}
            .card-value {{ font-weight: 700; color: #0f172a; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; text-align: right; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%); color: #ffffff !important; text-decoration: none; padding: 13px 26px; border-radius: 10px; font-weight: 700; font-size: 14px; margin: 16px 0; text-align: center; box-shadow: 0 4px 12px rgba(79,70,229,0.3); }}
            .security-box {{ font-size: 12px; color: #475569; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 12px 14px; margin-top: 20px; line-height: 1.5; }}
            .footer {{ background: #f8fafc; padding: 22px; text-align: center; font-size: 11.5px; color: #94a3b8; border-top: 1px solid #e2e8f0; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="email-container">
                <div class="brand-bar">
                    <div class="badge">{badge_text}</div>
                    <div class="brand-logo">SIRI BANK</div>
                    <div class="brand-tagline">AI Powered Smart Banking Ecosystem</div>
                </div>
                <div class="content">
                    <div class="headline">{headline}</div>
                    {body_html}
                </div>
                <div class="footer">
                    <p style="margin: 0 0 6px;"><strong>SIRI BANK AI Technologies Ltd.</strong> • Digital Banking Division</p>
                    <p style="margin: 0 0 6px;">Toll-Free Helpline: <strong>1800-SIRI-BANK</strong> | Email: <strong>support@siribank.in</strong></p>
                    <p style="margin: 0; color: #cbd5e1; font-size: 10.5px;">This is an automated encrypted message. SIRI BANK will never ask for your password, PIN, or OTP over call or email.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def send_registration_received_email(to_email, full_name, customer_id, phone_number):
    """Sends email when user submits registration and waits for Admin approval."""
    subject = f"Registration Received - SIRI BANK (Ref: {customer_id})"
    headline = f"Welcome, {full_name}!"
    body = f"""
    <p>Thank you for choosing <strong>SIRI BANK</strong>. We have received your new account application along with your ID verification documents.</p>
    
    <div class="card">
        <div style="font-weight: 800; color: #0284c7; margin-bottom: 12px; font-size: 15px;">Application Summary</div>
        <div class="card-row"><span class="card-label">Applicant Name:</span><span class="card-value">{full_name}</span></div>
        <div class="card-row"><span class="card-label">Reference ID:</span><span class="card-value">{customer_id}</span></div>
        <div class="card-row"><span class="card-label">Mobile Number:</span><span class="card-value">+91-{phone_number}</span></div>
        <div class="card-row"><span class="card-label">Status:</span><span class="card-value" style="color: #d97706;">PENDING ADMIN APPROVAL</span></div>
    </div>

    <p>Our verification team is currently inspecting your uploaded Photo and ID Proof. Once approved, your bank account will be activated immediately and you will receive your official Account Number.</p>
    
    <div class="security-note">
        🔒 <strong>Application Tracking:</strong> You can check your live approval status anytime on the login page using your Reference ID or Mobile Number.
    </div>
    """
    html = get_base_email_template("Registration Received", headline, body, "APPLICATION UNDER REVIEW")
    return send_real_email(to_email, subject, html)

def send_account_approval_email(to_email, full_name, customer_id, account_number, upi_id, opening_balance="1,000.00"):
    """Sends congratulatory email when Admin approves the user account."""
    subject = f"🎉 Account Approved! Welcome to SIRI BANK (Acc: {account_number})"
    headline = f"Congratulations {full_name}, Your Account is Active!"
    body = f"""
    <p>We are delighted to inform you that your <strong>SIRI BANK</strong> savings account application has been <strong>APPROVED</strong> by the bank administration.</p>
    
    <div class="card" style="border-left: 4px solid #10b981;">
        <div style="font-weight: 800; color: #059669; margin-bottom: 12px; font-size: 15px;">Your Bank Account Credentials</div>
        <div class="card-row"><span class="card-label">Account Holder:</span><span class="card-value">{full_name}</span></div>
        <div class="card-row"><span class="card-label">Account Number:</span><span class="card-value" style="color: #0284c7; font-size: 16px;">{account_number}</span></div>
        <div class="card-row"><span class="card-label">Customer ID:</span><span class="card-value">{customer_id}</span></div>
        <div class="card-row"><span class="card-label">SIRI UPI ID:</span><span class="card-value">{upi_id}</span></div>
        <div class="card-row"><span class="card-label">IFSC Code:</span><span class="card-value">SIRI0008000</span></div>
        <div class="card-row"><span class="card-label">Opening Bonus Balance:</span><span class="card-value" style="color: #10b981;">₹{opening_balance}</span></div>
        <div class="card-row"><span class="card-label">Account Status:</span><span class="card-value" style="color: #059669;">ACTIVE</span></div>
    </div>

    <p style="text-align: center;">
        <a href="http://127.0.0.1:5000/login" class="btn">Sign In to Your Account</a>
    </p>

    <div class="security-note">
        🌟 <strong>Voice Banking Enabled:</strong> You can now use your AI Voice Assistant in both English and Kannada for instant transfers, bill payments, and balance checks.
    </div>
    """
    html = get_base_email_template("Account Approved", headline, body, "ACCOUNT ACTIVATION")
    return send_real_email(to_email, subject, html)

def send_account_rejection_email(to_email, full_name, reason):
    """Sends notification email if Admin rejects the application."""
    subject = "Update regarding your SIRI BANK application"
    headline = f"Notice regarding your Account Application"
    body = f"""
    <p>Dear {full_name},</p>
    <p>Thank you for applying for a SIRI BANK account. After inspecting your submitted documents, our verification desk was unable to approve your application at this time.</p>
    
    <div class="card" style="border-left: 4px solid #ef4444; background: #fff5f5;">
        <div style="font-weight: 800; color: #dc2626; margin-bottom: 8px; font-size: 14px;">Reason for Rejection:</div>
        <div style="color: #991b1b; font-size: 14px; font-weight: 600;">{reason}</div>
    </div>

    <p>You can re-apply anytime with updated or clearer identification proof and a clear profile photo.</p>
    
    <p style="text-align: center;">
        <a href="http://127.0.0.1:5000/login" class="btn" style="background: #475569;">Re-apply Online</a>
    </p>
    """
    html = get_base_email_template("Application Update", headline, body, "VERIFICATION UPDATE")
    return send_real_email(to_email, subject, html)

def send_transaction_email(to_email, full_name, tx_type, amount, balance, counterpart_info, description=""):
    """Sends real-time email notification when funds are debited or credited."""
    is_credit = (tx_type.upper() in ['CREDIT', 'DEPOSIT', 'TRANSFER_IN'])
    tx_title = "Credit Alert: Funds Received" if is_credit else "Debit Alert: Funds Transferred"
    color = "#10b981" if is_credit else "#ef4444"
    sign = "+" if is_credit else "-"
    
    subject = f"{'🟢' if is_credit else '🔴'} ₹{amount} {tx_type.lower()}ed - SIRI BANK Alert"
    headline = tx_title
    body = f"""
    <p>Dear {full_name},</p>
    <p>Your SIRI BANK account has undergone a recent transaction:</p>
    
    <div class="card" style="border-left: 4px solid {color};">
        <div style="font-size: 24px; font-weight: 900; color: {color}; margin-bottom: 12px;">{sign}₹{amount:,.2f}</div>
        <div class="card-row"><span class="card-label">Transaction Type:</span><span class="card-value">{tx_type.upper()}</span></div>
        <div class="card-row"><span class="card-label">Recipient / Source:</span><span class="card-value">{counterpart_info}</span></div>
        <div class="card-row"><span class="card-label">Description:</span><span class="card-value">{description or 'Transfer / Transaction'}</span></div>
        <div class="card-row"><span class="card-label">Available Balance:</span><span class="card-value" style="color: #0f172a; font-weight: 800;">₹{balance:,.2f}</span></div>
    </div>

    <div class="security-note">
        🛡️ If you did not authorize this transaction, please immediately freeze your account via Voice Assistant or contact SIRI BANK fraud desk.
    </div>
    """
    html = get_base_email_template(tx_title, headline, body, "TRANSACTION NOTIFICATION")
    return send_real_email(to_email, subject, html)

# ─────────────────────────────────────────────────────────────────────────────
# CARD APPLICATION & APPROVAL EMAIL NOTIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def send_card_application_received_email(to_email, full_name, card_details="Visa Platinum Debit Card"):
    """Sends email when user requests an ATM Debit Card (Status: PENDING)."""
    subject = f"Debit Card Request Received (Status: PENDING) - SIRI BANK"
    headline = "Debit Card Request Submitted"
    body = f"""
    <p>Dear {full_name},</p>
    <p>We have successfully received your request for a new <strong>SIRI BANK Debit Card</strong>.</p>
    
    <div class="card" style="border-left: 4px solid #f59e0b;">
        <div style="font-weight: 800; color: #d97706; margin-bottom: 12px; font-size: 15px;">Application Summary</div>
        <div class="card-row"><span class="card-label">Card Holder:</span><span class="card-value">{full_name}</span></div>
        <div class="card-row"><span class="card-label">Card Type / Request:</span><span class="card-value">{card_details}</span></div>
        <div class="card-row"><span class="card-label">Status:</span><span class="card-value" style="color: #d97706; font-weight: 800;">PENDING ADMIN APPROVAL</span></div>
    </div>

    <p>Your request is being reviewed by the bank administration. Once approved, your personalized ATM debit card will be dispatched to your registered address.</p>
    
    <div class="security-note">
        🔒 You can check the live status of your card request in your <strong>Request History</strong> tab anytime.
    </div>
    """
    html = get_base_email_template("Debit Card Request", headline, body, "CARD REQUEST PENDING")
    return send_real_email(to_email, subject, html)

def send_card_approval_email(to_email, full_name, card_details="Visa Platinum Debit Card"):
    """Sends email when Admin approves the Debit Card request."""
    subject = f"🎉 Debit Card Approved & Dispatched! - SIRI BANK"
    headline = "Congratulations, Your Debit Card is Approved!"
    body = f"""
    <p>Dear {full_name},</p>
    <p>We are pleased to inform you that your <strong>SIRI BANK Debit Card</strong> application has been <strong>APPROVED</strong> by the bank administration.</p>
    
    <div class="card" style="border-left: 4px solid #10b981;">
        <div style="font-weight: 800; color: #059669; margin-bottom: 12px; font-size: 15px;">Card Issuance & Dispatch Details</div>
        <div class="card-row"><span class="card-label">Card Holder:</span><span class="card-value">{full_name}</span></div>
        <div class="card-row"><span class="card-label">Card Details:</span><span class="card-value">{card_details}</span></div>
        <div class="card-row"><span class="card-label">Card Status:</span><span class="card-value" style="color: #10b981; font-weight: 800;">APPROVED &amp; DISPATCHED</span></div>
        <div class="card-row"><span class="card-label">Estimated Delivery:</span><span class="card-value">3 - 5 Business Days</span></div>
    </div>

    <p>Once delivered, you can set your ATM PIN and control international/contactless limits directly from your account or by speaking to your AI Voice Assistant.</p>
    
    <div class="security-note">
        🛡️ For security, your card is delivered in a sealed envelope. Never share your card number, CVV, or OTP with anyone.
    </div>
    """
    html = get_base_email_template("Debit Card Approved", headline, body, "CARD APPROVED & DISPATCHED")
    return send_real_email(to_email, subject, html)

def send_card_rejection_email(to_email, full_name, reason="Application did not meet requirements"):
    """Sends email when Admin rejects the Debit Card request."""
    subject = f"Update regarding your Debit Card Request - SIRI BANK"
    headline = "Notice regarding your Debit Card Application"
    body = f"""
    <p>Dear {full_name},</p>
    <p>Thank you for requesting a SIRI BANK Debit Card. After review, our administration was unable to approve your application at this time.</p>
    
    <div class="card" style="border-left: 4px solid #ef4444; background: #fff5f5;">
        <div style="font-weight: 800; color: #dc2626; margin-bottom: 8px; font-size: 14px;">Reason for Non-Approval:</div>
        <div style="color: #991b1b; font-size: 14px; font-weight: 600;">{reason}</div>
    </div>

    <p>You can re-apply anytime from your ATM services tab once your account requirements are fulfilled.</p>
    """
    html = get_base_email_template("Debit Card Update", headline, body, "REQUEST UPDATE")
    return send_real_email(to_email, subject, html)

# ─────────────────────────────────────────────────────────────────────────────
# AADHAAR KYC SUBMISSION & APPROVAL EMAIL NOTIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def send_kyc_submission_received_email(to_email, full_name, aadhaar_number=""):
    """Sends email when user submits Aadhaar KYC (Status: PENDING)."""
    masked_aadhaar = f"XXXX-XXXX-{str(aadhaar_number)[-4:]}" if aadhaar_number and len(str(aadhaar_number)) >= 4 else "Submitted"
    subject = f"Aadhaar KYC Submitted (Status: PENDING) - SIRI BANK"
    headline = "Aadhaar KYC Verification Under Review"
    body = f"""
    <p>Dear {full_name},</p>
    <p>We have successfully received your <strong>Aadhaar KYC Verification</strong> submission including identity proof and biometric face scan.</p>
    
    <div class="card" style="border-left: 4px solid #3b82f6;">
        <div style="font-weight: 800; color: #2563eb; margin-bottom: 12px; font-size: 15px;">KYC Submission Summary</div>
        <div class="card-row"><span class="card-label">Customer Name:</span><span class="card-value">{full_name}</span></div>
        <div class="card-row"><span class="card-label">Aadhaar Reference:</span><span class="card-value">{masked_aadhaar}</span></div>
        <div class="card-row"><span class="card-label">Status:</span><span class="card-value" style="color: #d97706; font-weight: 800;">PENDING ADMIN VERIFICATION</span></div>
    </div>

    <p>Our verification team is inspecting your Aadhaar details and facial liveness confirmation. You will receive an official notification once verification is complete.</p>
    
    <div class="security-note">
        🔒 All biometric and identity records are transmitted under 256-bit encryption compliant with RBI and UIDAI standards.
    </div>
    """
    html = get_base_email_template("KYC Verification", headline, body, "KYC UNDER VERIFICATION")
    return send_real_email(to_email, subject, html)

def send_kyc_approval_email(to_email, full_name):
    """Sends email when Admin approves the Aadhaar KYC request."""
    subject = f"✅ Aadhaar KYC Verified & Approved! - SIRI BANK"
    headline = "Congratulations, Your KYC is Complete!"
    body = f"""
    <p>Dear {full_name},</p>
    <p>We are delighted to confirm that your <strong>Aadhaar KYC Verification</strong> has been successfully <strong>APPROVED</strong> by SIRI BANK compliance.</p>
    
    <div class="card" style="border-left: 4px solid #10b981;">
        <div style="font-weight: 800; color: #059669; margin-bottom: 12px; font-size: 15px;">Account Verification Privileges</div>
        <div class="card-row"><span class="card-label">Account Holder:</span><span class="card-value">{full_name}</span></div>
        <div class="card-row"><span class="card-label">KYC Status:</span><span class="card-value" style="color: #10b981; font-weight: 800;">VERIFIED &amp; COMPLIANT</span></div>
        <div class="card-row"><span class="card-label">Daily Transfer Limit:</span><span class="card-value">₹5,00,000.00</span></div>
        <div class="card-row"><span class="card-label">ATM Cash Limit:</span><span class="card-value">₹1,00,000.00 / day</span></div>
    </div>

    <p>With full KYC verification completed, your account is now free of all limits. You can make instant high-value transfers, open Fixed Deposits, and use all banking services hands-free.</p>
    """
    html = get_base_email_template("KYC Approved", headline, body, "KYC FULLY VERIFIED")
    return send_real_email(to_email, subject, html)

def send_kyc_rejection_email(to_email, full_name, reason="Aadhaar document verification failed"):
    """Sends email when Admin rejects the Aadhaar KYC request."""
    subject = f"Aadhaar KYC Verification Update - SIRI BANK"
    headline = "Action Required on your Aadhaar KYC"
    body = f"""
    <p>Dear {full_name},</p>
    <p>Thank you for submitting your Aadhaar KYC documents. Our verification desk reviewed your submission and was unable to complete verification at this time.</p>
    
    <div class="card" style="border-left: 4px solid #ef4444; background: #fff5f5;">
        <div style="font-weight: 800; color: #dc2626; margin-bottom: 8px; font-size: 14px;">Reason for Non-Approval:</div>
        <div style="color: #991b1b; font-size: 14px; font-weight: 600;">{reason}</div>
    </div>

    <p>You can re-attempt Aadhaar KYC verification anytime with clear identity details and well-lit camera liveness.</p>
    
    <p style="text-align: center;">
        <a href="http://127.0.0.1:5000/aadhaar-kyc?retry=true" class="btn">Retry KYC Verification</a>
    </p>
    """
    html = get_base_email_template("KYC Update", headline, body, "KYC ACTION REQUIRED")
    return send_real_email(to_email, subject, html)

