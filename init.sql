-- PostgreSQL initialization script for ModularChatBot
-- This script runs when the PostgreSQL container starts for the first time

-- Set timezone
SET timezone = 'UTC';

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create a test database for testing
CREATE DATABASE test_chatbot;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE chatbot TO postgres;
GRANT ALL PRIVILEGES ON DATABASE test_chatbot TO postgres;

-- Set proper encoding for both databases
ALTER DATABASE chatbot SET client_encoding TO 'UTF8';
ALTER DATABASE test_chatbot SET client_encoding TO 'UTF8';
