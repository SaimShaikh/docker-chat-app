-- Modified by Muhammad Abdulghaffar
-- Adds a password column (if missing). App will hash '123' at startup.

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS password VARCHAR(255) NULL;
