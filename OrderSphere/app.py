"""
OrderSphere — Intelligent Order & Fulfillment Management Platform
Flask + MySQL 8.0  |  Production-ready MVP
"""

from flask import (Flask, render_template, request, redirect,
                   session, flash, jsonify, abort, url_for)
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import mysql.connector
from mysql.connector import pooling
from functools import wraps
from datetime import datetime, timedelta
from decimal import Decimal
import json
import re
import hmac
import os
import smtplib
from email.message import EmailMessage
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Load environment variables from .env file
if load_dotenv:
    load_dotenv()

# ═══════════════════════════════════════════════════════════
#  APP CONFIG
# ═══════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'ordersphere_ultra_secret_2024_xyz')
app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', 'ordersphere-auth-v2')
app.config['VERIFY_TOKEN_MAX_AGE'] = int(os.getenv('VERIFY_TOKEN_MAX_AGE', 86400))
app.config['RESET_TOKEN_MAX_AGE'] = int(os.getenv('RESET_TOKEN_MAX_AGE', 1800))

# ─── Connection Pool (handles concurrent users) ──────────
db_pool = pooling.MySQLConnectionPool(
    pool_name="ordersphere_pool",
    pool_size=10,                        # 10 concurrent connections
    pool_reset_session=True,
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', '123456'),
    database=os.getenv('DB_NAME', 'ordersphere_db'),
    charset=os.getenv('DB_CHARSET', 'utf8mb4'),
    use_unicode=True
)

def get_db():
    """Get a connection from the pool."""
    return db_pool.get_connection()

serializer = URLSafeTimedSerializer(app.secret_key)

NATURE_CATEGORIES = [
    ('Fresh Flowers', 'fresh-flowers'),
    ('Bouquets', 'bouquets'),
    ('Indoor Plants', 'indoor-plants'),
    ('Outdoor Plants', 'outdoor-plants'),
    ('Gardening Tools', 'gardening-tools'),
    ('Seeds & Fertilizers', 'seeds-fertilizers'),
]

NATURE_PRODUCTS = [
    ('fresh-flowers','Premium Dutch Roses','premium-dutch-roses','Fresh long-stem roses selected for gifting, events, and elegant home styling.',1299,80,'https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=600&q=80'),
    ('fresh-flowers','Fresh Lily Bundle','fresh-lily-bundle','Fragrant lilies with lush greens for celebrations and graceful floral orders.',1199,48,'https://images.unsplash.com/photo-1501973931234-5ac2964cd94a?w=600&q=80'),
    ('fresh-flowers','Sunflower Stem Pack','sunflower-stem-pack','Bright fresh sunflowers bundled for cheerful gifting and decor.',899,52,'https://images.unsplash.com/photo-1470509037663-253afd7f0f51?w=600&q=80'),
    ('fresh-flowers','Orchid Flower Stems','orchid-flower-stems','Premium orchid stems with long-lasting color and refined presentation.',1599,34,'https://images.unsplash.com/photo-1566908829550-e6551b00979b?w=600&q=80'),
    ('bouquets','Spring Garden Bouquet','spring-garden-bouquet','Hand-tied bouquet with seasonal blooms, textured greens, and premium wrapping.',1899,35,'https://images.unsplash.com/photo-1561181286-d3fee7d55364?w=600&q=80'),
    ('bouquets','Classic Rose Bouquet','classic-rose-bouquet','A timeless rose bouquet wrapped for birthdays, anniversaries, and proposals.',1499,44,'https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=600&q=80'),
    ('bouquets','Pastel Mixed Bouquet','pastel-mixed-bouquet','Soft pastel bouquet with gentle tones for premium gifting moments.',1699,30,'https://images.unsplash.com/photo-1487070183336-b863922373d4?w=600&q=80'),
    ('indoor-plants','Monstera Deliciosa','monstera-deliciosa','Statement indoor plant with broad split leaves for premium homes and offices.',1499,42,'https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=600&q=80'),
    ('indoor-plants','Snake Plant Laurentii','snake-plant-laurentii','Air-purifying plant that handles low light and busy schedules beautifully.',899,70,'https://images.unsplash.com/photo-1593482892290-f54927ae1bb6?w=600&q=80'),
    ('indoor-plants','Peace Lily Plant','peace-lily-plant','Elegant white blooms with glossy foliage for desks, bedrooms, and lounges.',1099,38,'https://images.unsplash.com/photo-1520412099551-62b6bafeb5bb?w=600&q=80'),
    ('indoor-plants','ZZ Plant','zz-plant','Glossy, drought-tolerant indoor plant with a clean architectural look.',999,55,'https://images.unsplash.com/photo-1632207691143-643e2a9a9361?w=600&q=80'),
    ('outdoor-plants','Hibiscus Outdoor Plant','hibiscus-outdoor-plant','Sun-loving flowering plant for balconies, patios, and garden borders.',699,64,'https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?w=600&q=80'),
    ('outdoor-plants','Bougainvillea Pot Plant','bougainvillea-pot-plant','Hardy outdoor bloomer with vibrant bracts for terraces and entrances.',799,46,'https://images.unsplash.com/photo-1622923824240-05b2f1db6f38?w=600&q=80'),
    ('outdoor-plants','Areca Palm','areca-palm','Lush palm for verandas, office corners, and shaded outdoor spaces.',1299,32,'https://images.unsplash.com/photo-1592150621744-aca64f48394a?w=600&q=80'),
    ('gardening-tools','Ergonomic Garden Tool Set','ergonomic-garden-tool-set','Durable trowel, cultivator, pruning shear, and gloves for everyday gardening.',999,50,'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=80'),
    ('gardening-tools','Premium Pruning Shears','premium-pruning-shears','Sharp hand pruners for flowers, shrubs, herbs, and balcony gardens.',699,75,'https://images.unsplash.com/photo-1599685315640-091a5e92cc3a?w=600&q=80'),
    ('gardening-tools','Watering Can Matte Black','watering-can-matte-black','Balanced watering can for indoor plants, seedlings, and patio planters.',799,58,'https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?w=600&q=80'),
    ('seeds-fertilizers','Organic Vegetable Seeds Pack','organic-vegetable-seeds-pack','Curated seeds for tomatoes, basil, spinach, coriander, and chillies.',349,180,'https://images.unsplash.com/photo-1459156212016-c812468e2115?w=600&q=80'),
    ('seeds-fertilizers','Slow Release Plant Fertilizer','slow-release-plant-fertilizer','Balanced nutrients for flowering plants, foliage, and kitchen gardens.',599,95,'https://images.unsplash.com/photo-1589923188900-85dae523342b?w=600&q=80'),
    ('seeds-fertilizers','Organic Potting Mix','organic-potting-mix','Lightweight soil mix with compost, cocopeat, and drainage support.',399,160,'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=80'),
]

catalog_synced = False
demo_auth_repaired = False

# ═══════════════════════════════════════════════════════════
#  DECORATORS
# ═══════════════════════════════════════════════════════════
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def agent_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') not in ('admin', 'delivery_agent'):
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def notify(user_id, message, ntype='info'):
    """Insert a notification for a user."""
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO notifications (user_id, message, notif_type) VALUES (%s,%s,%s)",
            (user_id, message, ntype))
        conn.commit()
        cur.close(); conn.close()
    except Exception:
        pass

def log_status(order_id, status, note='', updated_by=None):
    """Append to order_status_logs."""
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO order_status_logs (order_id,status,note,updated_by) VALUES (%s,%s,%s,%s)",
            (order_id, status, note, updated_by))
        conn.commit()
        cur.close(); conn.close()
    except Exception:
        pass

