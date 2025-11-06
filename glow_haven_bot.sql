-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 05, 2025 at 09:18 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `glow_haven_bot`
--

-- --------------------------------------------------------

--
-- Table structure for table `bookings`
--

CREATE TABLE `bookings` (
  `id` int(11) NOT NULL,
  `user_name` varchar(100) NOT NULL,
  `phone_number` varchar(20) NOT NULL,
  `service_id` int(11) NOT NULL,
  `booking_time` datetime NOT NULL,
  `deposit_paid` decimal(10,2) DEFAULT 0.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `feedback`
--

CREATE TABLE `feedback` (
  `id` int(11) NOT NULL,
  `booking_id` int(11) NOT NULL,
  `message` text NOT NULL,
  `rating` int(11) DEFAULT NULL CHECK (`rating` between 1 and 5),
  `submitted_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `payments`
--

CREATE TABLE `payments` (
  `id` int(11) NOT NULL,
  `booking_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_date` datetime NOT NULL,
  `transaction_id` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `services`
--

CREATE TABLE `services` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(255) NOT NULL,
  `duration` varchar(50) NOT NULL,
  `price` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `services`
--

INSERT INTO `services` (`id`, `name`, `description`, `duration`, `price`) VALUES
(1, 'Wash & Blow Dry', 'Deep cleansing shampoo and style finish', '45 mins', 1000.00),
(2, 'Silk Press', 'Straightening for natural hair', '1 hr 15 mins', 2000.00),
(3, 'Braiding (Medium)', 'Classic medium-sized braids', '3 hrs', 3500.00),
(4, 'Wig Installation', 'Wig fitting and styling', '1 hr', 2500.00),
(5, 'Classic Manicure', 'Nail trimming, shaping, polish', '45 mins', 800.00),
(6, 'Gel Manicure', 'Gel polish with nail prep', '1 hr', 1200.00),
(7, 'Pedicure', 'Foot soak, scrub, massage', '1 hr 15 mins', 1500.00),
(8, 'Express Facial', 'Cleansing, exfoliation, hydration', '30 mins', 1200.00),
(9, 'Deep Cleansing Facial', 'Full facial with mask & extraction', '1 hr', 2000.00),
(10, 'Anti-Aging Facial', 'Collagen-boosting and rejuvenation', '1 hr 15 mins', 3000.00),
(11, 'Swedish Massage', 'Full body relaxation massage', '1 hr', 2800.00),
(12, 'Deep Tissue Massage', 'Relieves muscle tension', '1 hr 15 mins', 3200.00),
(13, 'Aromatherapy Massage', 'Essential oils and relaxation', '1 hr', 3000.00),
(14, 'Day Makeup', 'Light natural look', '45 mins', 1800.00),
(15, 'Glam Makeup', 'Full coverage, lashes included', '1 hr 15 mins', 2800.00),
(16, 'Lash Extension (Classic)', 'Single lash extensions', '1 hr 30 mins', 3500.00),
(17, 'Underarm Wax', 'Smooth finish for underarms', '20 mins', 700.00),
(18, 'Full Leg Wax', 'Complete leg waxing', '45 mins', 1800.00),
(19, 'Brazilian Wax', 'Intimate waxing service', '45 mins', 2000.00),
(20, 'Wash & Blow Dry', 'Deep cleansing shampoo and style finish', '45 mins', 1000.00),
(21, 'Silk Press', 'Straightening for natural hair', '1 hr 15 mins', 2000.00),
(22, 'Braiding (Medium)', 'Classic medium-sized braids', '3 hrs', 3500.00),
(23, 'Wig Installation', 'Wig fitting and styling', '1 hr', 2500.00),
(24, 'Classic Manicure', 'Nail trimming, shaping, polish', '45 mins', 800.00),
(25, 'Gel Manicure', 'Gel polish with nail prep', '1 hr', 1200.00),
(26, 'Pedicure', 'Foot soak, scrub, massage', '1 hr 15 mins', 1500.00),
(27, 'Express Facial', 'Cleansing, exfoliation, hydration', '30 mins', 1200.00),
(28, 'Deep Cleansing Facial', 'Full facial with mask & extraction', '1 hr', 2000.00),
(29, 'Anti-Aging Facial', 'Collagen-boosting and rejuvenation', '1 hr 15 mins', 3000.00),
(30, 'Swedish Massage', 'Full body relaxation massage', '1 hr', 2800.00),
(31, 'Deep Tissue Massage', 'Relieves muscle tension', '1 hr 15 mins', 3200.00),
(32, 'Aromatherapy Massage', 'Essential oils and relaxation', '1 hr', 3000.00),
(33, 'Day Makeup', 'Light natural look', '45 mins', 1800.00),
(34, 'Glam Makeup', 'Full coverage, lashes included', '1 hr 15 mins', 2800.00),
(35, 'Lash Extension (Classic)', 'Single lash extensions', '1 hr 30 mins', 3500.00),
(36, 'Underarm Wax', 'Smooth finish for underarms', '20 mins', 700.00),
(37, 'Full Leg Wax', 'Complete leg waxing', '45 mins', 1800.00),
(38, 'Brazilian Wax', 'Intimate waxing service', '45 mins', 2000.00);

-- --------------------------------------------------------

--
-- Table structure for table `sessions`
--

CREATE TABLE `sessions` (
  `phone_number` varchar(20) NOT NULL,
  `current_state` varchar(50) NOT NULL,
  `temp_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`temp_data`)),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `service_id` (`service_id`);

--
-- Indexes for table `feedback`
--
ALTER TABLE `feedback`
  ADD PRIMARY KEY (`id`),
  ADD KEY `booking_id` (`booking_id`);

--
-- Indexes for table `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `transaction_id` (`transaction_id`),
  ADD KEY `booking_id` (`booking_id`);

--
-- Indexes for table `services`
--
ALTER TABLE `services`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sessions`
--
ALTER TABLE `sessions`
  ADD PRIMARY KEY (`phone_number`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bookings`
--
ALTER TABLE `bookings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `feedback`
--
ALTER TABLE `feedback`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `payments`
--
ALTER TABLE `payments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `services`
--
ALTER TABLE `services`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `bookings`
--
ALTER TABLE `bookings`
  ADD CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`);

--
-- Constraints for table `feedback`
--
ALTER TABLE `feedback`
  ADD CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`);

--
-- Constraints for table `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
