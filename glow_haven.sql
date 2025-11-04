-- --------------------------------------------------------
-- Glow Haven Beauty Lounge Database Setup
--
-- This SQL script creates the necessary database and tables
-- (sessions, services, bookings, payments, feedback)
-- for the Python WhatsApp bot (app.py) to function.
-- --------------------------------------------------------

-- 1. DATABASE CREATION
-- Ensure you replace 'glow_haven' with your desired database name if needed,
-- but remember to update your .env file to match.
CREATE DATABASE IF NOT EXISTS glow_haven CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Select the new database for use
USE glow_haven;

-- 2. TABLE: sessions
-- Used by the bot to track the user's current conversation state.
-- CRITICAL for multi-step flows like booking or payment.
CREATE TABLE IF NOT EXISTS sessions (
    phone_number VARCHAR(20) PRIMARY KEY,
    current_state VARCHAR(50) NOT NULL,
    temp_data JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 3. TABLE: services
-- Stores the services offered by the salon (e.g., Manicure, Massage).
-- The bot fetches this data to populate the booking menu.
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. INITIAL DATA: Insert default services
INSERT INTO services (name, price) VALUES
('Luxury Manicure & Pedicure', 2500.00),
('Deep Tissue Massage (60 min)', 4000.00),
('Full Face Makeup Application', 3500.00),
('Hydrating Facial Treatment', 5000.00);


-- 5. TABLE: bookings
-- Stores all appointment bookings and links them to services and payments.
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    service_id INT NOT NULL,
    booking_time DATETIME NOT NULL,
    deposit_paid DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES services(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. TABLE: payments
-- Records every payment transaction (like a deposit).
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATETIME NOT NULL,
    transaction_id VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. TABLE: feedback
-- Captures customer ratings and comments.
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Setup Complete
-- --------------------------------------------------------