def unread_count(user_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id=%s AND is_read=0", (user_id,))
        c = cur.fetchone()[0]
        cur.close(); conn.close()
        return c
    except Exception:
        return 0

def wants_json():
    return request.path.startswith('/api/') or request.accept_mimetypes.best == 'application/json'

def json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value

def row_to_json(row):
    return {k: json_value(v) for k, v in row.items()}

def ensure_nature_catalog(force=False):
    global catalog_synced
    if catalog_synced and not force:
        return
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        for name, slug in NATURE_CATEGORIES:
            cur.execute("""
                INSERT INTO categories (name, slug) VALUES (%s,%s)
                ON DUPLICATE KEY UPDATE name=VALUES(name), slug=VALUES(slug)
            """, (name, slug))
        conn.commit()

        cur.execute("SELECT cat_id, slug FROM categories")
        cat_ids = {row['slug']: row['cat_id'] for row in cur.fetchall()}
        product_slugs = [p[2] for p in NATURE_PRODUCTS]

        for cat_slug, name, slug, desc, price, stock, image_url in NATURE_PRODUCTS:
            cur.execute("""
                INSERT INTO products (cat_id,name,slug,description,price,stock,image_url,is_active)
                VALUES (%s,%s,%s,%s,%s,%s,%s,1)
                ON DUPLICATE KEY UPDATE
                  cat_id=VALUES(cat_id), name=VALUES(name), description=VALUES(description),
                  price=VALUES(price), stock=VALUES(stock), image_url=VALUES(image_url), is_active=1
            """, (cat_ids[cat_slug], name, slug, desc, price, stock, image_url))

        placeholders = ",".join(["%s"] * len(product_slugs))
        cur.execute(f"UPDATE products SET is_active=0 WHERE slug NOT IN ({placeholders})", product_slugs)
        category_slugs = [slug for _, slug in NATURE_CATEGORIES]
        cat_placeholders = ",".join(["%s"] * len(category_slugs))
        cur.execute(f"DELETE FROM categories WHERE slug NOT IN ({cat_placeholders})", category_slugs)
        conn.commit()
        catalog_synced = True
    finally:
        cur.close(); conn.close()

def repair_demo_accounts(force=False):
    global demo_auth_repaired
    if demo_auth_repaired and not force:
        return
    credentials = {
        'admin': '123456',
        'agent_raj': '123456',
        'agent_priya': 'Agent@123',
        'john_doe': 'User@123',
    }
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT role_id, role_name FROM roles")
        roles = {row['role_name']: row['role_id'] for row in cur.fetchall()}
        for username, password in credentials.items():
            cur.execute("SELECT user_id, password FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
            if not user:
                role_name = 'admin' if username == 'admin' else ('delivery_agent' if username.startswith('agent_') else 'customer')
                email = {
                    'admin': 'admin@ordersphere.com',
                    'agent_raj': 'raj@ordersphere.com',
                    'agent_priya': 'priya@ordersphere.com',
                    'john_doe': 'john@example.com',
                }[username]
                phone = {
                    'admin': None,
                    'agent_raj': '9876543210',
                    'agent_priya': '9123456780',
                    'john_doe': '9000011111',
                }[username]
                cur.execute("""
                    INSERT INTO users (username,email,password,role_id,phone,is_active)
                    VALUES (%s,%s,%s,%s,%s,1)
                """, (username, email, generate_password_hash(password), roles[role_name], phone))
                user_id = cur.lastrowid
                if role_name == 'customer':
                    cur.execute("""
                        INSERT INTO addresses (user_id,label,line1,city,state,pincode,is_default)
                        VALUES (%s,'Home','12 MG Road','Mumbai','Maharashtra','400001',1)
                    """, (user_id,))
                elif role_name == 'delivery_agent':
                    zone = 'North Zone' if username == 'agent_raj' else 'South Zone'
                    vehicle = 'Bike' if username == 'agent_raj' else 'Scooter'
                    cur.execute("INSERT IGNORE INTO delivery_agents (user_id, vehicle, zone) VALUES (%s,%s,%s)",
                                (user_id, vehicle, zone))
                continue
            try:
                valid = check_password_hash(str(user['password']), password)
            except Exception:
                valid = False
            if not valid:
                cur.execute("UPDATE users SET password=%s, is_active=1 WHERE user_id=%s",
                            (generate_password_hash(password), user['user_id']))
            if username == 'john_doe':
                cur.execute("SELECT COUNT(*) AS c FROM addresses WHERE user_id=%s", (user['user_id'],))
                if cur.fetchone()['c'] == 0:
                    cur.execute("""
                        INSERT INTO addresses (user_id,label,line1,city,state,pincode,is_default)
                        VALUES (%s,'Home','12 MG Road','Mumbai','Maharashtra','400001',1)
                    """, (user['user_id'],))
        conn.commit()
        demo_auth_repaired = True
    finally:
        cur.close(); conn.close()

def password_is_strong(password):
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password)
    )

def password_matches(user, password):
    stored = str(user.get('password') or '')
    try:
        if check_password_hash(stored, password):
            return True
    except Exception:
        pass

    # Repair accidental plain-text passwords such as:
    # UPDATE users SET password=123456 WHERE username='admin';
    if stored and hmac.compare_digest(stored, password):
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET password=%s WHERE user_id=%s",
                    (generate_password_hash(password), user['user_id']))
        conn.commit()
        cur.close(); conn.close()
        return True
    return False

def build_token(email, purpose):
    return serializer.dumps({'email': email.lower(), 'purpose': purpose},
                            salt=app.config['SECURITY_PASSWORD_SALT'])

def read_token(token, purpose, max_age):
    data = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=max_age)
    if data.get('purpose') != purpose:
        raise BadSignature('Invalid token purpose')
    return data

