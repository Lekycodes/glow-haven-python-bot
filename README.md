💅 Glow Haven Beauty Lounge — WhatsApp Chatbot

1. Project Overview & Objective

This project delivers a stateful, transactional WhatsApp chatbot for Glow Haven Beauty Lounge, a contemporary unisex salon and spa based in Nairobi. The primary objective is to automate the client journey from discovery to booking, ensuring a professional and streamlined user experience.

The bot currently handles the following core functionalities:

Service & Price Inquiry: Clients can browse the full menu of services and their associated pricing.

Appointment Booking: Users can initiate and finalize an appointment, capturing their name, service selection, and preferred date/time.

Deposit Payment: Facilitates deposit collection via a simulated M-Pesa Pochi la Biashara transaction.

Booking Confirmation: Automatically generates and delivers a PDF receipt detailing the booking summary.

Feedback Collection: Captures unstructured client feedback for review.

2. Architecture and Approach

The chatbot is built on a robust, multi-layered architecture focused on persistence and reliability.

Key Technology Stack

Component

Technology

Purpose

Backend Logic

Python (Flask)

Lightweight framework for handling incoming webhooks, managing state transitions, and orchestrating responses.

Messaging

Twilio WhatsApp API

Handles secure delivery and receipt of messages.

State & Data

MySQL

Centralized, persistent database for storing service menus, client sessions (state), appointment records, and feedback.

Receipt Generation

FPDF

Used to programmatically generate professional PDF receipts for instant booking confirmation.

Deployment

ngrok

Exposes the local Flask server to the public internet via a secure, stable HTTPS tunnel for Twilio's webhook.

Stateful Flow Management

The bot employs a state-machine approach where every user interaction is tied to a stored session in the MySQL database. This ensures:

Context Preservation: The bot remembers where the user is in the booking process (e.g., waiting for Name, waiting for Service ID, waiting for Date).

Robust Error Handling: Users can be guided back to a specific step without losing their prior input.

3. Flow Diagram

User (WhatsApp)
      ↓
Twilio WhatsApp API
      ↓
Flask App (app.py)
      ↓
MySQL Database <—> FPDF Receipt Generator


4. How to Test & Interact

To begin a test, simply send any greeting (e.g., "Hi," "Hello," "Menu") to the test number.

WhatsApp Test Number: +14155238886

Input

Bot Menu Response

Action / Notes

hi

Main Menu (1-4)

Confirms the bot is running and resets the user session.

2

Service Category Selection (e.g., Hair Care)

Initiates the multi-step booking process.

1

Service List (e.g., Wash & Blow Dry)

Displays services pulled directly from the services table.

2025-11-05 14:00

Asks to confirm booking or pay deposit.

The bot validates and stores the booking details.

3

"Thank you for paying..."

Simulates deposit payment, records the booking, and sends the PDF receipt.

5. Local Setup and Deployment

To run this application, you must have Python 3.8+, pip, MySQL, and Ngrok installed.

Step 1: Clone and Install Dependencies

# Clone the repository
git clone [https://github.com/Lekycodes/glow-haven-python-bot](https://github.com/Lekycodes/glow-haven-python-bot)
cd glow-haven-python-bot

# Create and activate a virtual environment (optional, but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use 'venv\Scripts\activate'

# Install Python dependencies
pip install -r requirements.txt


Step 2: Database Setup

Start your MySQL server.

Run the schema.sql file to create the database (glow_haven), the required tables (users, services, bookings, feedback, sessions), and populate the service menu.

mysql -u [your_user] -p < schema.sql


Step 3: Environment Variables

Create a file named .env in the root directory and populate it with your credentials:

# Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=whatsapp:+14155238886

# MySQL Database Connection Details
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_NAME=glow_haven


Step 4: Run the Flask Application

Run the application on port 5000:

python app.py


Step 5: Expose the Webhook with Ngrok

In a separate terminal, start Ngrok to tunnel port 5000 to a public HTTPS URL:

ngrok http 5000


Copy the resulting HTTPS URL (e.g., https://*****.ngrok-free.app). You must then paste this URL, followed by /whatsapp, into the Twilio WhatsApp Sandbox Webhook setting (e.g., https://*****.ngrok-free.app/whatsapp).

6. Assumptions & Future Improvements

Assumptions Made

Payment Simulation: For project scope, the M-Pesa Pochi la Biashara transaction is simulated. The bot simply records a deposit value and proceeds without validating a real transaction.

Name Inference: The user's name is inferred once upon first contact and stored in the database.

Time Slot Availability: The current system assumes time slots are available unless explicitly booked. There is no real-time availability check against a calendar.

Recommended Future Improvements

Real M-Pesa Integration: Replace the simulated step with integration to the M-Pesa Daraja API for real-time payment validation and deposit collection.

Calendar Integration: Implement Google Calendar/Outlook API sync to check and update time slot availability in real-time, preventing double-bookings.

Admin Dashboard: Develop a small web-based admin interface (e.g., using Dash or Django) for staff to view, manage, and analyze bookings and feedback stored in the MySQL database.

Natural Language Processing (NLP): Integrate a tool like Dialogflow to allow users to book by typing phrases (e.g., "I want a haircut at 3 PM tomorrow") instead of only relying on menu numbers.
