Glow Haven Beauty Lounge — WhatsApp Chatbot

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

3. How to Test & Interact

To begin a test, simply send any greeting (e.g., "Hi," "Hello," "Menu") to the test number below.

Step

User Input

Expected Bot Response

Notes

1. Start

Hi

Responds with the main menu (1, 2, 3, 4).

Full name of client is stored in the database upon first interaction.

2. Initiate Booking

2 (Book Appointment)

Prompts the user to select a service category (e.g., 1. Hair Care).



3. Select Service

1 (Hair Care)

Displays the list of services and prices (from MySQL).



4. Choose Item

2 (e.g., Silk Press)

Prompts for preferred date and time.



5. Provide Date

2025-11-05 14:00

Asks the user to confirm the booking or proceed to payment.



6. Pay Deposit

3 (Pay Deposit)

Simulates the M-Pesa Pochi transaction and confirms.

This is where the PDF receipt is generated and sent.

7. New Session

Hi (After paying)

Resets the session and returns to the main menu.

All previous data is saved to the bookings table.

WhatsApp Test Number: +14155238886

4. Assumptions & Future Improvements

Assumptions Made

Payment Simulation: For project scope, the M-Pesa Pochi la Biashara transaction is simulated. The bot simply records a deposit value and proceeds without validating a real transaction.

Name Inference: The user's name is inferred once upon first contact and stored in the database.

Time Slot Availability: The current system assumes time slots are available unless explicitly booked. There is no real-time availability check against a calendar.

Recommended Future Improvements

Real M-Pesa Integration: Replace the simulated step with integration to the M-Pesa Daraja API for real-time payment validation and deposit collection.

Calendar Integration: Implement Google Calendar/Outlook API sync to check and update time slot availability in real-time, preventing double-bookings.

Admin Dashboard: Develop a small web-based admin interface (e.g., using Dash or Django) for staff to view, manage, and analyze bookings and feedback stored in the MySQL database.

Natural Language Processing (NLP): Integrate a tool like Dialogflow to allow users to book by typing phrases (e.g., "I want a haircut at 3 PM tomorrow") instead of only relying on menu numbers.
