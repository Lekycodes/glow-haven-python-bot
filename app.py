# -------Imports ------ #
import sys
import os
import json
import random
import mysql.connector
import time
from datetime import datetime
from fpdf import FPDF
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from flask import Flask, request

# -------------------- Load Environment Variables -------------------- #
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_WHATSAPP_NUMBER is typically not used for the webhook, but kept for clarity
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") 

# SALON_MEDIA_URL = "https://videos.pexels.com/video-files/3847844/3847844-hd_1920_1080_30fps.mp4"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DATABASE = os.getenv("DB_DATABASE", "glow_haven")

# Check for essential Twilio credentials 
if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    print("FATAL ERROR: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set in .env file.")
    sys.exit(1)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ----- Global DB and Cursor  ---- #
db = None
cursor = None

def get_db_connection():
    """Initializes or returns the global database connection and cursor."""
    global db, cursor
    try:
        # Check if connection exists and is still active
        if db and db.is_connected():
            return db, cursor
        
        print("Database connection not active or needs initialization. Connecting...")
        # Attempt to establish a new connection
        db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = db.cursor(dictionary=True)
        return db, cursor
        
    except mysql.connector.Error as err:
        print(f"FATAL DATABASE ERROR: Cannot connect to MySQL: {err}")
        # In a production environment, you might just log and return None,
        # but for this assignment, we maintain the exit on critical failure.
        sys.exit(1)

# Initialize the connection upon startup
get_db_connection()


# -------------------- Utility Functions -------------------- #
def get_main_menu_message():
    """Returns the standardized main menu message with enhanced look and feel."""
    return (
        "💅 *How can I serve your beauty needs today?*\n"
        "\n"
        "1️⃣ **Chat:** General Info (Services, Hours, Location)\n"
        "2️⃣ **Book:** Schedule an Appointment\n"
        "3️⃣ **Pay:** Settle Your Deposit\n"
        "4️⃣ **Review:** Give Us Your Feedback"
    )

# -------------------- Session Functions -------------------- #
# All DB functions now rely on the global 'cursor' and 'db' which are managed by get_db_connection()

def get_session(phone_number):
    """Retrieves session data for a given phone number. Using 'phone_number' as column name."""
    global cursor
    try:
        cursor.execute("SELECT * FROM sessions WHERE phone_number=%s", (phone_number,))
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"SESSION DB ERROR (get_session): Failed to retrieve session for {phone_number}. Error: {err}")
        return None

def save_session(phone_number, state, temp_data):
    """Saves or updates session state and temporary data. Using 'phone_number' as column name."""
    global db, cursor
    try:
        temp_json = json.dumps(temp_data)
        cursor.execute("""
            INSERT INTO sessions(phone_number, current_state, temp_data)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE current_state=%s, temp_data=%s
        """, (phone_number, state, temp_json, state, temp_json))
        db.commit()
    except mysql.connector.Error as err:
        print(f"SESSION DB ERROR (save_session): Failed to save session for {phone_number}. Error: {err}")
        db.rollback()

# -------------------- PDF Generation -------------------- #
def generate_pdf_receipt(booking_id):
    """
    Generates a PDF receipt and saves it locally. 
    NOTE: This is a BLOCKING I/O operation and is the main reason for latency.
    """
    global cursor
    try:
        cursor.execute("""
            SELECT b.id, b.user_name, b.phone_number, b.booking_time, b.deposit_paid,
                   s.name as service_name, s.price as service_price
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            WHERE b.id=%s
        """, (booking_id,))
        booking = cursor.fetchone()

        if not booking:
             print(f"Error: Booking ID {booking_id} not found for PDF generation.")
             return None
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Glow Haven Beauty Lounge Receipt", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.ln(10)
        
        pdf.cell(0, 7, f"Booking Receipt - ID: {booking['id']}", ln=True)
        pdf.cell(0, 7, f"Name: {booking['user_name']}", ln=True)
        pdf.cell(0, 7, f"Phone: {booking['phone_number']}", ln=True)
        pdf.cell(0, 7, f"Service: {booking['service_name']} (KES {booking['service_price']:.2f})", ln=True)
        pdf.cell(0, 7, f"Booking Time: {booking['booking_time']}", ln=True)
        pdf.cell(0, 7, f"Deposit Paid: KES {booking['deposit_paid']:.2f}", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 5, "Thank you for booking with us!", ln=True, align='C')
        
        filename = f"receipt_{booking_id}.pdf"
        
        # This line is the biggest delay factor.
        pdf.output(filename) 
        
        return filename
    except Exception as e:
        print(f"Error generating PDF for Booking ID {booking_id}: {e}")
        return None

