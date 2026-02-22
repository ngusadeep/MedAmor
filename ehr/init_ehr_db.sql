-- Initialize EHR database and user
-- This runs only on first database initialization

CREATE USER ehr WITH PASSWORD 'ehr';
CREATE DATABASE ehr OWNER ehr;
GRANT ALL PRIVILEGES ON DATABASE ehr TO ehr;