def emit_email(to_email, subject, link):
    """
    Send email via Gmail SMTP or print to console (development mode).
    
    Environment variables needed (optional):
    - GMAIL_USER: Gmail address
    - GMAIL_APP_PASSWORD: Gmail app password (from https://myaccount.google.com/apppasswords)
    
    If credentials are missing, prints link to console for testing.
    """
    gmail_user = os.getenv('ORDERSPHERE_GMAIL_USER') or os.getenv('GMAIL_USER')
    gmail_password = os.getenv('ORDERSPHERE_GMAIL_APP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        # Development mode: print to console
        print("\n" + "="*70)
        print(f"📧 EMAIL (Console Mode - Gmail not configured)")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-"*70)
        print(f"Hello,\n\nUse this secure OrderSphere link:\n{link}\n\n"
              "If you did not request this, you can ignore this email.")
        print("="*70 + "\n")
        return True  # Still consider it successful for development

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = os.getenv('MAIL_FROM', gmail_user)
        msg['To'] = to_email
        msg.set_content(
            f"Hello,\n\nUse this secure OrderSphere link:\n{link}\n\n"
            "If you did not request this, you can ignore this email."
        )

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as smtp:
            smtp.login(gmail_user, gmail_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False

def login_user(user, remember=False):
    session.clear()
    session.permanent = bool(remember)
    session['user_id']  = user['user_id']
    session['username'] = user['username']
    session['email']    = user.get('email')
    session['role']     = user['role_name']

def cart_count(user_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(quantity),0) FROM cart WHERE user_id=%s", (user_id,))
        c = cur.fetchone()[0]
        cur.close(); conn.close()
        return int(c)
    except Exception:
        return 0

# ─── Template context ───────────────────────────────────
@app.context_processor
def inject_globals():
    uid = session.get('user_id')
    if uid:
        return dict(
            g_unread=unread_count(uid),
            g_cart=cart_count(uid),
            g_role=session.get('role','customer'),
            g_username=session.get('username','')
        )
    return dict(g_unread=0, g_cart=0, g_role='', g_username='')

# ═══════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════
@app.route('/login', methods=['GET','POST'])
def login():
    repair_demo_accounts()
    if 'user_id' in session:
        return redirect('/')
    if request.method == 'POST':
        username = request.form.get('username','').strip().lower()
        password = request.form['password']
        remember = bool(request.form.get('remember'))
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT u.user_id, u.username, u.email, u.password, u.is_active, r.role_name
            FROM users u JOIN roles r ON u.role_id=r.role_id
            WHERE LOWER(u.username)=%s OR LOWER(u.email)=%s
        """, (username, username))
        user = cur.fetchone()
        cur.close(); conn.close()
        if not user or not password_matches(user, password):
            flash("Invalid username/email or password.", "error")
            return render_template("login.html", login_identifier=username)
        if not user['is_active']:
            token = build_token(user['email'], 'verify')
            verify_link = url_for('verify_email', token=token, _external=True)
            sent = emit_email(user['email'], 'Verify your OrderSphere account', verify_link)
            flash("Please verify your email first. Check your email for verification link." if sent else
                  "Please verify your email first. Check console for verification link.", "warning")
            return render_template("login.html", login_identifier=username)

        # Login the user
        login_user(user, remember)
        flash(f"Welcome back, {user['username']}! 👋", "success")
        
        # Role-based redirect
        if user['role_name'] == 'admin':
            return redirect('/admin/dashboard')
        elif user['role_name'] == 'delivery_agent':
            return redirect('/agent/dashboard')
        else:
            return redirect('/')
    return render_template("login.html")

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        phone    = request.form.get('phone','').strip()
        if not re.match(r'^[A-Za-z0-9_.-]{3,60}$', username):
            flash("Username must be 3-60 characters using letters, numbers, dots, dashes, or underscores.", "error")
            return render_template("signup.html")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            flash("Enter a valid email address.", "error")
            return render_template("signup.html")
        if not password_is_strong(password):
            flash("Password must be 8+ characters with uppercase, lowercase, and a number.", "error")
            return render_template("signup.html")
        hashed = generate_password_hash(password)
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username,email,password,role_id,phone,is_active) VALUES (%s,%s,%s,2,%s,0)",
                (username, email, hashed, phone or None))
            conn.commit()
            uid = cur.lastrowid
            token = build_token(email, 'verify')
            verify_link = url_for('verify_email', token=token, _external=True)
            sent = emit_email(email, 'Verify your OrderSphere account', verify_link)
            notify(uid, "Welcome to OrderSphere 🎉 Verify your email to start ordering.", "success")
            flash("Account created! Check your email for verification link." if sent else
                  "Account created! Email verification link will be printed to console.", "success")
            return redirect('/login')
        except mysql.connector.IntegrityError:
            flash("Username or email already exists.", "error")
        finally:
            cur.close(); conn.close()
    return render_template("signup.html")

@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        data = read_token(token, 'verify', app.config['VERIFY_TOKEN_MAX_AGE'])
    except SignatureExpired:
        flash("Verification link expired. Log in to request a fresh one.", "error")
        return redirect('/login')
    except BadSignature:
        flash("Invalid verification link.", "error")
        return redirect('/login')

    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET is_active=1 WHERE LOWER(email)=%s", (data['email'],))
    conn.commit()
    cur.close(); conn.close()
    flash("Email verified. You can now sign in.", "success")
    return redirect('/login')

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT user_id, email FROM users WHERE LOWER(email)=%s", (email,))
        user = cur.fetchone()
        cur.close(); conn.close()
        if user:
            token = build_token(user['email'], 'reset')
            reset_link = url_for('reset_password', token=token, _external=True)
            emit_email(user['email'], 'Reset your OrderSphere password', reset_link)
        flash("If that email exists, a password reset link has been sent.", "success")
        return redirect('/login')
    return render_template("forgot_password.html")

@app.route('/reset-password/<token>', methods=['GET','POST'])
def reset_password(token):
    try:
        data = read_token(token, 'reset', app.config['RESET_TOKEN_MAX_AGE'])
    except SignatureExpired:
        flash("Password reset link expired.", "error")
        return redirect('/forgot-password')
    except BadSignature:
        flash("Invalid password reset link.", "error")
        return redirect('/forgot-password')

    if request.method == 'POST':
        password = request.form.get('password','')
        if not password_is_strong(password):
            flash("Password must be 8+ characters with uppercase, lowercase, and a number.", "error")
            return render_template("reset_password.html", token=token)
        hashed = generate_password_hash(password)
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET password=%s, is_active=1 WHERE LOWER(email)=%s", (hashed, data['email']))
        conn.commit()
        cur.close(); conn.close()
        flash("Password reset complete. Please sign in.", "success")
        return redirect('/login')
    return render_template("reset_password.html", token=token)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ═══════════════════════════════════════════════════════════
#  DASHBOARD / HOME
# ═══════════════════════════════════════════════════════════
@app.route('/')
@login_required
def index():
    ensure_nature_catalog()
    role = session.get('role')
    if role == 'admin':
        return redirect('/admin/dashboard')
    if role == 'delivery_agent':
        return redirect('/agent/dashboard')

    uid  = session['user_id']
    conn = get_db(); cur = conn.cursor(dictionary=True)

    # Search + filter
    search   = request.args.get('q','').strip()
    cat_id   = request.args.get('cat','')
    sort_by  = request.args.get('sort','newest')

    base_sql = """
        SELECT p.product_id, p.name, p.slug, p.description, p.price,
               p.stock, p.image_url, c.name AS category,
               COALESCE(AVG(r.rating),0) AS avg_rating,
               COUNT(r.review_id) AS review_count
        FROM products p
        LEFT JOIN categories c ON p.cat_id = c.cat_id
        LEFT JOIN reviews r    ON r.product_id = p.product_id
        WHERE p.is_active = 1
    """
    params = []
    if search:
        base_sql += " AND MATCH(p.name, p.description) AGAINST (%s IN BOOLEAN MODE)"
        params.append(f"+{search}*")
    if cat_id:
        base_sql += " AND p.cat_id = %s"
        params.append(cat_id)

    base_sql += " GROUP BY p.product_id"

    order_map = {
        'newest': ' ORDER BY p.created_at DESC',
        'price_asc': ' ORDER BY p.price ASC',
        'price_desc': ' ORDER BY p.price DESC',
        'rating': ' ORDER BY avg_rating DESC'
    }
    base_sql += order_map.get(sort_by, order_map['newest'])

    cur.execute(base_sql, params)
    products = cur.fetchall()

    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS c FROM orders WHERE user_id=%s", (uid,))
    my_orders = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) AS c FROM products WHERE is_active=1")
    total_products = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) AS c FROM orders WHERE user_id=%s AND status='Delivered'", (uid,))
    delivered = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) AS c FROM orders WHERE user_id=%s AND status NOT IN ('Delivered','Cancelled')", (uid,))
    active_orders = cur.fetchone()['c']

    cur.close(); conn.close()
    return render_template("index.html",
        products=products, categories=categories,
        my_orders=my_orders, delivered=delivered,
        active_orders=active_orders,
        total_products=total_products,
        search=search, cat_id=cat_id, sort_by=sort_by
    )

# ═══════════════════════════════════════════════════════════
#  PRODUCT DETAIL
# ═══════════════════════════════════════════════════════════
@app.route('/product/<slug>')
@login_required
def product_detail(slug):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.name AS category
        FROM products p LEFT JOIN categories c ON p.cat_id=c.cat_id
        WHERE p.slug=%s AND p.is_active=1
    """, (slug,))
    product = cur.fetchone()
    if not product:
        abort(404)

    cur.execute("""
        SELECT r.rating, r.comment, r.reviewed_at, u.username
        FROM reviews r JOIN users u ON r.user_id=u.user_id
        WHERE r.product_id=%s ORDER BY r.reviewed_at DESC
    """, (product['product_id'],))
    reviews = cur.fetchall()

    cur.execute("SELECT AVG(rating) AS avg FROM reviews WHERE product_id=%s", (product['product_id'],))
    avg_row = cur.fetchone()
    avg_rating = round(float(avg_row['avg']),1) if avg_row['avg'] else None

    # Related products (same category)
    cur.execute("""
        SELECT p.product_id, p.name, p.slug, p.price, p.image_url,
               COALESCE(AVG(r.rating),0) AS avg_rating
        FROM products p LEFT JOIN reviews r ON r.product_id=p.product_id
        WHERE p.cat_id=%s AND p.product_id != %s AND p.is_active=1
        GROUP BY p.product_id LIMIT 4
    """, (product['cat_id'], product['product_id']))
    related = cur.fetchall()

    cur.close(); conn.close()
    return render_template("product_detail.html",
        product=product, reviews=reviews,
        avg_rating=avg_rating, related=related
    )

# ═══════════════════════════════════════════════════════════
#  CART
# ═══════════════════════════════════════════════════════════
@app.route('/cart')
@login_required
def view_cart():
    uid  = session['user_id']
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.cart_id, c.quantity, p.product_id, p.name, p.price,
               p.image_url, p.stock, (c.quantity * p.price) AS subtotal
        FROM cart c JOIN products p ON c.product_id=p.product_id
        WHERE c.user_id=%s
    """, (uid,))
    items = cur.fetchall()
    total = sum(float(i['subtotal']) for i in items)
    cur.execute("SELECT * FROM addresses WHERE user_id=%s ORDER BY is_default DESC", (uid,))
    addresses = cur.fetchall()
    cur.close(); conn.close()
    return render_template("cart.html", items=items, total=total, addresses=addresses)

@app.route('/cart/add/<int:pid>', methods=['POST'])
@login_required
def add_to_cart(pid):
    uid = session['user_id']
    qty = int(request.form.get('quantity', 1))
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT stock FROM products WHERE product_id=%s", (pid,))
    row = cur.fetchone()
    if not row or row[0] < qty:
        flash("Insufficient stock.", "error")
        cur.close(); conn.close()
        return redirect(request.referrer or '/')
    cur.execute("""
        INSERT INTO cart (user_id, product_id, quantity)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE quantity = quantity + %s
    """, (uid, pid, qty, qty))
    conn.commit()
    cur.close(); conn.close()
    flash("Added to cart! 🛒", "success")
    return redirect(request.referrer or '/')

@app.route('/cart/remove/<int:cid>')
@login_required
def remove_from_cart(cid):
    uid = session['user_id']
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE cart_id=%s AND user_id=%s", (cid, uid))
    conn.commit()
    cur.close(); conn.close()
    return redirect('/cart')

@app.route('/cart/update/<int:cid>', methods=['POST'])
@login_required
def update_cart(cid):
    qty = int(request.form.get('quantity', 1))
    uid = session['user_id']
    conn = get_db(); cur = conn.cursor()
    if qty < 1:
        cur.execute("DELETE FROM cart WHERE cart_id=%s AND user_id=%s", (cid, uid))
    else:
        cur.execute("UPDATE cart SET quantity=%s WHERE cart_id=%s AND user_id=%s", (qty, cid, uid))
    conn.commit()
    cur.close(); conn.close()
    return redirect('/cart')

@app.route('/order/place/<int:pid>')
@login_required
def place_order(pid):
    """Buy Now: create a one-item order and redirect to tracking."""
    uid = session['user_id']
    qty = 1

    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT product_id, stock, name, slug, price FROM products WHERE product_id=%s AND is_active=1", (pid,))
    product = cur.fetchone()

    if not product:
        flash("Product not found or is unavailable.", "error")
        cur.close(); conn.close()
        return redirect('/')

    if product['stock'] < qty:
        flash(f"'{product['name']}' is out of stock.", "error")
        cur.close(); conn.close()
        return redirect(f"/product/{product['slug']}")

    cur.execute("SELECT address_id FROM addresses WHERE user_id=%s ORDER BY is_default DESC, address_id ASC LIMIT 1", (uid,))
    address = cur.fetchone()
    if not address:
        flash("Add a delivery address before using Buy Now.", "warning")
        cur.close(); conn.close()
        return redirect('/addresses')

    try:
        total = float(product['price']) * qty
        cur.execute("""
            INSERT INTO orders (user_id, address_id, status, total_amount, notes)
            VALUES (%s,%s,'Pending',%s,%s)
        """, (uid, address['address_id'], total, 'Buy Now - Payment: COD'))
        conn.commit()
        order_id = cur.lastrowid
        cur.execute("""
            INSERT INTO order_items (order_id,product_id,quantity,unit_price)
            VALUES (%s,%s,%s,%s)
        """, (order_id, product['product_id'], qty, product['price']))
        cur.execute("UPDATE products SET stock = stock - %s WHERE product_id=%s", (qty, product['product_id']))
        conn.commit()
        log_status(order_id, 'Pending', 'Buy Now order placed by customer', uid)
        notify(uid, f"Order #{order_id} placed successfully.", "success")
        flash(f"Order #{order_id} placed successfully.", "success")
        return redirect(f'/orders/{order_id}')
    except Exception:
        conn.rollback()
        flash("Failed to place order. Please try again.", "error")
        return redirect(f"/product/{product['slug']}")
    finally:
        cur.close(); conn.close()

# ═══════════════════════════════════════════════════════════
#  CHECKOUT & PLACE ORDER
# ═══════════════════════════════════════════════════════════
@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    uid        = session['user_id']
    address_id = request.form.get('address_id')
    notes      = request.form.get('notes','').strip()
    payment_method = request.form.get('payment_method', 'COD')
    if payment_method not in ('COD', 'UPI', 'Card'):
        payment_method = 'COD'

    conn = get_db(); cur = conn.cursor(dictionary=True)

    # Load cart
    cur.execute("""
        SELECT c.quantity, p.product_id, p.name, p.price, p.stock
        FROM cart c JOIN products p ON c.product_id=p.product_id
        WHERE c.user_id=%s
    """, (uid,))
    cart_items = cur.fetchall()

    if not cart_items:
        flash("Your cart is empty.", "error")
        cur.close(); conn.close()
        return redirect('/cart')

    # Check stock
    for item in cart_items:
        if item['stock'] < item['quantity']:
            flash(f"'{item['name']}' has only {item['stock']} units left.", "error")
            cur.close(); conn.close()
            return redirect('/cart')

    total = sum(float(i['price']) * i['quantity'] for i in cart_items)

    try:
        # Create order
        cur2 = conn.cursor()
        cur2.execute("""
            INSERT INTO orders (user_id, address_id, status, total_amount, notes)
            VALUES (%s,%s,'Pending',%s,%s)
        """, (uid, address_id or None, total, f"Payment: {payment_method}" + (f" | {notes}" if notes else "")))
        conn.commit()
        order_id = cur2.lastrowid

        # Insert items & reduce stock
        for item in cart_items:
            cur2.execute("""
                INSERT INTO order_items (order_id,product_id,quantity,unit_price)
                VALUES (%s,%s,%s,%s)
            """, (order_id, item['product_id'], item['quantity'], item['price']))
            cur2.execute(
                "UPDATE products SET stock = stock - %s WHERE product_id=%s",
                (item['quantity'], item['product_id']))

        # Clear cart
        cur2.execute("DELETE FROM cart WHERE user_id=%s", (uid,))
        conn.commit()

        log_status(order_id, 'Pending', 'Order placed by customer', uid)
        notify(uid, f"Order #{order_id} placed successfully! 🎉", "success")

        cur2.close(); cur.close(); conn.close()
        flash(f"Order #{order_id} placed! 🎉", "success")
        return redirect(f'/orders/{order_id}')

    except Exception as e:
        conn.rollback()
        flash("Failed to place order. Please try again.", "error")
        return redirect('/cart')

# ═══════════════════════════════════════════════════════════
#  ORDERS
# ═══════════════════════════════════════════════════════════
@app.route('/orders')
@login_required
def orders():
    uid  = session['user_id']
    role = session.get('role')
    conn = get_db(); cur = conn.cursor(dictionary=True)

    status_filter = request.args.get('status','')

    if role == 'admin':
        sql = """
            SELECT o.order_id, o.status, o.total_amount, o.ordered_at, o.delivered_at,
                   u.username, u.email,
                   da.user_id AS agent_uid,
                   au.username AS agent_name,
                   (SELECT COUNT(*) FROM order_items WHERE order_id=o.order_id) AS item_count,
                   TIMESTAMPDIFF(HOUR, o.ordered_at, NOW()) AS age_hours
            FROM orders o
            JOIN users u ON o.user_id=u.user_id
            LEFT JOIN delivery_agents da ON o.agent_id=da.agent_id
            LEFT JOIN users au ON da.user_id=au.user_id
        """
        params = []
        if status_filter:
            sql += " WHERE o.status=%s"
            params.append(status_filter)
        sql += " ORDER BY o.ordered_at DESC"
        cur.execute(sql, params)
    else:
        sql = """
            SELECT o.order_id, o.status, o.total_amount, o.ordered_at, o.delivered_at,
                   u.username, u.email,
                   au.username AS agent_name,
                   (SELECT COUNT(*) FROM order_items WHERE order_id=o.order_id) AS item_count,
                   TIMESTAMPDIFF(HOUR, o.ordered_at, NOW()) AS age_hours
            FROM orders o
            JOIN users u ON o.user_id=u.user_id
            LEFT JOIN delivery_agents da ON o.agent_id=da.agent_id
            LEFT JOIN users au ON da.user_id=au.user_id
            WHERE o.user_id=%s
        """
        params = [uid]
        if status_filter:
            sql += " AND o.status=%s"
            params.append(status_filter)
        sql += " ORDER BY o.ordered_at DESC"
        cur.execute(sql, params)

    all_orders = cur.fetchall()
    cur.close(); conn.close()
    return render_template("orders.html",
        orders=all_orders, status_filter=status_filter,
        role=role, sla_limit=48
    )

@app.route('/orders/<int:oid>')
@login_required
def order_detail(oid):
    uid  = session['user_id']
    role = session.get('role')
    conn = get_db(); cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT o.*, u.username, u.email, u.phone,
               a.line1, a.line2, a.city, a.state, a.pincode,
               au.username AS agent_name, da.vehicle, da.zone
        FROM orders o
        JOIN users u ON o.user_id=u.user_id
        LEFT JOIN addresses a      ON o.address_id=a.address_id
        LEFT JOIN delivery_agents da ON o.agent_id=da.agent_id
        LEFT JOIN users au         ON da.user_id=au.user_id
        WHERE o.order_id=%s
    """, (oid,))
    order = cur.fetchone()

    if not order:
        abort(404)
    if role == 'customer' and order['user_id'] != uid:
        abort(403)

    cur.execute("""
        SELECT oi.quantity, oi.unit_price,
               (oi.quantity * oi.unit_price) AS subtotal,
               p.name, p.image_url, p.slug
        FROM order_items oi JOIN products p ON oi.product_id=p.product_id
        WHERE oi.order_id=%s
    """, (oid,))
    items = cur.fetchall()

    cur.execute("""
        SELECT l.status, l.note, l.updated_at, u.username AS updated_by
        FROM order_status_logs l
        LEFT JOIN users u ON l.updated_by=u.user_id
        WHERE l.order_id=%s ORDER BY l.updated_at ASC
    """, (oid,))
    logs = cur.fetchall()

    agents = []
    if role == 'admin':
        cur.execute("""
            SELECT da.agent_id, u.username, da.zone, da.vehicle
            FROM delivery_agents da JOIN users u ON da.user_id=u.user_id
            WHERE da.is_active=1
        """)
        agents = cur.fetchall()

    cur.close(); conn.close()

    STATUS_ORDER = ['Pending','Processing','Shipped','Out_for_Delivery','Delivered']
    current_idx  = STATUS_ORDER.index(order['status']) if order['status'] in STATUS_ORDER else 0

    return render_template("order_detail.html",
        order=order, items=items, logs=logs, agents=agents,
        STATUS_ORDER=STATUS_ORDER, current_idx=current_idx
    )

