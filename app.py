from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import os

# 1. INITIALIZE ENGINE
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [
    "http://127.0.0.1:5500", 
    "http://localhost:5500", 
    "https://calebmunyeks002.github.io"
]}}) 

# 2. APPLICATION CONFIGURATIONS
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-business-email@gmail.com"  # Replace with your email address
SENDER_PASSWORD = "your-app-password"           # Replace with your 16-character Google App Password

# Dynamically calculates the absolute folder path where app.py lives
# New robust cloud path configuration:
# Using the /tmp directory guarantees unrestricted write permissions on Render
DB_FILE = "/tmp/database.db"

# --- HELPER FUNCTIONS ---

def send_receipt_email(recipient_email, quantity, color, location, mpesa_code, total_amount):
    """Utility function to compile and transmit the receipt email including M-Pesa code."""
    recipient_email = str(recipient_email or "").strip()
    if not recipient_email or "@" not in recipient_email:
        print("❌ SMTP Abort: Recipient address format is completely invalid.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = f"📦 Order Confirmed - Receipt {mpesa_code}"

        body = f"""
        Hello,

        Thank you for choosing Smart Systems! Your order request has been logged successfully.

        --- ORDER RECAP ---
        Item: Iris Pro Smart Glasses
        Quantity Ordered: {quantity}
        Selected Color: {color}
        Total Amount: {total_amount}
        Delivery Destination: {location}
        Estimated Arrival: 2 to 4 working days

        --- PAYMENT TRACKING ---
        M-Pesa Confirmation Code: {mpesa_code}
        Sent To Line: 0729370661

        Our accounting team is cross-referencing your code ({mpesa_code}) against our payment gateway logs. 
        Your package will enter our dispatch routing stream immediately upon clearance.

        If you have any questions or typed your code incorrectly, please reply directly using our web space contact form.

        Best regards,
        The Innovation Hub Logistics Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"✅ Order receipt email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ SMTP Error encountered: {e}")
        return False

def init_db():
    """Builds structural schema safely on app initialization startup."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                color TEXT NOT NULL,
                location TEXT NOT NULL,
                mpesa_code TEXT NOT NULL UNIQUE,
                total_amount TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (1, 'Iris Pro Smart Glasses', 150.00)")
        conn.commit()


# --- REST API CONTROLLERS ---

@app.route('/api/register', methods=['POST'])
def register():
    # 1. Force database initialization to run immediately to ensure tables exist
    try:
        init_db()
    except Exception as db_err:
        return jsonify({"status": "error", "message": f"Database structural build failed: {str(db_err)}"}), 500

    data = request.json or {}
    full_name = str(data.get('name') or data.get('full_name') or "").strip()
    email = str(data.get('email') or "").strip().lower()
    password = str(data.get('password') or "")

    if not full_name or not email or not password:
        return jsonify({"status": "error", "message": "All fields are required for registration."}), 400

    hashed_password = generate_password_hash(password)

    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)",
                (full_name, email, hashed_password)
            )
            conn.commit()
        print(f"👤 Account Registered successfully: {email}")
        return jsonify({"status": "success", "message": "Account created successfully!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "This email address is already registered."}), 400
    except Exception as general_err:
        # 2. ✅ CRUCIAL: Capture and stream back the exact internal Python crash trace
        return jsonify({"status": "error", "message": f"Internal Database Write Error: {str(general_err)}"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = str(data.get('email') or "").strip().lower()
    password = str(data.get('password') or "")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required."}), 400

    print(f"🔑 Login Attempt received for account: {email}")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Bulletproof Fix: Explicitly ask for columns by name so index mismatches never break hashing checks
        cursor.execute("SELECT password, full_name FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
    if user and check_password_hash(user[0], password):
        print(f"✅ Verification Passed for {email}")
        return jsonify({"status": "success", "message": f"Welcome back, {user[1]}!", "user_email": email}), 200
    else:
        print(f"❌ Verification Failed for {email}")
        return jsonify({"status": "error", "message": "Invalid email or password sequence checked."}), 401


@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json or {}
    email = str(data.get('email') or "").strip().lower()

    if not email:
        return jsonify({"status": "error", "message": "Email address parameter is required."}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

    if not user:
        return jsonify({"status": "error", "message": "This email is not registered inside our system logs."}), 404

    user_name = user[0]
    char_pool = string.ascii_uppercase + string.digits
    temporary_pass = ''.join(random.choice(char_pool) for _ in range(8))
    hashed_temp_pass = generate_password_hash(temporary_pass)

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_temp_pass, email))
        conn.commit()

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "🔐 Urgent: Temporary Access Password Generated"

        body = f"""
        Hello {user_name},

        A password reset process was initialized for your account profile on AI Smart Systems.

        Your account access code has been updated to this temporary sequence:
        🔑 TEMPORARY PASSWORD: {temporary_pass}

        Please log into the platform space immediately using this value string.

        Best regards,
        The Innovation Hub Core Security Engine
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()

        return jsonify({"status": "success", "message": f"A temporary password has been successfully routed to {email}."}), 200
    except Exception as e:
        print(f"❌ Forgot Password SMTP Delivery failure: {e}")
        return jsonify({"status": "error", "message": "System could not execute SMTP email dispatch pipeline."}), 500


@app.route('/api/purchase', methods=['POST'])
def purchase():
    data = request.json or {}
    user_email = str(data.get('email') or "").strip().lower()
    quantity = data.get('quantity', 1)
    color = data.get('color', 'Default')
    location = str(data.get('location') or "").strip()
    mpesa_code = str(data.get('mpesa_code') or "").upper().strip() 
    total_amount = data.get('total_amount')
    
    if not user_email or not mpesa_code or not location:
        return jsonify({"status": "error", "message": "Missing critical fields (Email, M-Pesa, or Location)."}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO orders (email, quantity, color, location, mpesa_code, total_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_email, quantity, color, location, mpesa_code, total_amount))
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "This M-Pesa code has already been processed for an order!"}), 400

    email_success = send_receipt_email(user_email, quantity, color, location, mpesa_code, total_amount)
    
    if email_success:
        return jsonify({"status": "success", "message": "Order tracked and receipt email dispatched successfully!"}), 200
    else:
        return jsonify({"status": "partial_success", "message": "Order registered in database, but verification email failed to deliver."}), 200

@app.route('/api/admin/clear-test-accounts', methods=['GET'])
def clear_test_accounts():
    """Hidden testing API utility routine to instantly clear target accounts for structural re-registration testing."""
    target_emails = ["calebmunyeks002@gmail.com", "reinhardkalesh@gmail.com"]
    cleared = []
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            for email in target_emails:
                cursor.execute("DELETE FROM users WHERE email = ?", (email,))
                cleared.append(email)
            conn.commit()
        return jsonify({"status": "success", "message": f"Wiped developer test credentials successfully! Cleared profiles: {cleared}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database administrative write fail pipeline break: {str(e)}"}), 500
    
if __name__ == '__main__':
    init_db()
    
    # ✅ Tell Flask to accept the dynamic port assigned by Render's environment
    # If it runs locally on your computer, it defaults back to 5000 automatically
    port = int(os.environ.get("PORT", 5000))
    
    # ✅ Bind to 0.0.0.0 so external cloud traffic can reach your app endpoints
    # Turn off debug mode for production security
    app.run(host="0.0.0.0", port=port, debug=False)
