CREATE DATABASE IF NOT EXISTS siri_bank;
USE siri_bank;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(20) UNIQUE NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    preferred_language VARCHAR(20) DEFAULT 'English',
    upi_id VARCHAR(50) UNIQUE,
    aadhaar_number VARCHAR(20) UNIQUE,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    balance DECIMAL(15, 2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    request_details TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert dummy data for testing
-- Create Admin
INSERT INTO users (customer_id, phone_number, password_hash, full_name, is_admin, upi_id) 
VALUES ('ADMIN001', '0000000000', 'admin123', 'System Administrator', 1, 'admin@siri');

INSERT INTO accounts (user_id, account_number, balance, status) 
VALUES (1, 'SYSTEM000', 999999999.00, 'ACTIVE');

-- Create 4 Users
INSERT INTO users (customer_id, phone_number, password_hash, full_name, preferred_language, upi_id, aadhaar_number) 
VALUES ('CUST1001', '9876543210', '123456', 'Arpitha', 'English', 'arpitha1@siri', '123456789001');

INSERT INTO accounts (user_id, account_number, balance, status) 
VALUES (2, 'ACC80000', 15500.50, 'ACTIVE');

INSERT INTO users (customer_id, phone_number, password_hash, full_name, preferred_language, upi_id, aadhaar_number) 
VALUES ('CUST1002', '9876543211', '123456', 'Chaithanya', 'English', 'chaithanya2@siri', '123456789002');

INSERT INTO accounts (user_id, account_number, balance, status) 
VALUES (3, 'ACC80001', 7017.28, 'ACTIVE');

INSERT INTO users (customer_id, phone_number, password_hash, full_name, preferred_language, upi_id, aadhaar_number) 
VALUES ('CUST1003', '9876543212', '123456', 'Harshitha', 'English', 'harshitha3@siri', '123456789003');

INSERT INTO accounts (user_id, account_number, balance, status) 
VALUES (4, 'ACC80002', 85000.00, 'ACTIVE');

INSERT INTO users (customer_id, phone_number, password_hash, full_name, preferred_language, upi_id, aadhaar_number) 
VALUES ('CUST1004', '9876543213', '123456', 'Jyothi', 'English', 'jyothi4@siri', '123456789004');

INSERT INTO accounts (user_id, account_number, balance, status) 
VALUES (5, 'ACC80003', 125000.00, 'ACTIVE');
