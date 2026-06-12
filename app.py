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
# Use Environment Variables in Render settings for these!
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") 
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# Use the /tmp directory for cloud-compatible read/write access
DB_FILE = "/tmp/database.db"

# --- HELPER FUNCTIONS ---

def send_receipt_email(recipient_email, quantity, color, location, mpesa_code, total_amount):
    """Utility function to compile and transmit the receipt email."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ SMTP Config Error: Email credentials not set.")
        return False

    recipient_email = str(recipient_email or "").strip()
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
        Quantity: {quantity}
        Color: {color}
        Total: {total_amount}
        Destination: {location}

        --- PAYMENT TRACKING ---
        M-Pesa Code: {mpesa_code}

        Best regards,
        The Innovation Hub Logistics Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        return False

def init_db():
    """Builds structural schema safely on app initialization."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, quantity INTEGER NOT NULL, color TEXT NOT NULL, location TEXT NOT NULL, mpesa_code TEXT NOT NULL UNIQUE, total_amount TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS products (product_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL)')
        cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (1, 'Iris Pro Smart Glasses', 150.00)")
        conn.commit()

# --- REST API CONTROLLERS ---

@app.route('/api/register', methods=['POST'])
def register():
    try:
        init_db()
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
            
        full_name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)", 
                           (full_name, email, generate_password_hash(password)))
            conn.commit()
        return jsonify({"status": "success", "message": "Account created!"}), 201
        
    except Exception as e:
        # This print statement is the KEY. 
        # It sends the real error to your Render 'Logs' tab.
        print(f"CRITICAL ERROR IN REGISTER: {str(e)}") 
        return jsonify({"status": "error", "message": str(e)}), 500
        
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = str(data.get('email') or "").strip().lower()
    password = str(data.get('password') or "")
    
    with sqlite3.connect(DB_FILE) as conn:
        user = conn.cursor().execute("SELECT password, full_name FROM users WHERE email = ?", (email,)).fetchone()
        
    if user and check_password_hash(user[0], password):
        return jsonify({"status": "success", "message": f"Welcome, {user[1]}!"}), 200
    return jsonify({"status": "error", "message": "Invalid credentials."}), 401

@app.route('/api/purchase', methods=['POST'])
def purchase():
    data = request.json or {}
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.cursor().execute("INSERT INTO orders (email, quantity, color, location, mpesa_code, total_amount) VALUES (?, ?, ?, ?, ?, ?)",
                                (data['email'], data['quantity'], data['color'], data['location'], data['mpesa_code'], data['total_amount']))
            conn.commit()
        send_receipt_email(data['email'], data['quantity'], data['color'], data['location'], data['mpesa_code'], data['total_amount'])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
