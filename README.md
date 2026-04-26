# 📦 OrderSphere — Intelligent Order & Fulfillment Platform

### Stack: Python (Flask) · MySQL 8.0 · HTML · CSS · REST API

---

## 🧩 Real-World Problem

In real-world e-commerce and logistics systems, teams face critical operational challenges:

* ❌ Inventory inconsistencies → overselling or stock mismatch
* ❌ Manual order tracking → delays and poor visibility
* ❌ Lack of role separation → admin, agent, and user workflows overlap
* ❌ No audit trail → difficult to debug order lifecycle issues
* ❌ Poor system scalability → slow search, inefficient queries
* ❌ Weak UI control → unsafe frontend interactions (e.g., unsafe JS, modal bugs)

These issues are common in **early-stage startups and internal tools**.

---

## 💡 Solution: OrderSphere

OrderSphere is designed as a **practical system to simulate real production constraints**, solving:

* Centralized product + order management
* Role-based system design (Admin / Customer / Delivery Agent)
* Full order lifecycle tracking with logs
* Inventory consistency with DB-level guarantees
* Scalable search and analytics
* Secure and predictable UI behavior

This project focuses on **learning by building production-like systems**, not just CRUD apps.

---

## ⚙️ Key Engineering Improvements (Recent Changes)

### 1. UI Bug Fix — Modal System

* Fixed modal always-visible bug caused by conflicting CSS (`display:flex !important`)
* Introduced controlled visibility via JS state

### 2. Frontend Security Hardening

* Eliminated unsafe inline JS injection:

```html
❌ '{{ p.name }}'
✅ {{ p.name | tojson }}
```

### 3. Robust DOM Handling

* Wrapped JS in `DOMContentLoaded` to prevent null reference errors

### 4. Better UI Architecture

* Moved toward event-driven JS instead of inline handlers

👉 These changes reflect **real frontend engineering practices**, not just templating.

---

## 🌿 What's Inside

| Feature               | Details                                                 |
| --------------------- | ------------------------------------------------------- |
| **Authentication**    | Login / Signup with Werkzeug password hashing           |
| **Role-Based Access** | Admin · Customer · Delivery Agent                       |
| **Product Catalogue** | Search (MySQL FULLTEXT), filter by category, sort       |
| **Cart System**       | Add, update quantity, remove, stock validation          |
| **Order Tracking**    | 5-stage pipeline with live status timeline              |
| **Status Logs**       | Every status change logged with timestamp + actor       |
| **Notifications**     | Bell icon with unread count, live polling               |
| **Inventory**         | Stock decremented on order, low-stock warnings          |
| **SLA Monitoring**    | Delayed orders (>48h) highlighted in red                |
| **Delivery Agents**   | Assigned to orders, update status from dashboard        |
| **Analytics**         | Revenue trend, top products, category split, agent KPIs |
| **Addresses**         | Multiple addresses per user                             |
| **Invoice**           | Printable HTML invoice                                  |
| **REST API**          | `/api/products`, `/api/orders`, `/api/order`            |
| **SEO**               | Meta tags, Open Graph, schema.org                       |
| **Concurrency**       | MySQL connection pool + threaded Flask                  |
| **Performance**       | FULLTEXT search + indexed queries                       |

---

## 🏗️ System Design Thinking

```
Client (Browser)
     ↓
Flask App (Routes)
     ↓
Service Logic (Validation, Auth, Business Rules)
     ↓
MySQL (Indexed, Normalized Schema)
```

### Design Decisions:

* **Server-side rendering (SSR)** → reduces frontend complexity
* **Connection pooling** → handles concurrent users efficiently
* **Normalized DB (3NF)** → avoids redundancy
* **Status logs** → ensures auditability (critical in real systems)

---

## ⚡ Execution Steps

### 1. Install Dependencies

```
pip install flask mysql-connector-python werkzeug
```

---

### 2. Setup Database

```
mysql -u root < setup_db.sql
```

---

### 3. Fix Password Hashes

```
python fix_passwords.py
```

---

### 4. Run Application

```
python app.py
```

Visit:

```
http://127.0.0.1:5000
```

---

## 🔑 Demo Credentials

| Role     | Username  | Password  |
| -------- | --------- | --------- |
| Admin    | admin     | Admin@123 |
| Customer | john_doe  | User@123  |
| Agent    | agent_raj | Agent@123 |

---

## 🗂️ Project Structure

```
ordersphere/
├── app.py
├── setup_db.sql
├── fix_passwords.py
├── templates/
├── static/
└── requirements.txt
```

---

## 🗄️ Database Design (3NF)

Key highlights:

* FULLTEXT index for product search
* Composite indexes for orders + products
* Separate status log table → audit trail
* Cart isolation → prevents order corruption

---

## 🌐 API Layer

| Method | Route           | Description    |
| ------ | --------------- | -------------- |
| GET    | `/api/products` | Fetch products |
| GET    | `/api/orders`   | Fetch orders   |
| POST   | `/api/order`    | Place order    |

---

## 🏎️ Performance Engineering

* O(log n) lookups via indexing
* FULLTEXT search avoids linear scans
* Connection pool avoids DB bottlenecks
* JOIN optimization prevents N+1 queries

---

## 🔐 Security Engineering

* PBKDF2 password hashing
* Parameterized queries → no SQL injection
* Role-based access decorators
* Controlled UI rendering (prevents XSS)

---

## 🧠 What This Project Teaches

* Real-world backend architecture (not toy CRUD)
* DB design + indexing strategy
* Concurrency handling in web apps
* Secure frontend-backend interaction
* Debugging production-like issues
* Bridging system design with implementation

---

## 📈 Future Work

* JWT authentication + RBAC
* Microservices split (orders, users, inventory)
* Redis caching
* Docker + CI/CD
* Async task queue (Celery)

---

## 🧪 Troubleshooting

| Issue         | Fix                     |
| ------------- | ----------------------- |
| DB not found  | Run setup_db.sql        |
| Login fails   | Run fix_passwords.py    |
| Push rejected | Use `git pull --rebase` |
| Module error  | Install dependencies    |

---

## 👨‍💻 Maintainer

DRSTRANGE-cloud

---
