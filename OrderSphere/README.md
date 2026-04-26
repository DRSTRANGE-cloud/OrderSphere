# 📦 OrderSphere — Intelligent Order & Fulfillment Platform
### Stack: Python (Flask) · MySQL 8.0 · HTML · CSS · REST API

---

## 🌿 What's Inside

| Feature | Details |
|---|---|
| **Authentication** | Login / Signup with Werkzeug password hashing |
| **Role-Based Access** | Admin · Customer · Delivery Agent |
| **Product Catalogue** | Search (MySQL FULLTEXT), filter by category, sort |
| **Cart System** | Add, update quantity, remove, stock validation |
| **Order Tracking** | 5-stage pipeline with live status timeline |
| **Status Logs** | Every status change logged with timestamp + actor |
| **Notifications** | Bell icon with unread count, live polling |
| **Inventory** | Stock decremented on order, low-stock warnings |
| **SLA Monitoring** | Delayed orders (>48h) highlighted in red |
| **Delivery Agents** | Assigned to orders, update status from their dashboard |
| **Analytics** | Revenue trend, top products, category split, agent KPIs |
| **Addresses** | Multiple addresses per user, default selector |
| **Invoice** | Printable HTML invoice per order |
| **REST API** | GET /api/products · GET /api/orders · POST /api/order |
| **SEO** | Meta tags, Open Graph, canonical URLs, schema.org markup |
| **Concurrency** | MySQL connection pool (10 connections), threaded Flask |
| **Performance** | FULLTEXT index for search, composite indexes, JOIN optimization |

---

## ⚡ Execution Steps (Read Carefully)

### Step 1 — Install Python packages

Open your terminal / CMD:

```
pip install flask mysql-connector-python werkzeug
py -m pip install flask mysql-connector-python werkzeug
```

---

### Step 2 — Set up MySQL 8.0 Database

Open **MySQL 8.0 Command Line Client** (with blank password):

```
mysql -u root
```

Then inside MySQL shell:

```sql
SOURCE C:\path\to\ordersphere\setup_db.sql;
```

**Or** from Windows CMD / PowerShell (outside MySQL):

```
mysql -u root < C:\path\to\ordersphere\setup_db.sql
```

**Or** from Linux/Mac terminal:

```
mysql -u root < /path/to/ordersphere/setup_db.sql
```

You should see:  `Database setup complete! ✅`

---

### Step 3 — Fix Passwords (Required!)

The DB now seeds real Werkzeug password hashes. Run this only if you manually changed demo passwords and want to restore them:

```
cd ordersphere
python fix_passwords.py
```

You'll see:
```
  ✅  admin → password hash updated
  ✅  agent_raj → password hash updated
  ✅  agent_priya → password hash updated
  ✅  john_doe → password hash updated

All passwords fixed! You can now log in.
```

---

### Step 4 — Run the App

```
python app.py
```

Visit: **http://127.0.0.1:5000**

---

## 🔑 Login Credentials

| Role | Username | Password |
|---|---|---|
| 🛡️ Admin | `admin` | `Admin@123` |
| 👤 Customer | `john_doe` | `User@123` |
| 🚚 Agent | `agent_raj` | `Agent@123` |
| 🚚 Agent | `agent_priya` | `Agent@123` |

---

## 🗂️ Project Structure

```
ordersphere/
├── app.py                        ← Full Flask app (all routes, pool, decorators)
├── fix_passwords.py              ← Run once to hash passwords
├── setup_db.sql                  ← Full schema + seed data
├── requirements.txt
├── static/
│   └── css/
│       └── style.css             ← Forest theme design system
└── templates/
    ├── base.html                 ← Glassmorphism navbar, SEO meta
    ├── login.html
    ├── signup.html
    ├── index.html                ← Product grid with search + filter
    ├── product_detail.html       ← PDP with reviews + related
    ├── cart.html                 ← Cart + checkout
    ├── orders.html               ← Order list with SLA badges
    ├── order_detail.html         ← Timeline + admin controls
    ├── notifications.html
    ├── addresses.html
    ├── invoice.html              ← Printable invoice
    ├── admin/
    │   ├── dashboard.html        ← KPIs + bar chart + status dist
    │   ├── products.html
    │   ├── product_form.html     ← Add / Edit product
    │   ├── users.html
    │   ├── agents.html
    │   └── analytics.html        ← 30-day trend + top products + agent KPIs
    ├── agent/
    │   └── dashboard.html        ← Agent delivery queue
    └── errors/
        ├── 403.html
        └── 404.html
```

