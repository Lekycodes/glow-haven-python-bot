Glow Haven Beauty Lounge — WhatsApp Chatbot

1.Overview

This is a WhatsApp chatbot built for Glow Haven Beauty Lounge, a unisex salon and spa based in Nairobi.
The chatbot helps clients:

Ask about services, prices, and promotions

Book appointments

Pay deposits (via simulated Pochi la Biashara)

Receive a PDF receipt with booking details

Provide feedback


2.Architecture & Approach

Stack:

Python (Flask) for backend logic

Twilio WhatsApp API for message handling

MySQL for storing services, bookings, feedback, and sessions

FPDF for generating booking receipts

ngrok for local webhook exposure

dotenv for managing credentials securely

3.Flow Diagram:

User (WhatsApp)
    ↓
Twilio WhatsApp API
    ↓
Flask App (app.py)
    ↓
MySQL Database  ←→  FPDF Receipt Generator


4.How to Interact with the Bot

test number +14155238886 

Type "hi" or any greeting.

The bot will respond with:


5.Hi! Welcome to Glow Haven Beauty Lounge. How can I assist you today?

1. Services 💇‍♀️
2. Book Appointment 📅
3. Pay Deposit 💰
4. Feedback 📝

   You: hi  
Bot: Hi! Welcome to Glow Haven Beauty Lounge...  

You: 2  
Bot: Please choose a service category:  
1. Hair Care  
2. Nail Care  
...

You: 1  
Bot: Select a service:  
1. Wash & Blow Dry - KES 1000  
2. Silk Press - KES 2000  
...

You: 2  
Bot: Great! Please enter your preferred date and time (e.g., 2025-11-01 10:00 AM)


6.Assumptions & Improvements

Assumptions:

Payment integration (Pochi la Biashara mock).

Timeslots avaialability unless explicitly booked.

Customer name inferred from WhatsApp contact.

Improvements (Future):

Integrate real M-Pesa Daraja API for payments.

Enable Google Calendar sync for appointments.

Implement admin dashboard for bookings and analytics.

WhatsApp Test Number

Include this in your submission (e.g.):

Test Number: +14155238886