# ─── Admin: update order status ──────────────────────────
@app.route('/orders/<int:oid>/update', methods=['POST'])
@login_required
@admin_required
def update_order(oid):
    new_status = request.form.get('status')
    agent_id   = request.form.get('agent_id') or None
    note       = request.form.get('note','').strip()
    valid = ['Pending','Processing','Shipped','Out_for_Delivery','Delivered','Cancelled']
    if new_status not in valid:
        flash("Invalid status.", "error")
        return redirect(f'/orders/{oid}')

    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, status FROM orders WHERE order_id=%s", (oid,))
    order = cur.fetchone()
    if not order:
        abort(404)

    updates = {"status": new_status}
    if agent_id:
        updates["agent_id"] = int(agent_id)
    if new_status == 'Delivered':
        updates["delivered_at"] = datetime.now()

    set_clause = ", ".join(f"{k}=%s" for k in updates)
    cur2 = conn.cursor()
    cur2.execute(f"UPDATE orders SET {set_clause} WHERE order_id=%s",
                 list(updates.values()) + [oid])
    conn.commit()
    cur2.close()

    log_status(oid, new_status, note or f'Status updated to {new_status}', session['user_id'])

    emoji = {'Pending':'⏳','Processing':'🔄','Shipped':'📦',
             'Out_for_Delivery':'🚚','Delivered':'✅','Cancelled':'❌'}.get(new_status,'')
    notify(order['user_id'], f"Order #{oid} is now {new_status} {emoji}", "success")

    cur.close(); conn.close()
    flash(f"Order #{oid} updated to {new_status}.", "success")
    return redirect(f'/orders/{oid}')