# -------------------- Payment Simulation -------------------- #
def process_payment(booking_id, amount):
    """Simulates a payment and updates the booking record."""
    global db, cursor
    try:
        transaction_id = "TXN" + str(random.randint(100000, 999999))
        
        cursor.execute(
            "INSERT INTO payments(booking_id, amount, payment_date, transaction_id) VALUES (%s,%s,NOW(),%s)",
            (booking_id, amount, transaction_id)
        )
        
        cursor.execute(
            "UPDATE bookings SET deposit_paid=%s WHERE id=%s",
            (amount, booking_id)
        )
        db.commit()
        return transaction_id
    except mysql.connector.Error as err:
        print(f"Database error during payment processing: {err}")
        db.rollback()
        return None

# -------------------- Flask App -------------------- #
app = Flask(__name__)

# -------------------- WhatsApp Webhook -------------------- #
@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    """Handles incoming WhatsApp messages from Twilio."""
    global db, cursor
    
    incoming_msg = request.values.get('Body', '').strip()
    phone_number = request.values.get('From', '')

    resp = MessagingResponse()
    msg = resp.message()

    # CRITICAL SPEED IMPROVEMENT.
    try:
        db, cursor = get_db_connection()
    except SystemExit:
        msg.body("Service unavailable. Database connection could not be established.")
        return str(resp)

    session = get_session(phone_number)

    # -------------------- New User (Basic Welcome) -------------------- #
    if not session:
        save_session(phone_number, 'menu', {})
        
        # Reverting to basic welcome message and menu, removing media URL
        msg.body(
            f"Welcome to Glow Haven Beauty Lounge! Please choose an option below:\n"
            f"{get_main_menu_message()}"
        )
        return str(resp)

    state = session['current_state']
    
    try:
        temp_data_raw = session['temp_data']
        if temp_data_raw:
            temp_data = json.loads(temp_data_raw)
        else:
            temp_data = {}
    except json.JSONDecodeError:
        temp_data = {}
        save_session(phone_number, 'menu', temp_data)
        msg.body("An error occurred with your previous session. Starting over. Please choose an option.")
        return str(resp)

    user_input = incoming_msg.lower()

    # Handle 'menu' input from any state to restart
    if user_input in ['menu', 'start', 'main menu']:
        save_session(phone_number, 'menu', {})
        msg.body(f"Returning to the main menu.\n{get_main_menu_message()}")
        return str(resp)

    # -------------------- Main Menu -------------------- #
    if state == 'menu':
        if user_input in ['1', 'general', 'questions', 'chat', 'general questions']:
            save_session(phone_number, 'general_questions_menu', {})
            msg.body(
                "What sparkling detail can I share?\n\n"
                "1️⃣ 💖 View Our Services\n"
                "2️⃣ 🕰️ Opening Hours\n"
                "3️⃣ 📍 Our Location\n\n"
                "_Reply 'menu' to go back._"
            )
        elif user_input in ['2', 'book', 'appointment']:
            save_session(phone_number, 'booking_name', {})
            msg.body("Great! Let's get you booked. Please enter your full name. _Reply 'menu' to cancel._")
        elif user_input in ['3', 'pay', 'deposit']:
            save_session(phone_number, 'pay_deposit', {})
            msg.body("Ready to pay your deposit? Please enter your **Booking ID**.")
        elif user_input in ['4', 'feedback', 'review']:
            save_session(phone_number, 'feedback_booking', {})
            msg.body("We'd love to hear from you! Please enter your **Booking ID** to start the feedback process.")
        else:
            msg.body("Option not recognized. Please choose 1️⃣, 2️⃣, 3️⃣, or 4️⃣ from the menu.")

    # -------------------- General Questions Flow (No major change needed here) -------------------- #
    elif state == 'general_questions_menu':
        if user_input in ['1', 'services']:
            try:
                cursor.execute("SELECT id, name, price FROM services ORDER BY id")
                services = cursor.fetchall()
                
                if services:
                    reply = "✨ *Glow Haven Service Menu* ✨\n\n" + "\n".join([f"*{s['id']}*. {s['name']} - KES *{s['price']:.2f}*" for s in services])
                    msg.body(f"{reply}\n\n_Anything else? Select from the menu below:_\n{get_main_menu_message()}")
                else:
                    msg.body(f"Sorry, no services are currently listed. We're updating our menu! 😔\n\n{get_main_menu_message()}")
            except mysql.connector.Error as e:
                print(f"DB Error fetching services: {e}")
                msg.body(f"A database error prevented fetching services. Please try again later.\n\n{get_main_menu_message()}")
            finally:
                save_session(phone_number, 'menu', {})

        elif user_input in ['2', 'hours', 'opening hours']:
            msg.body(f"🕰️ *Opening Hours:*\nWe are open **Monday to Saturday** from *9:00 AM to 7:00 PM*. We rest on Sundays! 🧘‍♀️\n\n{get_main_menu_message()}")
            save_session(phone_number, 'menu', {})

        elif user_input in ['3', 'location', 'address']:
            msg.body(f"📍 *Our Location:*\nFind us at **456 Beauty Avenue**, right next to the Central Mall in Nairobi. We can't wait to see you! 🗺️\n\n{get_main_menu_message()}")
            save_session(phone_number, 'menu', {})

        else:
            msg.body("Option not recognized. Please choose 1️⃣ (Services), 2️⃣ (Hours), or 3️⃣ (Location). _Reply 'menu' to go back._")


    # -------------------- Booking Flow (No major change needed here) -------------------- #
    elif state == 'booking_name':
        if len(incoming_msg.strip()) < 3:
            msg.body("Please enter your full name (at least 3 characters). _Reply 'menu' to cancel:_")
            return str(resp)
            
        temp_data['user_name'] = incoming_msg.title()
        save_session(phone_number, 'booking_service', temp_data)
        
        try:
            cursor.execute("SELECT id, name, price FROM services ORDER BY id")
            services = cursor.fetchall()
            service_list = "\n".join([f"*{s['id']}*. {s['name']} - KES *{s['price']:.2f}*" for s in services])
            msg.body(f"Excellent, {temp_data['user_name']}! Now, which service are you booking?\n\n{service_list}\n\n*Select a service by entering its ID.* _Reply 'menu' to cancel:_")
        except mysql.connector.Error:
            msg.body("Could not retrieve services. Returning to menu.")
            save_session(phone_number, 'menu', {})

    elif state == 'booking_service':
        if not user_input.isdigit():
            msg.body("Invalid input. Please enter the *numeric ID* of the service you want. _Reply 'menu' to cancel:_")
            return str(resp)
        
        service_id = int(user_input)
        cursor.execute("SELECT id FROM services WHERE id=%s", (service_id,))
        if not cursor.fetchone():
            msg.body(f"Service ID {service_id} not found. Please select a valid ID. _Reply 'menu' to cancel:_")
            return str(resp)

        temp_data['service_id'] = service_id
        save_session(phone_number, 'booking_datetime', temp_data)
        msg.body("Service selected! ✨ Please send your preferred booking date and time using this format: **YYYY-MM-DD HH:MM** (e.g., 2025-11-20 15:30). _Reply 'menu' to cancel:_")

    elif state == 'booking_datetime':
        try:
            datetime.strptime(incoming_msg, "%Y-%m-%d %H:%M")
            
            temp_data['booking_time'] = incoming_msg
            save_session(phone_number, 'booking_confirm', temp_data)
            
            cursor.execute("SELECT name FROM services WHERE id=%s", (temp_data['service_id'],))
            service_name = cursor.fetchone()['name']
            
            msg.body(
                f"📝 *Please Review Your Booking:*\n"
                f"👤 **Name:** {temp_data['user_name']}\n"
                f"🛠️ **Service:** {service_name}\n"
                f"⏰ **Time:** {temp_data['booking_time']}\n\n"
                "Ready to finalize? Reply **'yes'** to confirm or **'no'** to cancel. _Reply 'menu' to return to the main menu._"
            )
        except ValueError:
            msg.body("Invalid datetime format. Please use the exact format: **YYYY-MM-DD HH:MM** (e.g., 2025-11-20 15:30). _Reply 'menu' to cancel:_")
        except mysql.connector.Error as e:
            print(f"DB Error on service name lookup: {e}")
            msg.body("A database error occurred. Returning to menu.")
            save_session(phone_number, 'menu', {})

    elif state == 'booking_confirm':
        if user_input == 'yes':
            try:
                cursor.execute(
                    "INSERT INTO bookings(user_name, phone_number, service_id, booking_time, deposit_paid) VALUES (%s,%s,%s,%s,%s)",
                    (temp_data['user_name'], phone_number, temp_data['service_id'], temp_data['booking_time'], 0)
                )
                db.commit()
                cursor.execute("SELECT LAST_INSERT_ID() as booking_id")
                booking_id = cursor.fetchone()['booking_id']
                save_session(phone_number, 'menu', {})
                msg.body(
                    f"🎉 *Hooray! Booking Confirmed!* 🎉\n"
                    f"Your Booking ID is: *{booking_id}*\n"
                    "Please remember to pay your deposit to secure this slot (Option 3). See you soon!\n\n"
                    "--- Main Menu ---\n"
                    f"{get_main_menu_message()}"
                )
            except mysql.connector.Error as e:
                print(f"DB Error on booking insert: {e}")
                msg.body("A database error prevented booking confirmation. Returning to main menu.")
                save_session(phone_number, 'menu', {})
        else:
            msg.body(f"❌ Booking cancelled. Returning to main menu.\n{get_main_menu_message()}")
            save_session(phone_number, 'menu', {})

    # -------------------- Payment Flow (Optimized for Speed) -------------------- #
    elif state == 'pay_deposit':
        if not user_input.isdigit():
            msg.body("Booking ID must be numeric. Enter a valid Booking ID.")
            return str(resp)
            
        booking_id = int(user_input)
        
        try:
            cursor.execute("SELECT id, deposit_paid FROM bookings WHERE id=%s", (booking_id,))
            booking_check = cursor.fetchone()
            
            if not booking_check:
                msg.body("Booking ID not found. Enter a valid Booking ID.")
                return str(resp)

            if booking_check['deposit_paid'] > 0:
                 msg.body(f"Booking ID *{booking_id}* already has a deposit paid (KES {booking_check['deposit_paid']:.2f}). Returning to main menu.\n{get_main_menu_message()}")
                 save_session(phone_number, 'menu', {})
                 return str(resp)
            
            temp_data['booking_id'] = booking_id
            temp_data['amount_suggested'] = 500  # suggested deposit
            save_session(phone_number, 'pay_amount', temp_data)
            
            msg.body(
                f"We are processing the deposit for Booking ID *{booking_id}*.\n"
                f"The minimum deposit is KES {temp_data['amount_suggested']:.2f}.\n"
                "*Payment is assumed to be completed via Pochi la Biashara.* Please enter the **amount** you have paid."
            )
        except mysql.connector.Error as e:
            print(f"DB Error on deposit lookup: {e}")
            msg.body("A database error occurred. Returning to menu.")
            save_session(phone_number, 'menu', {})

    elif state == 'pay_amount':
        try:
            amount = float(incoming_msg)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
            
            # 1. Process Payment - FAST DB UPDATE
            transaction_id = process_payment(temp_data['booking_id'], amount)
            
            if transaction_id:
                # 2. SPEED IMPROVEMENT: Send the successful message immediately (low latency)
                msg.body(f"💰 *Deposit Success!* 💰\n"
                         f"Transaction ID: *{transaction_id}*\n"
                         f"Amount Paid: KES {amount:.2f}\n"
                         f"Your receipt is being generated. Thank you! Your slot is secure.\n\n"
                         "--- Main Menu ---\n"
                         f"{get_main_menu_message()}")
                save_session(phone_number, 'menu', {})
                
                # 3. DECOUPLE BLOCKING TASK: Generate PDF *after* sending the response.
                pdf_file = generate_pdf_receipt(temp_data['booking_id'])
                print(f"INFO: PDF receipt generated/logged: {pdf_file}")
                
            else:
                msg.body("Payment failed due to a processing error. Returning to menu.")
                save_session(phone_number, 'menu', {})
        except ValueError:
            msg.body("Invalid amount. Enter a numeric value greater than zero. _Reply 'menu' to return to the main menu._")
        except Exception as e:
            print(f"General error in pay_amount: {e}")
            msg.body("An unexpected error occurred. Returning to menu.")
            save_session(phone_number, 'menu', {})

    # -------------------- Feedback Flow (No major change needed here) -------------------- #
    elif state == 'feedback_booking':
        if not user_input.isdigit():
            msg.body("Booking ID must be numeric. Enter Booking ID. _Reply 'menu' to return to the main menu:_")
            return str(resp)
            
        booking_id = int(user_input)
        
        try:
            cursor.execute("SELECT id FROM bookings WHERE id=%s", (booking_id,))
            if not cursor.fetchone():
                msg.body("Booking ID not found. Enter valid Booking ID. _Reply 'menu' to return to the main menu:_")
                return str(resp)
            
            temp_data['booking_id'] = booking_id
            save_session(phone_number, 'feedback_message', temp_data)
            msg.body(f"Booking *{booking_id}* confirmed. Now, please share your detailed feedback message. We appreciate your honesty! _Reply 'menu' to return to the main menu:_")
        except mysql.connector.Error as e:
            print(f"DB Error on feedback lookup: {e}")
            msg.body("A database error occurred. Returning to menu.")
            save_session(phone_number, 'menu', {})

    elif state == 'feedback_message':
        if not incoming_msg.strip():
            msg.body("Please enter your feedback message. _Reply 'menu' to return to the main menu._")
            return str(resp)
            
        temp_data['message'] = incoming_msg
        save_session(phone_number, 'feedback_rating', temp_data)
        msg.body("Fantastic. Now, rate your overall experience from **1 (Poor)** to **5 (Excellent)**.")

    elif state == 'feedback_rating':
        if not user_input.isdigit() or int(user_input) not in range(1, 6):
            msg.body("Please enter a valid rating (1 to 5). _Reply 'menu' to return to the main menu._")
            return str(resp)
            
        rating = int(user_input)
        
        try:
            cursor.execute(
                "INSERT INTO feedback(booking_id, message, rating) VALUES (%s,%s,%s)",
                (temp_data['booking_id'], temp_data['message'], rating)
            )
            db.commit()
            msg.body(f"⭐ *Thank you for your valuable feedback!* We recorded your rating of {rating}/5. Your input helps us shine. 🙏\n\n{get_main_menu_message()}")
            save_session(phone_number, 'menu', {})
        except mysql.connector.Error as e:
            print(f"DB Error on feedback insert: {e}")
            msg.body("Could not save feedback due to a database error. Returning to main menu.")
            save_session(phone_number, 'menu', {})

    else:
        # Fallback to main menu for an unknown state
        msg.body("⚠️ I'm lost! Returning to the main menu.")
        save_session(phone_number, 'menu', {})

    return str(resp)

# -------------------- Run Flask -------------------- #
if __name__ == "__main__":
    print(f"Starting Flask App. DB: {DB_DATABASE}@{DB_HOST}")
    # Run the app, listening on all public IPs (0.0.0.0) so Ngrok can access it
    app.run(host='0.0.0.0', port=5000, debug=True)
