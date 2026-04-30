-- ============================================================
--  OrderSphere  ·  Production DB Schema
--  MySQL 8.0  |  app.py expects root password: 123456
--  Run:  mysql -u root < setup_db.sql
-- ============================================================

DROP DATABASE IF EXISTS ordersphere_db;
CREATE DATABASE ordersphere_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ordersphere_db;

-- ── 1. ROLES ──────────────────────────────────────────────
CREATE TABLE roles (
  role_id   TINYINT     PRIMARY KEY,
  role_name VARCHAR(30) NOT NULL UNIQUE
);
INSERT INTO roles VALUES (1,'admin'),(2,'customer'),(3,'delivery_agent');

-- ── 2. USERS ──────────────────────────────────────────────
CREATE TABLE users (
  user_id    INT          AUTO_INCREMENT PRIMARY KEY,
  username   VARCHAR(60)  NOT NULL UNIQUE,
  email      VARCHAR(120) NOT NULL UNIQUE,
  password   VARCHAR(256) NOT NULL,          -- Werkzeug hashed
  role_id    TINYINT      NOT NULL DEFAULT 2,
  phone      VARCHAR(20),
  is_active  TINYINT(1)   DEFAULT 1,
  created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (role_id) REFERENCES roles(role_id)
);
CREATE INDEX idx_users_email    ON users(email);
CREATE INDEX idx_users_role     ON users(role_id);

-- ── 3. ADDRESSES ──────────────────────────────────────────
CREATE TABLE addresses (
  address_id   INT          AUTO_INCREMENT PRIMARY KEY,
  user_id      INT          NOT NULL,
  label        VARCHAR(40)  DEFAULT 'Home',   -- Home / Office / Other
  line1        VARCHAR(200) NOT NULL,
  line2        VARCHAR(200),
  city         VARCHAR(80)  NOT NULL,
  state        VARCHAR(80),
  pincode      VARCHAR(12)  NOT NULL,
  is_default   TINYINT(1)   DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_addr_user ON addresses(user_id);

-- ── 4. CATEGORIES ─────────────────────────────────────────
CREATE TABLE categories (
  cat_id   INT         AUTO_INCREMENT PRIMARY KEY,
  name     VARCHAR(80) NOT NULL UNIQUE,
  slug     VARCHAR(80) NOT NULL UNIQUE
);

-- ── 5. PRODUCTS ───────────────────────────────────────────
CREATE TABLE products (
  product_id  INT            AUTO_INCREMENT PRIMARY KEY,
  cat_id      INT,
  name        VARCHAR(200)   NOT NULL,
  slug        VARCHAR(200)   NOT NULL UNIQUE,
  description TEXT,
  price       DECIMAL(10,2)  NOT NULL,
  stock       INT            NOT NULL DEFAULT 0,
  image_url   VARCHAR(300)   DEFAULT '',
  is_active   TINYINT(1)     DEFAULT 1,
  created_at  DATETIME       DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cat_id) REFERENCES categories(cat_id) ON DELETE SET NULL,
  FULLTEXT INDEX ft_product_search (name, description)
);
CREATE INDEX idx_prod_cat      ON products(cat_id);
CREATE INDEX idx_prod_price    ON products(price);
CREATE INDEX idx_prod_stock    ON products(stock);
CREATE INDEX idx_prod_active   ON products(is_active);