# ─── Delivery agent: update status ───────────────────────
@app.route('/agent/update/<int:oid>', methods=['POST'])
@login_required
@agent_required
def agent_update_order(oid):
    new_status = request.form.get('status')
    allowed    = ['Shipped', 'Out_for_Delivery', 'Delivered']
    if new_status not in allowed:
        flash("You can only set Shipped / Out for Delivery / Delivered.", "error")
        return redirect('/agent/dashboard')

    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id FROM orders WHERE order_id=%s", (oid,))
    order = cur.fetchone()
    updates = {"status": new_status}
    if new_status == 'Delivered':
        updates["delivered_at"] = datetime.now()
    set_clause = ", ".join(f"{k}=%s" for k in updates)
    cur2 = conn.cursor()
    cur2.execute(f"UPDATE orders SET {set_clause} WHERE order_id=%s",
                 list(updates.values()) + [oid])
    conn.commit(); cur2.close()
    log_status(oid, new_status, f'Updated by agent', session['user_id'])
    if order:
        notify(order['user_id'], f"Order #{oid} → {new_status} 🚚", "success")
    cur.close(); conn.close()
    flash(f"Order #{oid} → {new_status}", "success")
    return redirect('/agent/dashboard')

# ═══════════════════════════════════════════════════════════
#  REVIEWS
# ═══════════════════════════════════════════════════════════
@app.route('/product/<int:pid>/review', methods=['POST'])
@login_required
def submit_review(pid):
    uid     = session['user_id']
    rating  = int(request.form['rating'])
    comment = request.form.get('comment','').strip()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO reviews (user_id,product_id,rating,comment)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE rating=%s, comment=%s
        """, (uid, pid, rating, comment, rating, comment))
        conn.commit()
        flash("Review submitted! ⭐", "success")
    except Exception:
        flash("Could not submit review.", "error")
    finally:
        cur.close(); conn.close()
    return redirect(request.referrer or '/')

# ═══════════════════════════════════════════════════════════
#  ADDRESSES
# ═══════════════════════════════════════════════════════════
@app.route('/addresses')
@login_required
def addresses():
    uid  = session['user_id']
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM addresses WHERE user_id=%s ORDER BY is_default DESC", (uid,))
    addrs = cur.fetchall()
    cur.close(); conn.close()
    return render_template("addresses.html", addresses=addrs)

@app.route('/addresses/add', methods=['POST'])
@login_required
def add_address():
    uid = session['user_id']
    data = {
        'label':  request.form.get('label','Home').strip(),
        'line1':  request.form['line1'].strip(),
        'line2':  request.form.get('line2','').strip() or None,
        'city':   request.form['city'].strip(),
        'state':  request.form.get('state','').strip() or None,
        'pincode':request.form['pincode'].strip(),
        'is_default': 1 if request.form.get('is_default') else 0
    }
    conn = get_db(); cur = conn.cursor()
    if data['is_default']:
        cur.execute("UPDATE addresses SET is_default=0 WHERE user_id=%s", (uid,))
    cur.execute("""
        INSERT INTO addresses (user_id,label,line1,line2,city,state,pincode,is_default)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (uid, data['label'], data['line1'], data['line2'],
          data['city'], data['state'], data['pincode'], data['is_default']))
    conn.commit(); cur.close(); conn.close()
    flash("Address saved!", "success")
    return redirect('/addresses')