---

## 🗄️ Database Schema (Normalized — 3NF)

```
roles               → role_id, role_name
users               → user_id, username, email, password(hashed), role_id, phone
addresses           → address_id, user_id, label, line1, city, state, pincode
categories          → cat_id, name, slug
products            → product_id, cat_id, name, slug, price, stock, image_url
                      FULLTEXT INDEX on (name, description)
delivery_agents     → agent_id, user_id, vehicle, zone
orders              → order_id, user_id, address_id, agent_id, status, total_amount
order_items         → item_id, order_id, product_id, quantity, unit_price
order_status_logs   → log_id, order_id, status, note, updated_by, updated_at
reviews             → review_id, user_id, product_id, rating, comment
notifications       → notif_id, user_id, message, notif_type, is_read
cart                → cart_id, user_id, product_id, quantity
```

**Indexes added for performance:**
- `idx_orders_user`, `idx_orders_status`, `idx_orders_created`
- `idx_prod_cat`, `idx_prod_price`, `idx_prod_stock`
- `idx_notif_user`, `idx_notif_read`
- `ft_product_search` (FULLTEXT)

---

## 🌐 REST API Endpoints

| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/api/products` | Public | List all active products |
| GET | `/api/orders` | Login | My orders (admin sees all) |
| POST | `/api/order` | Login | Place order via API |
| GET | `/api/analytics` | Admin | Revenue summary |
| GET | `/api/notifications/count` | Login | Unread notification count |

---

## 🏎️ Concurrency & Performance

- **Connection Pool** — `MySQLConnectionPool(pool_size=10)` handles 10 concurrent DB connections
- **Threaded Flask** — `app.run(threaded=True)` handles multiple requests simultaneously
- **FULLTEXT search** — MySQL's native BOOLEAN MODE full-text search (fast, no N+1)
- **Optimized JOINs** — All order/product queries use single JOIN queries
- **Indexed columns** — `status`, `user_id`, `ordered_at`, `product_id` all indexed

---

## 🔐 Security

- Passwords hashed with `werkzeug.security.generate_password_hash` (PBKDF2-SHA256)
- Session cookie: `HttpOnly=True`, `SameSite=Lax`
- Role-based decorators: `@admin_required`, `@agent_required`
- SQL injection protection: all queries use parameterized `%s` placeholders
- Stock race conditions handled with DB-level `stock = stock - qty`

---

## 🌍 SEO Features

- `<meta name="description">` on every page
- `<meta name="keywords">` and `robots` tags
- Open Graph (`og:title`, `og:description`, `og:image`)
- `<link rel="canonical">` per page
- `schema.org/Product` microdata on product cards
- Semantic HTML (`<nav>`, `<main>`, `<article>`, `<footer>`, `aria-label`)
- `loading="lazy"` on all product images
- SEO-friendly product slugs (e.g. `/product/sony-wh1000xm5`)

---

## 🩺 Troubleshooting

| Problem | Fix |
|---|---|
| `Access denied for user 'root'` | Run `mysql -u root` (no -p flag, blank password) |
| `Unknown database ordersphere_db` | Run `setup_db.sql` first |
| `Invalid credentials` | Run `fix_passwords.py` |
| `Pool exhausted` | Increase `pool_size` in `app.py` |
| `ModuleNotFoundError` | Run `pip install flask mysql-connector-python werkzeug` |
