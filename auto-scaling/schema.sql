-- ── ShopScale DB Schema ───────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS shopscale;
USE shopscale;

-- Categories
CREATE TABLE IF NOT EXISTS categories (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE
);

-- Products
CREATE TABLE IF NOT EXISTS products (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(200) NOT NULL,
  description TEXT,
  price       DECIMAL(10,2) NOT NULL,
  stock       INT DEFAULT 100,
  emoji       VARCHAR(10) DEFAULT '📦',
  category_id INT NOT NULL,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Users
CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(200) NOT NULL UNIQUE,
  password_hash VARCHAR(64) NOT NULL,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Reviews
CREATE TABLE IF NOT EXISTS reviews (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  product_id INT NOT NULL,
  rating     TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment    TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY one_review_per_user (user_id, product_id),
  FOREIGN KEY (user_id)    REFERENCES users(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Cart
CREATE TABLE IF NOT EXISTS cart (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  quantity   INT DEFAULT 1,
  session_id VARCHAR(100),
  added_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  user_id          INT NOT NULL,
  total            DECIMAL(10,2) NOT NULL,
  status           ENUM('pending','confirmed','shipped','delivered') DEFAULT 'confirmed',
  shipping_address TEXT,
  items_summary    TEXT,
  created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Order items
CREATE TABLE IF NOT EXISTS order_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id   INT NOT NULL,
  product_id INT NOT NULL,
  quantity   INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id)   REFERENCES orders(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

-- ── Seed Data ─────────────────────────────────────────────────────────────────
INSERT IGNORE INTO categories (name, slug) VALUES
  ('Electronics',   'electronics'),
  ('Clothing',      'clothing'),
  ('Home & Garden', 'home-garden'),
  ('Sports',        'sports'),
  ('Books',         'books'),
  ('Beauty',        'beauty');

INSERT IGNORE INTO products (name, description, price, stock, emoji, category_id) VALUES
  -- Electronics
  ('Wireless Earbuds Pro',    'Active noise cancellation, 30hr battery, IPX5 water resistant.',            89.99,  143, '🎧', 1),
  ('Smart Watch Series X',    '1.9" AMOLED display, heart rate, GPS, 7-day battery life.',                199.99,   67, '⌚', 1),
  ('Mechanical Keyboard',     'TKL layout, Cherry MX switches, RGB backlight, USB-C.',                    129.99,   88, '⌨️', 1),
  ('4K Webcam Ultra',         '4K 30fps, autofocus, built-in ring light, works with all platforms.',       79.99,   55, '📷', 1),
  ('Portable SSD 1TB',        'Read 1050MB/s, USB 3.2, shock-proof aluminum casing.',                      99.99,  112, '💾', 1),
  ('USB-C Hub 7-in-1',        'HDMI 4K, 3x USB-A, SD card, PD 100W passthrough.',                         39.99,  200, '🔌', 1),
  -- Clothing
  ('Merino Wool Hoodie',      'Sustainably sourced 100% merino, temperature regulating, odor resistant.', 119.99,   78, '🧥', 2),
  ('Running Shorts Pro',      '5" inseam, built-in liner, reflective trim, 3 pockets.',                    44.99,  156, '🩳', 2),
  ('Linen Button-Down',       'Portuguese linen, relaxed fit, perfect for warm weather.',                   69.99,   92, '👔', 2),
  ('Waterproof Trail Jacket', '2.5L shell, seam-sealed, packable into chest pocket.',                      149.99,   41, '🧤', 2),
  -- Home & Garden
  ('Air Purifier HEPA H13',   'Covers 500 sqft, 0.1μm filtration, whisper-quiet 25dB sleep mode.',       149.99,   63, '🌿', 3),
  ('Pour-Over Coffee Set',    'Borosilicate glass dripper + gooseneck kettle + 100 filters.',               59.99,   89, '☕', 3),
  ('Smart Plant Monitor',     'Soil moisture, light, temp & humidity — syncs to app via Bluetooth.',        34.99,  177, '🪴', 3),
  ('Bamboo Cutting Board',    'XL 18x12", juice groove, antimicrobial surface, easy-grip handles.',         29.99,  210, '🪵', 3),
  -- Sports
  ('Yoga Mat Premium',        '6mm thick, non-slip natural rubber, alignment lines, carry strap.',          54.99,  134, '🧘', 4),
  ('Adjustable Dumbbell Set', '5-52.5 lbs per dumbbell, 15 weight settings, compact storage.',            299.99,   23, '🏋️', 4),
  ('Road Cycling Helmet',     'MIPS protection, 18 vents, magnetic buckle, CE EN1078 certified.',          109.99,   47, '🚴', 4),
  ('Foam Roller Deep Tissue', 'High-density EVA, textured surface, 36" full-back coverage.',                29.99,  195, '🏃', 4),
  -- Books
  ('Designing Data-Intensive Applications', 'Martin Kleppmann. The definitive guide to distributed systems.', 45.99, 88, '📗', 5),
  ('The Staff Engineers Path',              'Tanya Reilly. Career guidance for senior IC engineers.',          35.99, 72, '📘', 5),
  ('System Design Interview Vol.2',         'Alex Xu. In-depth solutions for 13 real-world system designs.',   39.99, 104, '📙', 5),
  -- Beauty
  ('Vitamin C Serum 20%',          'L-ascorbic acid, ferulic acid, hyaluronic acid, 30ml.',                42.99,  166, '✨', 6),
  ('SPF 50 Tinted Moisturizer',    'Mineral UVA/UVB, 4 shades, non-comedogenic, dermatologist tested.',    36.99,  143, '🧴', 6),
  ('Jade Facial Roller',           'Genuine xiuyan jade, double-ended, reduces puffiness.',                 24.99,  218, '💆', 6);