@app.route('/addresses/delete/<int:aid>')
@login_required
def delete_address(aid):
    uid = session['user_id']
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM addresses WHERE address_id=%s AND user_id=%s", (aid, uid))
    conn.commit(); cur.close(); conn.close()
    return redirect('/addresses')

# ═══════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ═══════════════════════════════════════════════════════════
@app.route('/notifications')
@login_required
def notifications():
    uid  = session['user_id']
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", (uid,))
    conn.commit()
    cur.execute("""
        SELECT * FROM notifications WHERE user_id=%s
        ORDER BY created_at DESC LIMIT 50
    """, (uid,))
    notifs = cur.fetchall()
    cur.close(); conn.close()
    return render_template("notifications.html", notifications=notifs)

@app.route('/api/notifications/count')
@login_required
def notif_count():
    return jsonify(count=unread_count(session['user_id']))

# ═══════════════════════════════════════════════════════════
#  INVOICE
# ═══════════════════════════════════════════════════════════
@app.route('/invoice/<int:oid>')
@login_required
def invoice(oid):
    uid  = session['user_id']
    role = session.get('role')
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.*, u.username, u.email, u.phone,
               a.line1, a.line2, a.city, a.state, a.pincode
        FROM orders o
        JOIN users u ON o.user_id=u.user_id
        LEFT JOIN addresses a ON o.address_id=a.address_id
        WHERE o.order_id=%s
    """, (oid,))
    order = cur.fetchone()
    if not order: abort(404)
    if role == 'customer' and order['user_id'] != uid: abort(403)
    cur.execute("""
        SELECT p.name, oi.quantity, oi.unit_price, (oi.quantity*oi.unit_price) AS subtotal
        FROM order_items oi JOIN products p ON oi.product_id=p.product_id
        WHERE oi.order_id=%s
    """, (oid,))
    items = cur.fetchall()
    cur.close(); conn.close()
    return render_template("invoice.html", order=order, items=items)

# ═══════════════════════════════════════════════════════════
#  ADMIN — DASHBOARD
# ═══════════════════════════════════════════════════════════
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    ensure_nature_catalog()
    conn = get_db(); cur = conn.cursor(dictionary=True)

    # KPI cards
    cur.execute("SELECT COUNT(*) AS c FROM orders")
    total_orders = cur.fetchone()['c']

    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS r FROM orders WHERE status='Delivered'")
    revenue = float(cur.fetchone()['r'])

    cur.execute("SELECT COUNT(*) AS c FROM users WHERE role_id=2")
    total_customers = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) AS c FROM orders WHERE status='Pending'")
    pending = cur.fetchone()['c']

    # SLA breaches (pending/processing >48h)
    cur.execute("""
        SELECT COUNT(*) AS c FROM orders
        WHERE status NOT IN ('Delivered','Cancelled')
        AND TIMESTAMPDIFF(HOUR, ordered_at, NOW()) > 48
    """)
    sla_breaches = cur.fetchone()['c']

    # Orders per day (last 7 days)
    cur.execute("""
        SELECT DATE(ordered_at) AS day, COUNT(*) AS cnt,
               COALESCE(SUM(total_amount),0) AS rev
        FROM orders
        WHERE ordered_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(ordered_at) ORDER BY day
    """)
    daily = cur.fetchall()

    # Top products by order count
    cur.execute("""
        SELECT p.name, SUM(oi.quantity) AS sold,
               SUM(oi.quantity * oi.unit_price) AS revenue
        FROM order_items oi JOIN products p ON oi.product_id=p.product_id
        GROUP BY p.product_id ORDER BY sold DESC LIMIT 5
    """)
    top_products = cur.fetchall()

    # Status distribution
    cur.execute("""
        SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status
    """)
    status_dist = cur.fetchall()

    # Avg delivery time (hours)
    cur.execute("""
        SELECT AVG(TIMESTAMPDIFF(HOUR, ordered_at, delivered_at)) AS avg_hrs
        FROM orders WHERE status='Delivered' AND delivered_at IS NOT NULL
    """)
    avg_del = cur.fetchone()['avg_hrs']
    avg_delivery = round(float(avg_del), 1) if avg_del else 0

    # Recent orders
    cur.execute("""
        SELECT o.order_id, u.username, o.total_amount,
               o.status, o.ordered_at
        FROM orders o JOIN users u ON o.user_id=u.user_id
        ORDER BY o.ordered_at DESC LIMIT 8
    """)
    recent_orders = cur.fetchall()

    cur.close(); conn.close()
    return render_template("admin/dashboard.html",
        total_orders=total_orders, revenue=revenue,
        total_customers=total_customers, pending=pending,
        sla_breaches=sla_breaches, avg_delivery=avg_delivery,
        daily=daily, top_products=top_products,
        status_dist=status_dist, recent_orders=recent_orders
    )

# ─── Admin: Products ─────────────────────────────────────
@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    ensure_nature_catalog()
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.name AS category,
               COALESCE(AVG(r.rating),0) AS avg_rating
        FROM products p
        LEFT JOIN categories c ON p.cat_id=c.cat_id
        LEFT JOIN reviews r    ON r.product_id=p.product_id
        WHERE p.is_active=1
        GROUP BY p.product_id ORDER BY p.created_at DESC
    """)
    products = cur.fetchall()
    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin/products.html", products=products, categories=categories)

@app.route('/admin/product/add', methods=['GET','POST'])
@login_required
@admin_required
def admin_add_product():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        import re
        name  = request.form['name'].strip()
        slug  = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        desc  = request.form.get('description','').strip()
        price = request.form['price']
        stock = request.form.get('stock', 0)
        cat   = request.form.get('cat_id') or None
        img   = request.form.get('image_url','').strip() or None
        cur2  = conn.cursor()
        try:
            cur2.execute("""
                INSERT INTO products (cat_id,name,slug,description,price,stock,image_url)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (cat, name, slug, desc, price, stock, img))
            conn.commit()
            flash("Product added!", "success")
            return redirect('/admin/products')
        except mysql.connector.IntegrityError:
            flash("A product with this name/slug already exists.", "error")
        finally:
            cur2.close()
    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin/product_form.html", product=None, categories=categories)

@app.route('/admin/product/edit/<int:pid>', methods=['GET','POST'])
@login_required
@admin_required
def admin_edit_product(pid):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        import re
        name  = request.form['name'].strip()
        slug  = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        desc  = request.form.get('description','').strip()
        price = request.form['price']
        stock = request.form.get('stock', 0)
        cat   = request.form.get('cat_id') or None
        img   = request.form.get('image_url','').strip() or None
        active= 1 if request.form.get('is_active') else 0
        cur2  = conn.cursor()
        cur2.execute("""
            UPDATE products SET cat_id=%s, name=%s, slug=%s, description=%s,
            price=%s, stock=%s, image_url=%s, is_active=%s WHERE product_id=%s
        """, (cat, name, slug, desc, price, stock, img, active, pid))
        conn.commit(); cur2.close()
        flash("Product updated!", "success")
        return redirect('/admin/products')
    cur.execute("SELECT * FROM products WHERE product_id=%s", (pid,))
    product = cur.fetchone()
    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin/product_form.html", product=product, categories=categories)

@app.route('/admin/product/delete/<int:pid>', methods=['POST', 'GET'])
@login_required
@admin_required
def admin_delete_product(pid):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT name FROM products WHERE product_id=%s", (pid,))
    product = cur.fetchone()
    if not product:
        cur.close(); conn.close()
        flash("Product not found.", "error")
        return redirect('/admin/products')
    try:
        cur.execute("DELETE FROM cart WHERE product_id=%s", (pid,))
        cur.execute("DELETE FROM reviews WHERE product_id=%s", (pid,))
        cur.execute("DELETE FROM products WHERE product_id=%s", (pid,))
        conn.commit()
        flash(f"{product['name']} deleted.", "success")
    except mysql.connector.IntegrityError:
        conn.rollback()
        cur.execute("UPDATE products SET is_active=0 WHERE product_id=%s", (pid,))
        conn.commit()
        flash(f"{product['name']} has order history, so it was hidden instead.", "success")
    finally:
        cur.close(); conn.close()
    return redirect('/admin/products')

# ─── Admin: Users ────────────────────────────────────────
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.user_id, u.username, u.email, u.phone, u.is_active, u.created_at,
               r.role_name,
               COUNT(DISTINCT o.order_id) AS order_count
        FROM users u
        JOIN roles r ON u.role_id=r.role_id
        LEFT JOIN orders o ON o.user_id=u.user_id
        GROUP BY u.user_id ORDER BY u.created_at DESC
    """)
    users = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin/users.html", users=users)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == session.get('user_id'):
        flash("You cannot remove your own admin account while logged in.", "error")
        return redirect('/admin/users')

    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.user_id, u.username, r.role_name
        FROM users u JOIN roles r ON u.role_id=r.role_id
        WHERE u.user_id=%s
    """, (user_id,))
    user = cur.fetchone()
    if not user:
        cur.close(); conn.close()
        flash("User not found.", "error")
        return redirect('/admin/users')

    if user['role_name'] == 'admin':
        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role_id=1")
        if cur.fetchone()['c'] <= 1:
            cur.close(); conn.close()
            flash("At least one admin account must remain.", "error")
            return redirect('/admin/users')

    cur.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
    conn.commit()
    cur.close(); conn.close()
    flash(f"User {user['username']} removed.", "success")
    return redirect('/admin/users')

# ─── Admin: Agents ───────────────────────────────────────
@app.route('/admin/agents')
@login_required
@admin_required
def admin_agents():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT da.agent_id, u.username, u.email, u.phone,
               da.vehicle, da.zone, da.is_active,
               COUNT(o.order_id) AS assigned_orders
        FROM delivery_agents da
        JOIN users u ON da.user_id=u.user_id
        LEFT JOIN orders o ON o.agent_id=da.agent_id AND o.status NOT IN ('Delivered','Cancelled')
        GROUP BY da.agent_id
    """)
    agents = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin/agents.html", agents=agents)

# ─── Admin: Analytics ────────────────────────────────────
@app.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    ensure_nature_catalog()
    conn = get_db(); cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT DATE(ordered_at) AS day, COUNT(*) AS orders,
               COALESCE(SUM(total_amount),0) AS revenue
        FROM orders WHERE ordered_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(ordered_at) ORDER BY day
    """)
    daily_30 = cur.fetchall()

    cur.execute("""
        SELECT p.name, c.name AS category,
               SUM(oi.quantity) AS sold,
               SUM(oi.quantity*oi.unit_price) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_id=p.product_id
        LEFT JOIN categories c ON p.cat_id=c.cat_id
        GROUP BY p.product_id ORDER BY sold DESC LIMIT 10
    """)
    top_products = cur.fetchall()

    cur.execute("""
        SELECT c.name AS category, COUNT(oi.item_id) AS orders
        FROM order_items oi
        JOIN products p ON oi.product_id=p.product_id
        JOIN categories c ON p.cat_id=c.cat_id
        GROUP BY c.cat_id ORDER BY orders DESC
    """)
    cat_dist = cur.fetchall()

    cur.execute("""
        SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status
    """)
    status_dist = cur.fetchall()

    cur.execute("""
        SELECT da.agent_id, u.username,
               COUNT(o.order_id) AS total,
               SUM(o.status='Delivered') AS delivered,
               AVG(TIMESTAMPDIFF(HOUR,o.ordered_at,o.delivered_at)) AS avg_hrs
        FROM delivery_agents da
        JOIN users u ON da.user_id=u.user_id
        LEFT JOIN orders o ON o.agent_id=da.agent_id
        GROUP BY da.agent_id
    """)
    agent_perf = cur.fetchall()

    cur.close(); conn.close()
    return render_template("admin/analytics.html",
        daily_30=daily_30, top_products=top_products,
        cat_dist=cat_dist, status_dist=status_dist,
        agent_perf=agent_perf
    )

# ═══════════════════════════════════════════════════════════
#  DELIVERY AGENT DASHBOARD
# ═══════════════════════════════════════════════════════════
@app.route('/agent/dashboard')
@login_required
@agent_required
def agent_dashboard():
    uid  = session['user_id']
    conn = get_db(); cur = conn.cursor(dictionary=True)

    cur.execute("SELECT agent_id FROM delivery_agents WHERE user_id=%s", (uid,))
    row = cur.fetchone()
    if not row:
        flash("Delivery agent profile not found.", "error")
        return redirect('/logout')
    agent_id = row['agent_id']

    cur.execute("""
        SELECT o.order_id, o.status, o.total_amount, o.ordered_at,
               u.username, u.phone,
               a.line1, a.city, a.pincode
        FROM orders o
        JOIN users u ON o.user_id=u.user_id
        LEFT JOIN addresses a ON o.address_id=a.address_id
        WHERE o.agent_id=%s AND o.status NOT IN ('Delivered','Cancelled')
        ORDER BY o.ordered_at
    """, (agent_id,))
    active_orders = cur.fetchall()

    cur.execute("""
        SELECT COUNT(*) AS c FROM orders WHERE agent_id=%s AND status='Delivered'
    """, (agent_id,))
    total_delivered = cur.fetchone()['c']

    cur.close(); conn.close()
    return render_template("agent/dashboard.html",
        active_orders=active_orders, total_delivered=total_delivered
    )

# ═══════════════════════════════════════════════════════════
#  REST API LAYER
# ═══════════════════════════════════════════════════════════
@app.route('/api/auth/me')
def api_auth_me():
    if 'user_id' not in session:
        return jsonify(user=None), 401
    return jsonify(user={
        'user_id': session['user_id'],
        'username': session.get('username'),
        'email': session.get('email'),
        'role': session.get('role')
    })

@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    data = request.get_json() or {}
    identifier = (data.get('username') or data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.user_id, u.username, u.email, u.password, u.is_active, r.role_name
        FROM users u JOIN roles r ON u.role_id=r.role_id
        WHERE LOWER(u.username)=%s OR LOWER(u.email)=%s
    """, (identifier, identifier))
    user = cur.fetchone()
    cur.close(); conn.close()
    if not user or not password_matches(user, password):
        return jsonify(error='Invalid username/email or password'), 401
    if not user['is_active']:
        token = build_token(user['email'], 'verify')
        emit_email(user['email'], 'Verify your OrderSphere account',
                   url_for('verify_email', token=token, _external=True))
        return jsonify(error='Email verification required'), 403
    login_user(user, data.get('remember', False))
    return jsonify(user={
        'user_id': user['user_id'],
        'username': user['username'],
        'email': user['email'],
        'role': user['role_name']
    })

@app.route('/api/auth/signup', methods=['POST'])
def api_auth_signup():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    phone = (data.get('phone') or '').strip() or None
    if not re.match(r'^[A-Za-z0-9_.-]{3,60}$', username):
        return jsonify(error='Invalid username'), 400
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify(error='Invalid email'), 400
    if not password_is_strong(password):
        return jsonify(error='Password must be 8+ characters with uppercase, lowercase, and a number'), 400
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username,email,password,role_id,phone,is_active) VALUES (%s,%s,%s,2,%s,0)",
            (username, email, generate_password_hash(password), phone)
        )
        conn.commit()
        token = build_token(email, 'verify')
        sent = emit_email(email, 'Verify your OrderSphere account',
                          url_for('verify_email', token=token, _external=True))
        return jsonify(message='Account created. Verification email sent.' if sent else
                       'Account created. Gmail delivery is not configured.'), 201
    except mysql.connector.IntegrityError:
        return jsonify(error='Username or email already exists'), 409
    finally:
        cur.close(); conn.close()

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_auth_forgot_password():
    email = ((request.get_json() or {}).get('email') or '').strip().lower()
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT email FROM users WHERE LOWER(email)=%s", (email,))
    user = cur.fetchone()
    cur.close(); conn.close()
    if user:
        token = build_token(user['email'], 'reset')
        emit_email(user['email'], 'Reset your OrderSphere password',
                   url_for('reset_password', token=token, _external=True))
    return jsonify(message='If that email exists, a reset link has been sent.')

@app.route('/api/auth/reset-password/<token>', methods=['POST'])
def api_auth_reset_password(token):
    try:
        data = read_token(token, 'reset', app.config['RESET_TOKEN_MAX_AGE'])
    except SignatureExpired:
        return jsonify(error='Reset token expired'), 400
    except BadSignature:
        return jsonify(error='Invalid reset token'), 400
    password = ((request.get_json() or {}).get('password') or '')
    if not password_is_strong(password):
        return jsonify(error='Password must be 8+ characters with uppercase, lowercase, and a number'), 400
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET password=%s, is_active=1 WHERE LOWER(email)=%s",
                (generate_password_hash(password), data['email']))
    conn.commit()
    cur.close(); conn.close()
    return jsonify(message='Password reset complete')

@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    session.clear()
    return jsonify(message='Logged out')

@app.route('/api/products')
def api_products():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.product_id, p.name, p.slug, p.description, p.price,
               p.stock, p.image_url, c.name AS category,
               COALESCE(AVG(r.rating),0) AS rating
        FROM products p
        LEFT JOIN categories c ON p.cat_id=c.cat_id
        LEFT JOIN reviews r    ON r.product_id=p.product_id
        WHERE p.is_active=1 GROUP BY p.product_id
    """)
    products = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(products=[row_to_json(p) for p in products])

@app.route('/api/orders', methods=['GET'])
@login_required
def api_orders():
    uid  = session['user_id']
    role = session.get('role')
    conn = get_db(); cur = conn.cursor(dictionary=True)
    if role == 'admin':
        cur.execute("SELECT * FROM orders ORDER BY ordered_at DESC LIMIT 100")
    else:
        cur.execute("SELECT * FROM orders WHERE user_id=%s ORDER BY ordered_at DESC", (uid,))
    orders = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(orders=[row_to_json(o) for o in orders])

@app.route('/api/order', methods=['POST'])
@login_required
def api_place_order():
    data       = request.get_json() or {}
    uid        = session['user_id']
    product_id = data.get('product_id')
    quantity   = data.get('quantity', 1)
    if not product_id:
        return jsonify(error="product_id required"), 400
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM products WHERE product_id=%s AND is_active=1", (product_id,))
    product = cur.fetchone()
    if not product:
        return jsonify(error="Product not found"), 404
    if product['stock'] < quantity:
        return jsonify(error="Insufficient stock"), 400
    cur2 = conn.cursor()
    cur2.execute("INSERT INTO orders (user_id,status,total_amount) VALUES (%s,'Pending',%s)",
                 (uid, float(product['price']) * quantity))
    conn.commit()
    oid = cur2.lastrowid
    cur2.execute("INSERT INTO order_items (order_id,product_id,quantity,unit_price) VALUES (%s,%s,%s,%s)",
                 (oid, product_id, quantity, product['price']))
    cur2.execute("UPDATE products SET stock=stock-%s WHERE product_id=%s", (quantity, product_id))
    conn.commit()
    log_status(oid, 'Pending', 'API order', uid)
    cur2.close(); cur.close(); conn.close()
    return jsonify(order_id=oid, status='Pending', total=float(product['price'])*quantity), 201

@app.route('/api/analytics')
@login_required
@admin_required
def api_analytics():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total_orders FROM orders")
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS revenue FROM orders WHERE status='Delivered'")
    r = cur.fetchone()
    cur.close(); conn.close()
    return jsonify(revenue=float(r['revenue']))

# ═══════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════
@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode, threaded=True)   # threaded=True → handles concurrent users
