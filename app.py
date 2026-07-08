from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ============================================
# INITIALIZE FLASK APP
# ============================================

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://127.0.0.1:5500",
            "http://localhost:5500",
            "https://calebmunyeks002.github.io"
        ]
    }
})

# ============================================
# CONFIGURATION
# ============================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# Database path (Works on Windows and Render)

if os.name == "nt":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_FILE = os.path.join(BASE_DIR, "database.db")
else:
    DB_FILE = "/tmp/database.db"


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            color TEXT NOT NULL,
            location TEXT NOT NULL,
            mpesa_code TEXT NOT NULL UNIQUE,
            total_amount TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products(
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
        """)

        cursor.execute("""
        INSERT OR IGNORE INTO products(product_id, name, price)
        VALUES (1, 'Iris Pro Smart Glasses', 150.00)
        """)

        conn.commit()


# ============================================
# EMAIL FUNCTION
# ============================================

def send_receipt_email(recipient_email, quantity, color, location, mpesa_code, total_amount):

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Email credentials not configured.")
        return False

    try:
        msg = MIMEMultipart()

        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = f"Order Receipt - {mpesa_code}"

        body = f"""
Hello,

Thank you for purchasing from AI Smart Glasses Systems.

Order Summary
-------------------------
Product : Iris Pro Smart Glasses
Quantity: {quantity}
Color   : {color}
Total   : {total_amount}

Delivery Location:
{location}

M-Pesa Code:
{mpesa_code}

Thank you for your purchase.

AI Smart Glasses Systems
"""

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print("Email Error:", e)
        return False


# ============================================
# REGISTER
# ============================================

@app.route("/api/register", methods=["POST"])
def register():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data received."
            }), 400

        full_name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not full_name or not email or not password:
            return jsonify({
                "status": "error",
                "message": "All fields are required."
            }), 400

        with sqlite3.connect(DB_FILE) as conn:

            cursor = conn.cursor()

            existing = cursor.execute(
                "SELECT user_id FROM users WHERE email=?",
                (email,)
            ).fetchone()

            if existing:
                return jsonify({
                    "status": "error",
                    "message": "Email already exists."
                }), 409

            cursor.execute(
                """
                INSERT INTO users(full_name,email,password)
                VALUES(?,?,?)
                """,
                (
                    full_name,
                    email,
                    generate_password_hash(password)
                )
            )

            conn.commit()

        return jsonify({
            "status": "success",
            "message": "Account created successfully."
        }), 201

    except Exception as e:

        print(e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================
# LOGIN
# ============================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        with sqlite3.connect(DB_FILE) as conn:

            cursor = conn.cursor()

            user = cursor.execute(
                """
                SELECT full_name,password
                FROM users
                WHERE email=?
                """,
                (email,)
            ).fetchone()

        if user and check_password_hash(user[1], password):

            return jsonify({
                "status": "success",
                "message": f"Welcome {user[0]}!"
            }), 200

        return jsonify({
            "status": "error",
            "message": "Invalid email or password."
        }), 401

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================
# PURCHASE
# ============================================

@app.route("/api/purchase", methods=["POST"])
def purchase():

    try:

        data = request.get_json()

        with sqlite3.connect(DB_FILE) as conn:

            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO orders(
                email,
                quantity,
                color,
                location,
                mpesa_code,
                total_amount
            )
            VALUES(?,?,?,?,?,?)
            """, (

                data["email"],
                data["quantity"],
                data["color"],
                data["location"],
                data["mpesa_code"],
                data["total_amount"]

            ))

            conn.commit()

        send_receipt_email(
            data["email"],
            data["quantity"],
            data["color"],
            data["location"],
            data["mpesa_code"],
            data["total_amount"]
        )

        return jsonify({
            "status": "success",
            "message": "Purchase completed successfully."
        }), 200

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


# ============================================
# HOME
# ============================================

@app.route("/")
def home():
    return "AI Smart Glasses Systems Backend is running successfully."


# ============================================
# START SERVER
# ============================================

if __name__ == "__main__":

    init_db()

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )