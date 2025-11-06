# -------------------- Safe Imports -------------------- #
import sys
import os
import json
import random
from decimal import Decimal 
import mysql.connector
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from flask import Flask, request
from datetime import datetime, timedelta
from calendar import day_name

# -------------------- Configuration & DB Setup -------------------- #
load_dotenv()


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "").replace('whatsapp:', '') 

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DATABASE = os.getenv("DB_DATABASE", "glow_haven_bot") 

SALON_START_HOUR = 9
SALON_END_HOUR = 19 
EXCLUDED_WEEKDAY = 6 

# BRANDING_IMAGE_URL = "https://images.unsplash.com/photo-1542662562-b9e7634f195d?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    print("FATAL ERROR: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set in .env file.")
    sys.exit(1)

# Initialize Flask
app = Flask(__name__)

# --- DB Connection Management ---
def create_db_connection():
    """Creates a new, fresh database connection and cursor."""
    try:
        
        db = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE, autocommit=False
        )
        # dictionary=True ensures we can access columns by name (e.g., s['name'])
        cursor = db.cursor(dictionary=True, buffered=True) 
        return db, cursor
    except mysql.connector.Error as err:
        print(f"FATAL DATABASE ERROR: Cannot connect to MySQL: {err}")
        # Re-raise error to be caught in the main handler
        raise ConnectionRefusedError(f"Database connection failed: {err}")

# --- Session Functions ---
def get_session(phone_number, cursor):
    """Retrieves session data for a given phone number."""
    try:
        cursor.execute("SELECT * FROM sessions WHERE phone_number=%s", (phone_number,))
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"SESSION DB ERROR (get_session): {err}")
        return None

def save_session(phone_number, state, temp_data, db, cursor):
    """Saves or updates session state and temporary data."""
    try:
        temp_json = json.dumps(temp_data)
        cursor.execute("""
            INSERT INTO sessions(phone_number, current_state, temp_data)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE current_state=%s, temp_data=%s
        """, (phone_number, state, temp_json, state, temp_json))
        db.commit()
    except mysql.connector.Error as err:
        print(f"SESSION DB ERROR (save_session): {err}")
        db.rollback()

# -------------------- Utility Functions for Glow Haven Booking -------------------- #

def get_main_menu_text():
    """Returns the standardized main menu options for Glow Haven (Service Booking)."""
    
    return (
        "✨ *Welcome to Glow Haven Beauty Lounge!* We're here to make you shine. How can I assist you?\n\n"
        "1️⃣ *Chat:* Get Info (Services, Location, Hours)\n"
        "2️⃣ *Book:* Schedule Your Appointment\n"
        "3️⃣ *Pay:* Settle Your Deposit/Payment\n"
        "4️⃣ *My Bookings:* View Your Appointments\n"
        "5️⃣ *Review:* Share Your Feedback\n\n"
        "💡 *Tip:* You can always reply 'menu' to return here."
    )

def get_services_list(cursor):
    """Fetches and formats a list of services. Includes detailed error checking."""
    try:
        
        final_query = "SELECT id, name, price, duration FROM services ORDER BY id ASC"
        cursor.execute(final_query)
        services = cursor.fetchall()
        
        # Print number of rows fetched
        print(f"DIAGNOSTIC: Successfully fetched {len(services)} services from the database.")

        if not services:
            return "No services were returned by the database query. Please ensure your 'services' table has data (and correct column names).", [], []

        service_lines = []
        for s in services:
            # Robust handling for price
            try:
                price_data = s['price']
                
                # Check if it's a Decimal object (from MySQL DECIMAL type) and convert
                if isinstance(price_data, Decimal):
                    price_value = float(price_data.to_eng_string())
                else:
                    # Otherwise, try to convert it directly (it might be a standard float or int)
                    price_value = float(price_data)
                    
                price_text = f"KES {price_value:,.2f}" #comma formatting
            except Exception as format_e:
                print(f"SERVICE FORMATTING ERROR: Could not convert 'price' for service ID {s.get('id', 'Unknown')}. Error: {format_e}. Data received: {s}")
                price_text = "Price Error"
                
            # Use bold for service ID for clarity
            service_lines.append(f"*{s['id']}*. {s['name']} (Est. {s['duration']}) | {price_text}")
            
        # Return the list of formatted strings, not the single giant string
        return "Services successfully fetched.", services, service_lines
        
    except mysql.connector.Error as e:
        # Catch SQL execution errors (e.g., table missing, wrong column name in query)
        error_message = f"DATABASE ERROR fetching services. Check columns (id, name, price, duration) and table name. MySQL Error: {e}"
        print(f"FATAL DB ERROR in get_services_list: {error_message}")
        return f"A critical database error occurred while listing services. Error: {e.msg} (Check table/columns).", [], []

def get_available_dates():
    """Calculates the next 7 available business days (excluding Sunday)."""
    available_dates = []
    current_date = datetime.now()
    count = 0
    
    # Start checking from tomorrow (or today if it's past operating hours)
    start_time_check = current_date + timedelta(minutes=1)
    
    while count < 7:
        # Check if the current time is past today's operating hours
        if len(available_dates) == 0 and start_time_check.hour >= SALON_END_HOUR:
            # If it is past 7 PM, start checking from the next day
            current_date += timedelta(days=1)
            
        # Skip Sundays (day_name is 6)
        if current_date.weekday() == EXCLUDED_WEEKDAY:
            current_date += timedelta(days=1)
            continue
            
        # Add the date to the list
        available_dates.append({
            'date_object': current_date,
            'label': f"{day_name[current_date.weekday()]}, {current_date.strftime('%b %d')}"
        })
        current_date += timedelta(days=1)
        count += 1
        
    return available_dates

def get_available_slots(cursor, selected_date, service_id):
    """
    Generates available time slots for a given date, checking for existing bookings.
    Assumes a fixed 1-hour slot granularity for simplicity.
    """
    slots = []
    
    # Check if the date is today
    is_today = selected_date.date() == datetime.now().date()
    
    # Calculate the effective start hour (next hour if today, otherwise SALON_START_HOUR)
    start_hour = SALON_START_HOUR
    if is_today:
        now_hour = datetime.now().hour
        # Start from the next full hour, ensuring we don't start past closing
        start_hour = max(SALON_START_HOUR, now_hour + 1)
        
    # Get the service duration (assuming in minutes, for future use)
    cursor.execute("SELECT duration FROM services WHERE id=%s", (service_id,))
    duration_str = cursor.fetchone()['duration'] if cursor.fetchone() else '60 mins'
    
    # Extract minutes from duration (e.g., '1 hr 15 mins' -> 75 minutes) - simplified to 60 min slots for now
    slot_duration_minutes = 60 

    # Generate potential slots
    current_time = selected_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    
    while current_time.hour < SALON_END_HOUR:
        slot_end_time = current_time + timedelta(minutes=slot_duration_minutes)
        
        # Check if the slot ends before or at closing time
        if slot_end_time.hour <= SALON_END_HOUR:
            # 1. Check for existing bookings within this time slot
           
            cursor.execute("""
                SELECT COUNT(*) as occupied FROM bookings
                WHERE booking_time = %s
            """, (current_time.strftime('%Y-%m-%d %H:%M:%S'),))
            
            if cursor.fetchone()['occupied'] == 0:
                # Slot is available
                slots.append({
                    'time_object': current_time,
                    'label': current_time.strftime('%I:%M %p').lstrip('0')
                })
        
        current_time += timedelta(minutes=slot_duration_minutes)

    return slots


def send_long_message(resp, message_parts):
    """Adds multiple messages to the Twilio response to handle character limits."""
    # Send the first part
    resp.message(message_parts[0])
    
    # Send all subsequent parts
    for part in message_parts[1:]:
        resp.message(part)

# -------------------- Flask App Webhook -------------------- #

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    """Handles incoming WhatsApp messages from Twilio."""
    
    incoming_msg = request.values.get('Body', '').strip()
    phone_number = request.values.get('From', '').replace('whatsapp:', '')

    resp = MessagingResponse()
    
    db = None
    cursor = None

    try:
        # Establish DB connection
        db, cursor = create_db_connection()
    except ConnectionRefusedError:
       
        resp.message("🛠️ Our service is temporarily unavailable. Please try again in a few minutes.")
        return str(resp)
    except Exception as e:
        print(f"UNEXPECTED ERROR ON STARTUP: {e}")
        resp.message("⚠️ An internal error occurred. Our team is looking into it.")
        return str(resp)

    # -------------------- Main Logic Block -------------------- #
    try:
        session = get_session(phone_number, cursor)
        user_input = incoming_msg.strip().lower()

        # Universal Session Reset ---
        if user_input in ['hi', 'hello', 'start', 'menu', 'main menu', '0']:
            save_session(phone_number, 'menu', {}, db, cursor)
            resp.message(get_main_menu_text())
            return str(resp)

        # Handle initial message if no session exists
        if not session:
            save_session(phone_number, 'menu', {}, db, cursor)
            resp.message(get_main_menu_text())
            return str(resp)


        # --- Session Management ---
        state = session.get('current_state', 'menu')
        
        try:
            temp_data_raw = session.get('temp_data')
            temp_data = json.loads(temp_data_raw) if temp_data_raw else {}
        except json.JSONDecodeError:
            print(f"ERROR: JSONDecodeError for phone {phone_number}. Session cleared.")
            temp_data = {}
            save_session(phone_number, 'menu', temp_data, db, cursor)
            resp.message("⚠️ We encountered an issue with your session data. Starting fresh. Please choose an option.")
            return str(resp)

        # -------------------- Main Menu Logic -------------------- #
        if state == 'menu':
            if user_input in ['1', 'chat', 'info']:
            
                resp.message(
                    "💬 *General Info Menu:*\n\n"
                    "1️⃣ *Services:* See our full treatment list 💅\n"
                    "2️⃣ *Location:* Find us & check hours 📍\n"
                    "3️⃣ *Back:* Return to main menu"
                )
                save_session(phone_number, 'chat_info_menu', {}, db, cursor)
                
            elif user_input in ['2', 'book', 'schedule']:
                # Option 2: Start Booking
                message_status, services, service_lines = get_services_list(cursor)
                
                if not services:
                     resp.message(f"⚠️ {message_status}\n\nReturning to main menu.")
                     save_session(phone_number, 'menu', {}, db, cursor)
                     return str(resp)
                
                # Handle long list by splitting into messages
                message_parts = []
                # 
                current_chunk = "🗓️ *Ready to Book? Choose your service:* \n" 
                
                for line in service_lines:
                    if len(current_chunk) + len(line) + 1 > 1000:
                        message_parts.append(current_chunk.strip())
                        current_chunk = ""
                    current_chunk += "\n" + line
                
                if current_chunk:
                    message_parts.append(current_chunk.strip())
                
               
                final_instruction = "\n\n✨ To proceed, please reply with the **Service ID** you wish to book."
                message_parts[-1] += final_instruction
                
                send_long_message(resp, message_parts)
                save_session(phone_number, 'service_selection', {}, db, cursor)

            elif user_input in ['3', 'pay', 'payments', 'deposit']:
                
                resp.message("💳 To process a payment, please reply with your **Booking ID**.")
                save_session(phone_number, 'payment_input', {}, db, cursor)
                
            elif user_input in ['4', 'my bookings', 'bookings']:
                # Option 4: My Bookings
                cursor.execute("""
                    SELECT b.id, s.name, b.booking_time
                    FROM bookings b
                    JOIN services s ON b.service_id = s.id
                    WHERE b.phone_number=%s
                    ORDER BY b.booking_time DESC
                """, (phone_number,))
                bookings = cursor.fetchall()
                
                if bookings:
                    booking_list = "\n".join([f"**ID {b['id']}**: {b['name']} on {b['booking_time'].strftime('%Y-%m-%d at %H:%M')}" for b in bookings])
                    
                    resp.message(f"📅 *Your Upcoming & Past Bookings:*\n\n{booking_list}\n\nType 'menu' to go back to the main menu.")
                else:
                    resp.message("🥺 You have no current or past bookings recorded. Reply **2** to book your first service!")

                save_session(phone_number, 'menu', {}, db, cursor)
                resp.message(f"\n\n{get_main_menu_text()}")

            elif user_input in ['5', 'review', 'feedback']:
                
                resp.message("🌟 We value your opinion! Please enter the **Booking ID** for the service you'd like to review.")
                save_session(phone_number, 'review_booking_id_input', {}, db, cursor)
            else:
                resp.message("❌ That wasn't a valid menu option. Please choose 1, 2, 3, 4, or 5.") 


        # -------------------- Chat/Info Flow (Sub-Menu for Option 1) -------------------- #
        elif state == 'chat_info_menu':
            if user_input == '1':
                message_status, services, service_lines = get_services_list(cursor)
                
                if not services:
                    resp.message(f"⚠️ {message_status}\n\nReply with **3** to go back or 'menu' to return to the main menu.")
                    
                else:
                    message_parts = []
                    
                    current_chunk = "💆‍♀️ *Glow Haven Services Menu:*\n"
                    
                    for line in service_lines:
                        if len(current_chunk) + len(line) + 1 > 1000:
                            message_parts.append(current_chunk.strip())
                            current_chunk = ""
                        current_chunk += "\n" + line
                    
                    if current_chunk:
                        message_parts.append(current_chunk.strip())

                    final_instruction = "\n\nReply with **3** to go back to the Info Menu or 'menu' for the main menu."
                    message_parts[-1] += final_instruction
                    
                    send_long_message(resp, message_parts)

            elif user_input == '2':
                resp.message(
                    "📍 *Find Your Haven:*\n\n"
                    "**Location:** 1st Floor, Valley Arcade Mall, Nairobi\n"
                    "**Hours:** Mon-Sat, 9:00 AM - 7:00 PM | Sunday: Closed\n"
                    "**Contact:** Call us at +254 712 345 678 or email info@glowhavenbeauty.co.ke\n\n"
                    "**Instagram:** @glowhavenbeautylounge.\n\n"
                    "Reply with **3** to go back or 'menu' to return to the main menu."
                )
            elif user_input == '3':
                save_session(phone_number, 'menu', {}, db, cursor)
                resp.message(get_main_menu_text())
            else:
                resp.message("❌ Invalid option. Please choose 1 (Services), 2 (Location), or 3 (Back).")


        # -------------------- Booking Flow: Step 1 (Service Selection) -------------------- #
        elif state == 'service_selection':
            if user_input.isdigit():
                service_id = int(user_input)
                cursor.execute("SELECT id, name, price, duration FROM services WHERE id=%s", (service_id,))
                service = cursor.fetchone()

                if service:
                    temp_data['service_id'] = service_id
                    temp_data['service_name'] = service['name']
                    
                    save_session(phone_number, 'booking_name_input', temp_data, db, cursor)
                    resp.message(f"📝 Excellent! You chose **{service['name']}**. Please reply with your *full name* (First and Last) for the booking.")
                else:
                    resp.message("❌ Service ID *not* found. Please enter a valid ID from the list above.")
            else:
                 resp.message("❌ Invalid input. Please reply only with the *Service ID number*.")

        # -------------------- Booking Flow: Step 2 (Name Input) -------------------- #
        elif state == 'booking_name_input':
            user_name = incoming_msg.strip()
            if not user_name:
                resp.message("❌ Please enter your full name to proceed with the booking.")
                return str(resp)

            temp_data['user_name'] = user_name
            
            # --- NEW STEP 3: DATE SELECTION ---
            dates = get_available_dates()
            temp_data['available_dates'] = [d['date_object'].strftime('%Y-%m-%d') for d in dates] # Store dates as strings
            
            date_list = "📅 *Next Available Dates:*\n\n"
            for i, d in enumerate(dates):
                date_list += f"*{i + 1}*. {d['label']}\n"
            
            date_list += "\n➡️ Please reply with the **number** of the date you prefer."
            
            save_session(phone_number, 'booking_date_selection', temp_data, db, cursor)
            resp.message(f"Hello, *{user_name}*! Next, let's pick your date.\n\n{date_list}")


        # -------------------- Booking Flow: Step 3 (Date Selection) -------------------- #
        elif state == 'booking_date_selection':
            if user_input.isdigit():
                choice = int(user_input)
                
                available_dates_str = temp_data.get('available_dates', [])
                
                if 1 <= choice <= len(available_dates_str):
                    selected_date_str = available_dates_str[choice - 1]
                    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d')
                    
                    service_id = temp_data['service_id']
                    
                    # Get available time slots for the chosen date and service
                    slots = get_available_slots(cursor, selected_date, service_id)
                    
                    if not slots:
                        
                        resp.message(
                            f"😔 No available slots found for *{day_name[selected_date.weekday()]}, {selected_date.strftime('%b %d')}*.\n"
                            f"Please try selecting a different date from the menu by typing **'menu'**."
                        )
                        save_session(phone_number, 'menu', {}, db, cursor)
                        return str(resp)
                    
                    temp_data['selected_date'] = selected_date_str
                    # Store slots in a dictionary for easy mapping (A -> time_object)
                    slot_map = {}
                    slot_list_msg = f"⏱️ *Available Slots for {day_name[selected_date.weekday()]}, {selected_date.strftime('%b %d')}:*\n\n"
                    
                    # Use ASCII letters (A, B, C...) for time slot choices
                    for i, slot in enumerate(slots):
                        slot_key = chr(ord('A') + i)
                        slot_map[slot_key] = slot['time_object'].strftime('%Y-%m-%d %H:%M')
                        slot_list_msg += f"*{slot_key}*. {slot['label']}\n"
                        
                    temp_data['available_slots_map'] = slot_map
                    
                    slot_list_msg += "\n➡️ Please reply with the **letter** of the time slot you want."
                    
                    save_session(phone_number, 'booking_slot_selection', temp_data, db, cursor)
                    resp.message(slot_list_msg)

                else:
                    resp.message("❌ Invalid date choice. Please reply with a number corresponding to one of the listed dates.")
            else:
                resp.message("❌ Invalid input. Please reply with the **number** of your preferred date.")


        # -------------------- Booking Flow: Step 4 (Slot Selection & Confirmation) -------------------- #
        elif state == 'booking_slot_selection':
            user_choice_key = user_input.upper()
            slot_map = temp_data.get('available_slots_map', {})
            
            if user_choice_key in slot_map:
                booking_time_str = slot_map[user_choice_key]
                
                # --- Final Booking Insert ---
                service_id = temp_data['service_id']
                user_name = temp_data['user_name']
                
                try:
                    cursor.execute(
                        "INSERT INTO bookings (user_name, phone_number, service_id, booking_time) VALUES (%s, %s, %s, %s)",
                        (user_name, phone_number, service_id, booking_time_str)
                    )
                    db.commit()
                    resp.message(
                        f"🎉 *Booking Confirmed!* 🎉\n"
                        f"**Service:** {temp_data['service_name']}\n"
                        f"**Time:** {datetime.strptime(booking_time_str, '%Y-%m-%d %H:%M').strftime('%A, %B %d at %I:%M %p')}\n"
                        f"**Client:** {user_name}\n\n"
                        "We can't wait to pamper you! You can now send a payment (Option 3) or type 'menu'."
                    )
                except mysql.connector.Error as e:
                    print(f"DB Error on booking insert: {e}")
                    resp.message("⚠️ A database error prevented the booking. Please try again.")
                except Exception as e:
                    print(f"General Error: {e}")
                    resp.message("⚠️ An unexpected error occurred during finalization. Please try again.")
                finally:
                    save_session(phone_number, 'menu', {}, db, cursor)
                    resp.message(f"\n\nReturning to main menu.\n\n{get_main_menu_text()}")
            else:
                resp.message("❌ Invalid choice. Please reply with the **letter** corresponding to one of the listed time slots.")


        # -------------------- Payments Flow: Step 1 (Booking ID Input) -------------------- #
        elif state == 'payment_input':
            if user_input.isdigit():
                booking_id = int(user_input)
                cursor.execute("""
                    SELECT b.id, s.name, b.deposit_paid
                    FROM bookings b
                    JOIN services s ON b.service_id = s.id
                    WHERE b.id = %s AND b.phone_number = %s
                """, (booking_id, phone_number))
                booking = cursor.fetchone()

                if booking:
                    temp_data['booking_id'] = booking_id
                    temp_data['service_name'] = booking['name']

                    resp.message(f"💵 Booking Found: **{booking['name']}**. Current deposit paid: KES {booking['deposit_paid']:.2f}.\n\n"
                             f"Please enter the *amount* you wish to pay now (e.g., 1500).")
                    save_session(phone_number, 'payment_amount_input', temp_data, db, cursor)
                else:
                    resp.message("❌ Booking ID not found for your number. Please double-check your ID or type 'menu'.")
            else:
                resp.message("❌ Invalid input. Please reply with the *numeric Booking ID*.")

        # -------------------- Payments Flow: Step 2 (Amount Input & DB Update) -------------------- #
        elif state == 'payment_amount_input':
            try:
                amount = float(user_input)
                if amount <= 0:
                     resp.message("❌ Payment amount must be greater than zero. Please try again.")
                     return str(resp)

                booking_id = temp_data.get('booking_id')
                service_name = temp_data.get('service_name', 'Service')
                
                # --- Transaction Logic ---
                # 1. Update deposit in bookings table
                cursor.execute("""
                    UPDATE bookings SET deposit_paid = deposit_paid + %s WHERE id = %s
                """, (amount, booking_id))
                
                # 2. Insert transaction into payments table
                transaction_id = f"GH-TXN-{random.randint(100000, 999999)}"
                cursor.execute("""
                    INSERT INTO payments (booking_id, amount, payment_date, transaction_id) 
                    VALUES (%s, %s, NOW(), %s)
                """, (booking_id, amount, transaction_id))
                
                db.commit()

                # Fetch the total deposit paid after the update (for enhanced UX)
                cursor.execute("SELECT deposit_paid FROM bookings WHERE id = %s", (booking_id,))
                updated_booking = cursor.fetchone()
                total_paid = updated_booking['deposit_paid'] if updated_booking else 0.00
                
                # payment receipt
                resp.message(
                    f"✅ Payment Successfully Recorded!\n"
                    f"**Service:** {service_name}\n"
                    f"**Amount Paid NOW:** KES {amount:,.2f}\n"
                    f"**TOTAL Deposit Paid:** KES {total_paid:,.2f} 💰\n" 
                    f"**Transaction ID:** {transaction_id}\n\n"
                    "Thank you for your payment! Type 'menu' to continue."
                )
            except ValueError:
                resp.message("❌ Invalid amount. Please enter a number (e.g., 1500) without currency signs.")
            except mysql.connector.Error as e:
                print(f"DB Error on payment insert: {e}")
                db.rollback() 
                resp.message("⚠️ A database error prevented the payment from being recorded. Please try again.")
            except Exception as e:
                print(f"General Error during payment: {e}")
                resp.message("⚠️ An unexpected error occurred. Please try again.")
            finally:
                save_session(phone_number, 'menu', {}, db, cursor)
                resp.message(f"\n\n{get_main_menu_text()}")


        # -------------------- Review Flow: Step 1 (Booking ID Input) -------------------- #
        elif state == 'review_booking_id_input':
            if user_input.isdigit():
                booking_id = int(user_input)
                cursor.execute("""
                    SELECT b.id, s.name
                    FROM bookings b
                    JOIN services s ON b.service_id = s.id
                    WHERE b.id = %s AND b.phone_number = %s
                """, (booking_id, phone_number))
                booking = cursor.fetchone()

                if booking:
                    temp_data['review_booking_id'] = booking_id
                    temp_data['review_service_name'] = booking['name']
                    
                    # reveiw prompt
                    resp.message(f"You are reviewing: **{booking['name']}**.\n\n"
                             f"Please enter your rating (a single number from **1** to **5**, where 5 is excellent).")
                    save_session(phone_number, 'review_rating_input', temp_data, db, cursor)
                else:
                    resp.message("❌ Booking ID not found or does not belong to your number. Please try again or type 'menu'.")
            else:
                resp.message("❌ Invalid input. Please reply with the *numeric Booking ID*.")

        # -------------------- Review Flow: Step 2 (Rating Input) -------------------- #
        elif state == 'review_rating_input':
            try:
                rating = int(user_input)
                if 1 <= rating <= 5:
                    temp_data['review_rating'] = rating
                    resp.message(f"Thank you for the {rating}/5 star rating! ⭐️ You can now provide any additional **comments or suggestions** below (optional).")
                    save_session(phone_number, 'review_comment_input', temp_data, db, cursor)
                else:
                    resp.message("❌ Invalid rating. Please enter a single number between 1 and 5.")
            except ValueError:
                resp.message("❌ Invalid input. Please enter a single number between 1 and 5.")

        # -------------------- Review Flow: Step 3 (Comment Input & DB Insert) -------------------- #
        elif state == 'review_comment_input':
            comments = incoming_msg.strip()
            booking_id = temp_data.get('review_booking_id')
            rating = temp_data.get('review_rating')
            service_name = temp_data.get('review_service_name', 'service')
            
            comment_to_save = comments if comments else None

            try:
                cursor.execute("""
                    INSERT INTO feedback (booking_id, rating, comments) 
                    VALUES (%s, %s, %s)
                """, (booking_id, rating, comment_to_save))
                db.commit()
                resp.message(
                    f"💖 Feedback Received for the {service_name}!\n"
                    f"Your rating ({rating}/5) helps us improve. Thank you for choosing Glow Haven!"
                )
            except mysql.connector.Error as e:
                print(f"DB Error on feedback insert: {e}")
                db.rollback() 
                resp.message("⚠️ A database error occurred. Your feedback could not be saved. Please try again.")
            except Exception as e:
                print(f"General Error during feedback: {e}")
                resp.message("⚠️ An unexpected error occurred. Please try again.")
            finally:
                save_session(phone_number, 'menu', {}, db, cursor)
                resp.message(f"\n\n{get_main_menu_text()}")


        # -------------------- Fallback -------------------- #
        else:
            # fallback
            resp.message("🤔 Oops! I didn't recognize that. Let's start fresh. Type 'menu' to see all options.")
            save_session(phone_number, 'menu', {}, db, cursor)

        return str(resp)

    # -------------------- Final Cleanup -------------------- #
    except Exception as e:
        print(f"CRITICAL UNHANDLED ERROR IN WHATSAPP HANDLER: {e}")
        resp.message("⚠️ A serious internal error occurred. Please wait a moment and try sending 'menu' again.")
        return str(resp)
    finally:
        # Close the connection
        if db and db.is_connected():
            db.close()

# -------------------- Run Flask -------------------- #
if __name__ == "__main__":
    print(f"Starting Glow Haven Bot. DB: {DB_DATABASE}@{DB_HOST}")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