-- ── 6. DELIVERY AGENTS ────────────────────────────────────
CREATE TABLE delivery_agents (
  agent_id   INT         AUTO_INCREMENT PRIMARY KEY,
  user_id    INT         NOT NULL UNIQUE,
  vehicle    VARCHAR(60) DEFAULT 'Bike',
  zone       VARCHAR(80),
  is_active  TINYINT(1)  DEFAULT 1,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ── 7. ORDERS ─────────────────────────────────────────────
CREATE TABLE orders (
  order_id     INT            AUTO_INCREMENT PRIMARY KEY,
  user_id      INT            NOT NULL,
  address_id   INT,
  agent_id     INT,
  status       ENUM('Pending','Processing','Shipped',
                    'Out_for_Delivery','Delivered','Cancelled')
               DEFAULT 'Pending',
  total_amount DECIMAL(10,2)  DEFAULT 0,
  sla_hours    INT            DEFAULT 48,       -- expected delivery window
  ordered_at   DATETIME       DEFAULT CURRENT_TIMESTAMP,
  delivered_at DATETIME,
  notes        TEXT,
  payment_status VARCHAR(20)  DEFAULT 'PENDING',   -- PENDING, PAID, FAILED
  payment_id   VARCHAR(100),                       -- Razorpay payment ID
  razorpay_order_id VARCHAR(100),                  -- Razorpay order ID
  FOREIGN KEY (user_id)    REFERENCES users(user_id)    ON DELETE CASCADE,
  FOREIGN KEY (address_id) REFERENCES addresses(address_id) ON DELETE SET NULL,
  FOREIGN KEY (agent_id)   REFERENCES delivery_agents(agent_id) ON DELETE SET NULL
);
CREATE INDEX idx_orders_user      ON orders(user_id);
CREATE INDEX idx_orders_status    ON orders(status);
CREATE INDEX idx_orders_agent     ON orders(agent_id);
CREATE INDEX idx_orders_created   ON orders(ordered_at);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_payment_id     ON orders(payment_id);

-- ── 8. ORDER ITEMS ────────────────────────────────────────
CREATE TABLE order_items (
  item_id     INT            AUTO_INCREMENT PRIMARY KEY,
  order_id    INT            NOT NULL,
  product_id  INT            NOT NULL,
  quantity    INT            NOT NULL DEFAULT 1,
  unit_price  DECIMAL(10,2)  NOT NULL,
  FOREIGN KEY (order_id)   REFERENCES orders(order_id)   ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
);
CREATE INDEX idx_oi_order   ON order_items(order_id);
CREATE INDEX idx_oi_product ON order_items(product_id);

-- ── 9. ORDER STATUS LOGS ──────────────────────────────────
CREATE TABLE order_status_logs (
  log_id     INT         AUTO_INCREMENT PRIMARY KEY,
  order_id   INT         NOT NULL,
  status     VARCHAR(30) NOT NULL,
  note       VARCHAR(200),
  updated_by INT,                              -- user_id
  updated_at DATETIME    DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);
CREATE INDEX idx_log_order ON order_status_logs(order_id);
CREATE INDEX idx_log_time  ON order_status_logs(updated_at);

-- ── 10. REVIEWS ───────────────────────────────────────────
CREATE TABLE reviews (
  review_id   INT      AUTO_INCREMENT PRIMARY KEY,
  user_id     INT      NOT NULL,
  product_id  INT      NOT NULL,
  rating      TINYINT  NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment     TEXT,
  reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_review (user_id, product_id),
  FOREIGN KEY (user_id)    REFERENCES users(user_id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);
CREATE INDEX idx_rev_product ON reviews(product_id);

-- ── 11. NOTIFICATIONS ─────────────────────────────────────
CREATE TABLE notifications (
  notif_id   INT          AUTO_INCREMENT PRIMARY KEY,
  user_id    INT          NOT NULL,
  message    VARCHAR(300) NOT NULL,
  notif_type VARCHAR(30)  DEFAULT 'info',    -- info/success/warning
  is_read    TINYINT(1)   DEFAULT 0,
  created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_notif_user   ON notifications(user_id);
CREATE INDEX idx_notif_read   ON notifications(is_read);
CREATE INDEX idx_notif_time   ON notifications(created_at);

-- ── 12. CART ──────────────────────────────────────────────
CREATE TABLE cart (
  cart_id    INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  product_id INT NOT NULL,
  quantity   INT NOT NULL DEFAULT 1,
  added_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_cart (user_id, product_id),
  FOREIGN KEY (user_id)    REFERENCES users(user_id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);
CREATE INDEX idx_cart_user ON cart(user_id);

-- ═══════════════════════════════════════
--  SEED DATA
-- ═══════════════════════════════════════

-- Categories
INSERT INTO categories (name, slug) VALUES
('Fresh Flowers',      'fresh-flowers'),
('Bouquets',           'bouquets'),
('Indoor Plants',      'indoor-plants'),
('Outdoor Plants',     'outdoor-plants'),
('Gardening Tools',    'gardening-tools'),
('Seeds & Fertilizers','seeds-fertilizers'),
('Decorative Plants',  'decorative-plants');

-- Admin user  (password: Admin@123)
INSERT INTO users (username, email, password, role_id) VALUES
('admin', 'admin@ordersphere.com',
 'pbkdf2:sha256:1000000$Q3t7E74f0TCaW0f8$36bbb7c2b0acc306762eef75de3e0b772f6ca4fe9ea481cd0c89437fa269bf94',
 1);

-- Delivery agent user  (password: Agent@123)
INSERT INTO users (username, email, password, role_id, phone) VALUES
('agent_raj',  'raj@ordersphere.com',
 'pbkdf2:sha256:1000000$wAch0CpuINxTWcgQ$bd8550b1ff2f692d3cfc0cc30de58e68adf9f2d38704bd298bd99f47a6a5b65c',
 3, '9876543210'),
('agent_priya','priya@ordersphere.com',
 'pbkdf2:sha256:1000000$Ot0JymehicgirkoF$5c424d2acb9a03d831a819a2f55ec9b81704f8772579e3f2ee8897ed62479795',
 3, '9123456780');

INSERT INTO delivery_agents (user_id, vehicle, zone) VALUES
(2,'Bike','North Zone'),
(3,'Scooter','South Zone');

-- Sample customer  (password: User@123)
INSERT INTO users (username, email, password, role_id, phone) VALUES
('john_doe','john@example.com',
 'pbkdf2:sha256:1000000$RhDj4jl1YAAD0SlQ$4f6a11c947ae26225ff8770ea60f98efc7dc9256af3de8b27ca943c1c763d076',
 2, '9000011111');

INSERT INTO addresses (user_id, label, line1, city, state, pincode, is_default) VALUES
(4,'Home','12 MG Road','Mumbai','Maharashtra','400001',1);

-- Products
INSERT INTO products (cat_id, name, slug, description, price, stock, image_url) VALUES
(1,'Sony WH-1000XM5 Headphones','sony-wh1000xm5',
 'Industry-leading noise cancellation with 30hr battery life. Crystal clear calls.',
 24999.00, 45, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80'),
(1,'Apple iPad 10th Gen','apple-ipad-10',
 '10.9-inch Liquid Retina display, A14 Bionic chip, 5G capable.',
 44999.00, 20, 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&q=80'),
(1,'Samsung Galaxy Watch 6','samsung-watch6',
 'Advanced health tracking, sleep analysis, blood pressure monitoring.',
 19999.00, 38, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80'),
(2,'Nike Air Max 270','nike-airmax270',
 'Max Air heel unit delivers plush cushioning all day.',
 8999.00, 60, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80'),
(2,'Adidas Ultraboost 23','adidas-ultraboost23',
 'Responsive BOOST midsole returns energy with every stride.',
 12499.00, 30, 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400&q=80'),
(3,'Levi\'s 511 Slim Jeans','levis-511-slim',
 'Classic slim fit with just the right amount of stretch.',
 2999.00, 100, 'https://images.unsplash.com/photo-1542272454315-4c01d7abdf4a?w=400&q=80'),
(3,'Allen Solly Formal Shirt','allen-solly-formal',
 'Premium cotton blend, wrinkle-resistant formal shirt.',
 1499.00, 80, 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&q=80'),
(4,'Atomic Habits - James Clear','atomic-habits',
 'Tiny changes, remarkable results. #1 NYT bestseller.',
 399.00, 200, 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&q=80'),
(5,'Prestige Induction Cooktop','prestige-induction',
 '2000W, touch panel, 8 pre-set menus. ISI certified.',
 3499.00, 25, 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&q=80'),
(6,'Boldfit Yoga Mat','boldfit-yoga-mat',
 '6mm anti-slip TPE yoga mat with carry strap.',
 799.00, 150, 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&q=80');

UPDATE products SET cat_id=1, name='Premium Dutch Roses', slug='premium-dutch-roses',
 description='Long-stem fresh roses sourced for gifting, events, and same-day flower orders.',
 price=1299.00, stock=80, image_url='https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=600&q=80'
 WHERE product_id=1;
UPDATE products SET cat_id=2, name='Spring Garden Bouquet', slug='spring-garden-bouquet',
 description='Hand-tied bouquet with seasonal blooms, textured greens, and premium wrapping.',
 price=1899.00, stock=35, image_url='https://images.unsplash.com/photo-1561181286-d3fee7d55364?w=600&q=80'
 WHERE product_id=2;
UPDATE products SET cat_id=3, name='Monstera Deliciosa Plant', slug='monstera-deliciosa-plant',
 description='Low-maintenance indoor plant with sculptural split leaves and nursery pot.',
 price=1499.00, stock=42, image_url='https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=600&q=80'
 WHERE product_id=3;
UPDATE products SET cat_id=4, name='Hibiscus Outdoor Plant', slug='hibiscus-outdoor-plant',
 description='Sun-loving flowering plant for balconies, patios, and garden borders.',
 price=699.00, stock=64, image_url='https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?w=600&q=80'
 WHERE product_id=4;
UPDATE products SET cat_id=5, name='Ergonomic Garden Tool Set', slug='ergonomic-garden-tool-set',
 description='Durable trowel, cultivator, pruning shear, and gloves for everyday gardening.',
 price=999.00, stock=50, image_url='https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=80'
 WHERE product_id=5;
UPDATE products SET cat_id=6, name='Organic Vegetable Seeds Pack', slug='organic-vegetable-seeds-pack',
 description='Curated seeds for tomatoes, basil, spinach, coriander, and chillies.',
 price=349.00, stock=180, image_url='https://images.unsplash.com/photo-1459156212016-c812468e2115?w=600&q=80'
 WHERE product_id=6;
UPDATE products SET cat_id=6, name='Slow Release Plant Fertilizer', slug='slow-release-plant-fertilizer',
 description='Balanced nutrients for flowering plants, foliage, and kitchen gardens.',
 price=599.00, stock=95, image_url='https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?w=600&q=80'
 WHERE product_id=7;
UPDATE products SET cat_id=7, name='Ceramic Decorative Planter', slug='ceramic-decorative-planter',
 description='Minimal glazed planter for desks, shelves, and premium plant gifting.',
 price=799.00, stock=120, image_url='https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=600&q=80'
 WHERE product_id=8;
UPDATE products SET cat_id=1, name='Fresh Lily Bundle', slug='fresh-lily-bundle',
 description='Fragrant lilies with lush greens, ideal for celebrations and sympathy orders.',
 price=1199.00, stock=28, image_url='https://images.unsplash.com/photo-1501973931234-5ac2964cd94a?w=600&q=80'
 WHERE product_id=9;
UPDATE products SET cat_id=3, name='Snake Plant Laurentii', slug='snake-plant-laurentii',
 description='Air-purifying indoor plant that thrives in low light and busy homes.',
 price=899.00, stock=70, image_url='https://images.unsplash.com/photo-1593482892290-f54927ae1bb6?w=600&q=80'
 WHERE product_id=10;

-- Sample orders for demo analytics
INSERT INTO orders (user_id, address_id, agent_id, status, total_amount, ordered_at, delivered_at) VALUES
(4,1,1,'Delivered',  24999.00, DATE_SUB(NOW(),INTERVAL 10 DAY), DATE_SUB(NOW(),INTERVAL 8  DAY)),
(4,1,2,'Delivered',   8999.00, DATE_SUB(NOW(),INTERVAL 8  DAY), DATE_SUB(NOW(),INTERVAL 6  DAY)),
(4,1,1,'Shipped',    44999.00, DATE_SUB(NOW(),INTERVAL 3  DAY), NULL),
(4,1,NULL,'Processing',19999.00,DATE_SUB(NOW(),INTERVAL 1 DAY), NULL),
(4,1,NULL,'Pending',  2999.00, NOW(), NULL);

INSERT INTO order_items (order_id,product_id,quantity,unit_price) VALUES
(1,1,1,24999),(2,4,1,8999),(3,2,1,44999),(4,3,1,19999),(5,6,1,2999);

INSERT INTO order_status_logs (order_id,status,note,updated_by) VALUES
(1,'Pending',     'Order received',          4),
(1,'Processing',  'Payment confirmed',       1),
(1,'Shipped',     'Handed to Raj',           1),
(1,'Out_for_Delivery','Agent nearby',        2),
(1,'Delivered',   'Delivered successfully',  2),
(2,'Pending',     'Order received',          4),
(2,'Processing',  'Payment confirmed',       1),
(2,'Delivered',   'Express delivery',        3),
(3,'Pending',     'Order received',          4),
(3,'Processing',  'Packed',                  1),
(3,'Shipped',     'In transit',              1),
(4,'Pending',     'Order received',          4),
(4,'Processing',  'Being packed',            1),
(5,'Pending',     'Order received',          4);

INSERT INTO reviews (user_id,product_id,rating,comment) VALUES
(4,1,5,'Absolutely amazing headphones! Noise cancellation is top-notch.'),
(4,4,4,'Great comfort and cushioning. True to size.');

INSERT INTO notifications (user_id,message,notif_type,is_read) VALUES
(4,'Your order #3 has been shipped! 🚚','success',0),
(4,'Order #4 is now being processed.','info',0),
(4,'Welcome to OrderSphere! Start shopping now.','info',1);

SELECT 'OrderSphere DB setup complete! ✅' AS Status;
