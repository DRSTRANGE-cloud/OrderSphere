-- ═══════════════════════════════════════════════════════════════════════════
--  OrderSphere Payment Integration Migration
--  Run this script to add Razorpay payment columns to existing databases
--  MySQL Syntax: mysql -u root -p ordersphere_db < migrate_payment_schema.sql
-- ═══════════════════════════════════════════════════════════════════════════

USE ordersphere_db;

-- Add payment columns to orders table if they don't exist
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'PENDING' AFTER notes,
ADD COLUMN IF NOT EXISTS payment_id VARCHAR(100) AFTER payment_status,
ADD COLUMN IF NOT EXISTS razorpay_order_id VARCHAR(100) AFTER payment_id;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_id ON orders(payment_id);

-- Verify migration
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'orders' AND COLUMN_NAME IN ('payment_status', 'payment_id', 'razorpay_order_id');

-- Output: You should see three rows with the payment columns if migration is successful
COMMIT;
