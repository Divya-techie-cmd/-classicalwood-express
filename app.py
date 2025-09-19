# app.py
from flask import Flask, g, render_template_string, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

DATABASE = 'store.db'
SECRET_KEY = 'dev-secret-key-change-this'  # change in production

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

##### ---------- Database helpers ---------- #####
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    cur = get_db().execute(query, args)
    get_db().commit()
    lastrowid = cur.lastrowid
    cur.close()
    return lastrowid

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

##### ---------- DB initialization & seed ---------- #####
def init_db():
    if os.path.exists(DATABASE):
        return
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()

    # Users
    cur.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT
    )''')

    # Products
    cur.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        price REAL,
        image_url TEXT,
        created_at TEXT
    )''')

    # Orders
    cur.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        items TEXT, -- JSON string of items [{id, title, qty, price}, ...]
        total REAL,
        address TEXT,
        phone TEXT,
        method TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # Wishlist
    cur.execute('''
    CREATE TABLE wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        created_at TEXT,
        UNIQUE(user_id, product_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')

    # Reviews
    cur.execute('''
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_name TEXT,
        rating INTEGER,
        comment TEXT,
        created_at TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')

    db.commit()

    # Seed admin user and sample products
    password_hash = generate_password_hash('adminpass')
    cur.execute('INSERT INTO users (name, email, password, is_admin, created_at) VALUES (?, ?, ?, ?, ?)',
                ('Admin', 'admin@classicalwood.com', password_hash, 1, datetime.utcnow().isoformat()))

    sample_products = [
        {
            "title":"Mahogany Carved Armchair",
            "description":"Hand-carved mahogany armchair with plush leather seating — classic craftsmanship for a premium living room.",
            "category":"Chairs",
            "price":24999.00,
            "image":"https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=1000&q=80"
        },
        {
            "title":"Oak Dining Table (6 seater)",
            "description":"Solid oak dining table with natural grain finish. Seats 6 comfortably and ages beautifully.",
            "category":"Tables",
            "price":39999.00,
            "image":"https://images.unsplash.com/photo-1550583724-b2696b5a35b7?auto=format&fit=crop&w=1000&q=80"
        },
        {
            "title":"Walnut Bookshelf - 4 Tier",
            "description":"Modular walnut bookshelf with adjustable shelves — perfect for modern studies and living spaces.",
            "category":"Shelves",
            "price":17999.00,
            "image":"https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80"
        },
        {
            "title":"Solid Teak Bed (Queen)",
            "description":"Robust teak bed frame with elegant headboard — long-lasting and timeless.",
            "category":"Beds",
            "price":45999.00,
            "image":"https://images.unsplash.com/photo-1583511655896-947c5e0c6f7e?auto=format&fit=crop&w=1000&q=80"
        },
        {
            "title":"Reclaimed Wood Coffee Table",
            "description":"Eco reclaimed wood coffee table with brass accents — rustic yet refined.",
            "category":"Tables",
            "price":12999.00,
            "image":"https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=1000&q=80"
        },
        {
            "title":"Midcentury Accent Chair",
            "description":"Velvet upholstered accent chair with walnut legs — midcentury vibe for modern homes.",
            "category":"Chairs",
            "price":15999.00,
            "image":"https://images.unsplash.com/photo-1549187774-b4e9b0445b1e?auto=format&fit=crop&w=1000&q=80"
        }
    ]

    for p in sample_products:
        cur.execute('INSERT INTO products (title, description, category, price, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (p['title'], p['description'], p['category'], p['price'], p['image'], datetime.utcnow().isoformat()))
    db.commit()
    db.close()

# ensure DB created on first run
init_db()

##### ---------- Utility helpers ---------- #####
import json
def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    user = query_db('SELECT id, name, email, is_admin FROM users WHERE id=?', (uid,), one=True)
    return user

def cart_get():
    return session.get('cart', {})

def cart_save(cart):
    session['cart'] = cart
    session.modified = True

##### ---------- Routes ---------- #####

# --- Home ---
@app.route('/')
def home():
    featured = query_db('SELECT * FROM products ORDER BY id DESC LIMIT 6')
    categories = query_db('SELECT DISTINCT category FROM products')
    return render_template_string(BASE_TEMPLATE, page='home', featured=featured, categories=categories, user=current_user())

# --- Shop ---
@app.route('/shop')
def shop():
    q = request.args.get('q', '').strip()
    cat = request.args.get('category', '')
    if q:
        products = query_db("SELECT * FROM products WHERE title LIKE ? OR description LIKE ? OR category LIKE ?",
                            (f'%{q}%', f'%{q}%', f'%{q}%'))
    elif cat:
        products = query_db("SELECT * FROM products WHERE category = ?", (cat,))
    else:
        products = query_db("SELECT * FROM products")
    categories = query_db('SELECT DISTINCT category FROM products')
    return render_template_string(BASE_TEMPLATE, page='shop', products=products, categories=categories, q=q, user=current_user())

# --- Product detail ---
@app.route('/product/<int:pid>', methods=['GET'])
def product_detail(pid):
    product = query_db('SELECT * FROM products WHERE id=?', (pid,), one=True)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('shop'))
    reviews = query_db('SELECT * FROM reviews WHERE product_id=? ORDER BY created_at DESC', (pid,))
    return render_template_string(BASE_TEMPLATE, page='product', product=product, reviews=reviews, user=current_user())

# --- Add review ---
@app.route('/review/add/<int:pid>', methods=['POST'])
def add_review(pid):
    name = request.form.get('name') or 'Guest'
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '')
    execute_db('INSERT INTO reviews (product_id, user_name, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)',
               (pid, name, rating, comment, datetime.utcnow().isoformat()))
    flash('Review added — thank you!', 'success')
    return redirect(url_for('product_detail', pid=pid))

# --- Signup/Login/Logout ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        if not name or not email or not password:
            flash('Fill all fields', 'danger')
            return redirect(url_for('signup'))
        existing = query_db('SELECT id FROM users WHERE email=?', (email,), one=True)
        if existing:
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        pw_hash = generate_password_hash(password)
        uid = execute_db('INSERT INTO users (name, email, password, is_admin, created_at) VALUES (?, ?, ?, ?, ?)',
                         (name, email, pw_hash, 0, datetime.utcnow().isoformat()))
        session['user_id'] = uid
        flash('Welcome! Account created.', 'success')
        return redirect(url_for('home'))
    return render_template_string(BASE_TEMPLATE, page='signup', user=current_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        user = query_db('SELECT * FROM users WHERE email=?', (email,), one=True)
        if not user or not check_password_hash(user['password'], password):
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
        session['user_id'] = user['id']
        flash('Logged in successfully', 'success')
        return redirect(url_for('home'))
    return render_template_string(BASE_TEMPLATE, page='login', user=current_user())

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out', 'info')
    return redirect(url_for('home'))

# --- Wishlist ---
@app.route('/wishlist')
def wishlist():
    user = current_user()
    if not user:
        flash('Please login to view wishlist', 'warning')
        return redirect(url_for('login'))
    items = query_db('''
        SELECT p.* FROM products p
        JOIN wishlist w ON p.id = w.product_id
        WHERE w.user_id = ?
        ''', (user['id'],))
    return render_template_string(BASE_TEMPLATE, page='wishlist', items=items, user=user)

@app.route('/wishlist/toggle/<int:pid>')
def wishlist_toggle(pid):
    user = current_user()
    if not user:
        flash('Please login to modify wishlist', 'warning')
        return redirect(url_for('login'))
    exists = query_db('SELECT id FROM wishlist WHERE user_id=? AND product_id=?', (user['id'], pid), one=True)
    if exists:
        execute_db('DELETE FROM wishlist WHERE id=?', (exists['id'],))
        flash('Removed from wishlist', 'info')
    else:
        try:
            execute_db('INSERT INTO wishlist (user_id, product_id, created_at) VALUES (?, ?, ?)', (user['id'], pid, datetime.utcnow().isoformat()))
            flash('Added to wishlist', 'success')
        except:
            flash('Already in wishlist', 'info')
    return redirect(request.referrer or url_for('product_detail', pid=pid))

# --- Cart operations (session-based) ---
@app.route('/cart')
def cart():
    cart = cart_get()
    products = []
    total = 0.0
    if cart:
        ids = ','.join(map(str, cart.keys()))
        rows = query_db(f"SELECT * FROM products WHERE id IN ({ids})") if ids else []
        for r in rows:
            pid = str(r['id'])
            qty = cart.get(pid, 0)
            subtotal = r['price'] * qty
            products.append({'product': r, 'qty': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template_string(BASE_TEMPLATE, page='cart', items=products, total=total, user=current_user())

@app.route('/cart/add/<int:pid>', methods=['POST', 'GET'])
def cart_add(pid):
    qty = int(request.form.get('qty', 1)) if request.method == 'POST' else 1
    cart = cart_get()
    pid_s = str(pid)
    cart[pid_s] = cart.get(pid_s, 0) + qty
    cart_save(cart)
    flash('Added to cart', 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update', methods=['POST'])
def cart_update():
    cart = {}
    for k, v in request.form.items():
        if k.startswith('qty_'):
            pid = k.split('_', 1)[1]
            try:
                q = int(v)
            except:
                q = 0
            if q > 0:
                cart[pid] = q
    cart_save(cart)
    flash('Cart updated', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:pid>')
def cart_remove(pid):
    cart = cart_get()
    pid_s = str(pid)
    if pid_s in cart:
        cart.pop(pid_s)
        cart_save(cart)
        flash('Item removed', 'info')
    return redirect(url_for('cart'))

# --- Checkout (Cash on Delivery only) ---
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user = current_user()
    cart = cart_get()
    if not cart:
        flash('Cart is empty', 'warning')
        return redirect(url_for('shop'))
    # prepare items
    ids = ','.join(map(str, cart.keys()))
    rows = query_db(f"SELECT * FROM products WHERE id IN ({ids})") if ids else []
    items = []
    total = 0.0
    for r in rows:
        pid = str(r['id'])
        qty = cart.get(pid, 0)
        items.append({'id': r['id'], 'title': r['title'], 'price': r['price'], 'qty': qty})
        total += r['price'] * qty

    if request.method == 'POST':
        name = request.form.get('name') or (user['name'] if user else 'Guest')
        phone = request.form.get('phone')
        address = request.form.get('address')
        method = request.form.get('method', 'Cash on Delivery')
        uid = user['id'] if user else None
        execute_db('INSERT INTO orders (user_id, items, total, address, phone, method, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (uid, json.dumps(items), total, address, phone, method, 'Placed', datetime.utcnow().isoformat()))
        # clear cart
        session.pop('cart', None)
        flash('Order placed — Cash on Delivery selected. Thank you!', 'success')
        return redirect(url_for('orders'))
    return render_template_string(BASE_TEMPLATE, page='checkout', items=items, total=total, user=user)

# --- Orders page ---
@app.route('/orders')
def orders():
    user = current_user()
    if not user:
        flash('Please login to view orders', 'warning')
        return redirect(url_for('login'))
    rows = query_db('SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC', (user['id'],))
    # parse items JSON
    orders = []
    for r in rows:
        orders.append(dict(r))
        try:
            orders[-1]['items'] = json.loads(r['items'])
        except:
            orders[-1]['items'] = []
    return render_template_string(BASE_TEMPLATE, page='orders', orders=orders, user=user)

# --- Contact ---
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Message received. We will contact you shortly.', 'success')
        return redirect(url_for('contact'))
    return render_template_string(BASE_TEMPLATE, page='contact', user=current_user())

# --- Admin: list products & manage ---
def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*a, **kw):
        u = current_user()
        if not u or u['is_admin'] != 1:
            flash('Admin access required', 'danger')
            return redirect(url_for('login'))
        return fn(*a, **kw)
    return wrapper

@app.route('/admin')
@admin_required
def admin_panel():
    products = query_db('SELECT * FROM products ORDER BY id DESC')
    return render_template_string(BASE_TEMPLATE, page='admin', products=products, user=current_user())

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add():
    if request.method == 'POST':
        title = request.form.get('title')
        desc = request.form.get('description')
        cat = request.form.get('category')
        price = float(request.form.get('price') or 0)
        image = request.form.get('image_url') or 'https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=1000&q=80'
        execute_db('INSERT INTO products (title, description, category, price, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                   (title, desc, cat, price, image, datetime.utcnow().isoformat()))
        flash('Product added', 'success')
        return redirect(url_for('admin_panel'))
    return render_template_string(BASE_TEMPLATE, page='admin_add', user=current_user())

@app.route('/admin/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def admin_edit(pid):
    product = query_db('SELECT * FROM products WHERE id=?', (pid,), one=True)
    if not product:
        flash('Product missing', 'danger')
        return redirect(url_for('admin_panel'))
    if request.method == 'POST':
        title = request.form.get('title')
        desc = request.form.get('description')
        cat = request.form.get('category')
        price = float(request.form.get('price') or 0)
        image = request.form.get('image_url')
        execute_db('UPDATE products SET title=?, description=?, category=?, price=?, image_url=? WHERE id=?',
                   (title, desc, cat, price, image, pid))
        flash('Product updated', 'success')
        return redirect(url_for('admin_panel'))
    return render_template_string(BASE_TEMPLATE, page='admin_edit', product=product, user=current_user())

@app.route('/admin/delete/<int:pid>')
@admin_required
def admin_delete(pid):
    execute_db('DELETE FROM products WHERE id=?', (pid,))
    flash('Product deleted', 'info')
    return redirect(url_for('admin_panel'))

# --- Simple FAQ chatbot API (static answers) ---
FAQ_ANSWERS = {
    "shipping": "We offer free standard shipping across most cities. Premium/express delivery charges apply based on distance.",
    "delivery time": "Delivery typically takes 5-10 business days depending on your location and product availability.",
    "returns": "We accept returns within 7 days of delivery for damaged/defective items. Custom furniture may be non-returnable.",
    "payment": "We support Cash on Delivery. Online payments will be added soon.",
    "contact": "You can reach us at support@classicalwood.com or WhatsApp us via the contact page."
}

@app.route('/faq/chat', methods=['POST'])
def faq_chat():
    q = (request.json.get('q') or '').lower()
    # very simple keyword match
    for k in FAQ_ANSWERS:
        if k in q:
            return jsonify({"answer": FAQ_ANSWERS[k]})
    return jsonify({"answer": "Sorry — I don't understand. Try 'shipping', 'delivery time', 'returns', 'payment', or 'contact'."})

##### ---------- Base Template (inline templates block) ---------- #####
# We'll use a single base template variable and render different "pages" via 'page' variable.
BASE_TEMPLATE = """
{% macro nav_links(user) -%}
<nav class="navbar navbar-expand-lg navbar-dark" style="background: linear-gradient(90deg,#5a2a10, #3e1c0b);">
  <div class="container">
    <a class="navbar-brand d-flex align-items-center" href="{{ url_for('home') }}">
      <div style="width:44px;height:44px;border-radius:8px;background:linear-gradient(135deg,#7b3b1b,#3d1b07);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;margin-right:8px;">
        C
      </div>
      <div>
        <div style="font-weight:700">Classical Wood Express</div>
        <small style="font-size:11px;color:#f6e6d9">crafted wood · delivered quickly </small>
      </div>
    </a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu"><span class="navbar-toggler-icon"></span></button>
    <div class="collapse navbar-collapse" id="navMenu">
      <ul class="navbar-nav ms-auto align-items-lg-center">
        <li class="nav-item"><a class="nav-link" href="{{ url_for('shop') }}">Shop</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('wishlist') }}">Wishlist</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('orders') }}">Orders</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('contact') }}">Contact</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('cart') }}">Cart</a></li>
        {% if user %}
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">{{ user['name'] }}</a>
            <ul class="dropdown-menu dropdown-menu-end">
              {% if user['is_admin'] == 1 %}
              <li><a class="dropdown-item" href="{{ url_for('admin_panel') }}">Admin Panel</a></li>
              {% endif %}
              <li><a class="dropdown-item" href="{{ url_for('logout') }}">Logout</a></li>
            </ul>
          </li>
        {% else %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('login') }}">Login</a></li>
          <li class="nav-item"><a class="nav-link btn btn-outline-warning ms-2" href="{{ url_for('signup') }}" style="border-radius:20px;padding:6px 14px">Signup</a></li>
        {% endif %}
      </ul>
    </div>
  </div>
</nav>
{%- endmacro %}

<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Classical Wood Express</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Bootstrap 5 CDN -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root{
      --mahogany:#6b2f16;
      --oak:#a1704a;
      --walnut:#5b3a2a;
      --beige:#f5e9dd;
      --gold:#d4a55d;
      --darkwood: #2e1a12;
    }
    body{ background: linear-gradient(180deg,var(--beige), #fff); color:#2b2b2b; }
    .hero {
      min-height: 60vh;
      background-image: url('https://images.unsplash.com/photo-1505691723518-36aee6e98b8f?auto=format&fit=crop&w=1600&q=80');
      background-attachment: fixed;
      background-size: cover;
      background-position: center;
      position: relative;
      display:flex; align-items:center;
      color:white;
    }
    .hero::after {
      content:""; position:absolute; inset:0;
      background: linear-gradient(180deg, rgba(45,20,10,0.25), rgba(15,10,7,0.6));
    }
    .hero .container{ position:relative; z-index:2;}
    .card-3d { transform-style: preserve-3d; transition: transform 0.35s ease, box-shadow 0.35s ease; will-change: transform; }
    .card-3d:hover { box-shadow: 0 20px 35px rgba(0,0,0,0.2); transform: translateY(-8px) rotateX(4deg) rotateY(6deg) scale(1.02); }
    .btn-3d {
      border-radius:10px; padding:12px 20px; font-weight:600;
      box-shadow: 0 6px 0 rgba(0,0,0,0.12), inset 0 -6px 0 rgba(0,0,0,0.04);
      transform: translateZ(0); transition: transform 0.12s ease;
      background: linear-gradient(180deg,var(--gold), #c78f3f);
      color:#2b170b; border:none;
    }
    .btn-3d:active { transform: translateY(4px); box-shadow:none; }
    .product-img-3d { transform: perspective(900px) rotateX(0deg) rotateY(0deg); transition: transform 0.2s; }
    .parallax-layer { transform: translateZ(-1px) scale(1.1); }
    .footer {
      background: linear-gradient(90deg,var(--darkwood), #1f120a);
      color: #e7d9cc; padding:40px 0;
    }
    .faq-bubble {
      position: fixed; right: 24px; bottom: 24px; z-index: 2000;
    }
    .faq-bubble .bubble {
      width:68px; height:68px; border-radius:50%; background: linear-gradient(135deg,var(--gold), #c78f3f);
      display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;cursor:pointer;
      box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }
    .chat-popup {
      position: fixed; right: 24px; bottom: 100px; width: 360px; max-width: 92vw; z-index:2001;
      background: linear-gradient(180deg, #fff, #fcf7f2); border-radius:16px; box-shadow: 0 20px 50px rgba(0,0,0,0.25);
      display:none; overflow:hidden;
    }
    .chat-head { background: linear-gradient(90deg,var(--mahogany),var(--walnut)); color:#fff; padding:12px 16px; }
    .chat-body { max-height:320px; overflow:auto; padding:12px; font-size:14px; }
    .chat-input { padding:10px; display:flex; gap:8px; border-top:1px solid #eee; }
    .wood-badge { background:linear-gradient(90deg,var(--oak),var(--mahogany)); color:#fff; padding:6px 10px; border-radius:8px; font-weight:700; }
    .tilt { transform-style: preserve-3d; transition: transform 0.12s ease; }
    .testimonial { background: linear-gradient(90deg, rgba(255,255,255,0.6), rgba(255,255,255,0.2)); border-radius:12px; padding:18px; }
    .product-grid .card { border:none; border-radius:14px; overflow:hidden; }
    .contact-map { width:100%; height:250px; border-radius:12px; border:0; }
  </style>
</head>
<body>
  {{ nav_links(user) }}

  <div class="container my-4">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="mt-2">
          {% for cat, msg in messages %}
            <div class="alert alert-{{ 'warning' if cat=='warning' else ('success' if cat=='success' else ('danger' if cat=='danger' else 'info')) }} alert-dismissible fade show" role="alert">
              {{ msg }} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
  </div>

  {# ------------------- HOME ------------------- #}
  {% if page=='home' %}
    <section class="hero mb-5">
      <div class="container">
        <div class="row align-items-center">
          <div class="col-md-7 text-white">
            <h1 class="display-5 fw-bold">Crafted Wood. Delivered Quickly.</h1>
            <p class="lead">Premium wooden furniture — mahogany, oak, walnut — handcrafted for timeless homes. Explore our curated collections.</p>
            <a href="{{ url_for('shop') }}" class="btn btn-3d btn-lg">Shop Now</a>
          </div>
          <div class="col-md-5 d-none d-md-block">
            <div class="card card-3d p-3" style="border-radius:14px;background:linear-gradient(180deg,rgba(255,255,255,0.85), #fff);">
              <img src="https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80" alt="showcase" class="img-fluid product-img-3d" />
              <div class="mt-3">
                <h5 class="mb-0">Featured: Reclaimed Coffee Table</h5>
                <small class="text-muted">Rustic · Eco · Hand-finished</small>
                <div class="mt-2">
                  <a href="{{ url_for('shop') }}" class="btn btn-outline-dark btn-sm">Explore collection</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="container mb-5">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3 class="mb-0">Featured Categories</h3>
        <a href="{{ url_for('shop') }}" class="text-muted">View all</a>
      </div>
      <div class="row gy-3">
        {% for c in categories %}
        <div class="col-sm-6 col-md-3">
          <div class="p-3 tilt testimonial" style="min-height:120px;">
            <h5>{{ c['category'] }}</h5>
            <p class="mb-0 small text-muted">Curated selection of {{ c['category']|lower }}</p>
          </div>
        </div>
        {% endfor %}
      </div>
    </section>

    <section class="container mb-5">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3 class="mb-0">3D Product Showcase</h3>
        <small class="text-muted">Hover to interact</small>
      </div>
      <div class="row product-grid g-3">
        {% for p in featured %}
        <div class="col-12 col-md-4 col-lg-2">
          <div class="card card-3d p-2">
            <div onmousemove="tilt(event,this)" onmouseleave="tiltReset(this)" style="overflow:hidden;border-radius:12px;">
              <a href="{{ url_for('product_detail', pid=p['id']) }}">
                <img src="{{ p['image_url'] }}" class="img-fluid product-img-3d" style="height:180px;width:100%;object-fit:cover;" />
              </a>
            </div>
            <div class="p-2">
              <h6 class="mb-1">{{ p['title']|truncate(26) }}</h6>
              <div class="d-flex justify-content-between align-items-center">
                <strong>₹{{ '%.0f' % p['price'] }}</strong>
                <a href="{{ url_for('product_detail', pid=p['id']) }}" class="btn btn-sm btn-outline-secondary">View</a>
              </div>
            </div>
          </div>
        </div>
        {% endfor %}
      </div>
    </section>

  {% elif page=='shop' %}
    <section class="container">
      <div class="row mb-3 align-items-center">
        <div class="col-md-6">
          <h3>Shop</h3>
          <p class="text-muted">High-quality wooden furniture — filter, search, and discover.</p>
        </div>
        <div class="col-md-6">
          <form method="get" class="d-flex">
            <input class="form-control me-2" name="q" placeholder="Search products..." value="{{ q or '' }}">
            <select name="category" class="form-select me-2" onchange="this.form.submit()">
              <option value="">All categories</option>
              {% for c in categories %}
                <option value="{{ c['category'] }}" {% if c['category']==request.args.get('category') %}selected{% endif %}>{{ c['category'] }}</option>
              {% endfor %}
            </select>
            <button class="btn btn-3d" type="submit">Search</button>
          </form>
        </div>
      </div>

      <div class="row g-3 product-grid">
        {% for p in products %}
        <div class="col-6 col-md-4 col-lg-3">
          <div class="card card-3d h-100">
            <div onmousemove="tilt(event,this)" onmouseleave="tiltReset(this)" style="overflow:hidden;">
              <img src="{{ p['image_url'] }}" class="img-fluid" style="height:200px;width:100%;object-fit:cover;" />
            </div>
            <div class="card-body">
              <h6>{{ p['title'] }}</h6>
              <p class="small text-muted mb-2">{{ p['category'] }}</p>
              <div class="d-flex justify-content-between align-items-center">
                <strong>₹{{ '%.0f' % p['price'] }}</strong>
                <div>
                  <a href="{{ url_for('cart_add', pid=p['id']) }}" class="btn btn-sm btn-outline-success">Add</a>
                  <a href="{{ url_for('product_detail', pid=p['id']) }}" class="btn btn-sm btn-outline-secondary">Details</a>
                </div>
              </div>
            </div>
          </div>
        </div>
        {% endfor %}
      </div>
    </section>

  {% elif page=='product' %}
    <section class="container">
      <div class="row g-4">
        <div class="col-md-6">
          <div class="card card-3d p-2">
            <div onmousemove="tilt(event,this)" onmouseleave="tiltReset(this)" style="overflow:hidden;border-radius:12px;">
              <img src="{{ product['image_url'] }}" class="img-fluid product-img-3d" style="height:420px;width:100%;object-fit:cover;" />
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <h3>{{ product['title'] }}</h3>
          <p class="text-muted">{{ product['category'] }}</p>
          <h4 class="text-dark">₹{{ '%.0f' % product['price'] }}</h4>
          <p>{{ product['description'] }}</p>
          <div class="d-flex gap-2">
            <form method="post" action="{{ url_for('cart_add', pid=product['id']) }}">
              <input type="hidden" name="qty" value="1" />
              <button class="btn btn-3d">Add to Cart</button>
            </form>
            <a href="{{ url_for('wishlist_toggle', pid=product['id']) }}" class="btn btn-outline-secondary">Wishlist</a>
          </div>

          <hr class="my-4">
          <h5>Reviews</h5>
          <div>
            {% for r in reviews %}
              <div class="mb-2">
                <strong>{{ r['user_name'] }}</strong> · <small class="text-muted">{{ r['created_at'][:10] }}</small>
                <div>Rating: {{ r['rating'] }} / 5</div>
                <p>{{ r['comment'] }}</p>
              </div>
            {% else %}
              <p class="text-muted">No reviews yet — be the first to review!</p>
            {% endfor %}
          </div>

          <form action="{{ url_for('add_review', pid=product['id']) }}" method="post" class="mt-3">
            <div class="mb-2">
              <input name="name" class="form-control" placeholder="Your name" />
            </div>
            <div class="mb-2 d-flex gap-2">
              <select name="rating" class="form-select w-25">
                {% for i in range(5,0,-1) %}<option value="{{ i }}">{{ i }}</option>{% endfor %}
              </select>
              <input name="comment" class="form-control" placeholder="Your review" />
            </div>
            <button class="btn btn-outline-dark btn-sm">Submit review</button>
          </form>
        </div>
      </div>
    </section>

  {% elif page=='cart' %}
    <section class="container">
      <h3>Your Cart</h3>
      {% if items %}
        <form method="post" action="{{ url_for('cart_update') }}">
        <table class="table">
          <thead><tr><th>Product</th><th>Qty</th><th>Price</th><th>Subtotal</th><th></th></tr></thead>
          <tbody>
            {% for it in items %}
              <tr>
                <td>
                  <div><strong>{{ it['product']['title'] }}</strong></div>
                </td>
                <td style="width:120px;">
                  <input type="number" name="qty_{{ it['product']['id'] }}" value="{{ it['qty'] }}" min="0" class="form-control" />
                </td>
                <td>₹{{ '%.0f' % it['product']['price'] }}</td>
                <td>₹{{ '%.0f' % it['subtotal'] }}</td>
                <td><a href="{{ url_for('cart_remove', pid=it['product']['id']) }}" class="btn btn-sm btn-outline-danger">Remove</a></td>
              </tr>
            {% endfor %}
          </tbody>
        </table>

        <div class="d-flex justify-content-between align-items-center">
          <div>
            <a href="{{ url_for('shop') }}" class="btn btn-outline-secondary">Continue shopping</a>
          </div>
          <div>
            <strong class="me-3">Total: ₹{{ '%.0f' % total }}</strong>
            <button class="btn btn-3d" type="submit">Update Cart</button>
            <a href="{{ url_for('checkout') }}" class="btn btn-outline-success ms-2">Checkout</a>
          </div>
        </div>
        </form>
      {% else %}
        <p class="text-muted">Your cart is empty. <a href="{{ url_for('shop') }}">Shop now</a>.</p>
      {% endif %}
    </section>

  {% elif page=='checkout' %}
    <section class="container">
      <h3>Checkout</h3>
      <div class="row">
        <div class="col-md-6">
          <form method="post">
            <div class="mb-2">
              <label class="form-label">Name</label>
              <input name="name" class="form-control" value="{{ user['name'] if user else '' }}" required />
            </div>
            <div class="mb-2">
              <label class="form-label">Phone</label>
              <input name="phone" class="form-control" required />
            </div>
            <div class="mb-2">
              <label class="form-label">Address</label>
              <textarea name="address" class="form-control" rows="3" required></textarea>
            </div>
            <div class="mb-2">
              <label class="form-label">Payment method</label>
              <select name="method" class="form-select">
                <option>Cash on Delivery</option>
              </select>
            </div>
            <button class="btn btn-3d">Place Order (COD)</button>
          </form>
        </div>
        <div class="col-md-6">
          <h5>Order Summary</h5>
          <ul class="list-group">
            {% for it in items %}
              <li class="list-group-item d-flex justify-content-between align-items-center">
                {{ it['qty'] }} x {{ it['title'] }} <span>₹{{ '%.0f' % (it['qty'] * it['price']) }}</span>
              </li>
            {% endfor %}
            <li class="list-group-item d-flex justify-content-between"><strong>Total</strong><strong>₹{{ '%.0f' % total }}</strong></li>
          </ul>
        </div>
      </div>
    </section>

  {% elif page=='orders' %}
    <section class="container">
      <h3>Your Orders</h3>
      {% if orders %}
        {% for o in orders %}
          <div class="card mb-3">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <h6>Order #{{ o['id'] }}</h6>
                  <small class="text-muted">{{ o['created_at'][:16] }}</small>
                </div>
                <div class="text-end">
                  <div>Status: <span class="badge bg-secondary">{{ o['status'] }}</span></div>
                  <div>Total: ₹{{ '%.0f' % o['total'] }}</div>
                </div>
              </div>
              <hr>
              <ul>
                {% for it in o['items'] %}
                  <li>{{ it['qty'] }} x {{ it['title'] }} — ₹{{ '%.0f' % (it['qty'] * it['price']) }}</li>
                {% endfor %}
              </ul>
            </div>
          </div>
        {% endfor %}
      {% else %}
        <p class="text-muted">No orders yet. <a href="{{ url_for('shop') }}">Shop now</a>.</p>
      {% endif %}
    </section>

  {% elif page=='wishlist' %}
    <section class="container">
      <h3>Your Wishlist</h3>
      {% if items %}
        <div class="row g-3">
          {% for p in items %}
            <div class="col-md-3">
              <div class="card">
                <img src="{{ p['image_url'] }}" class="img-fluid" style="height:160px;object-fit:cover;" />
                <div class="p-2">
                  <h6>{{ p['title'] }}</h6>
                  <div class="d-flex justify-content-between">
                    <strong>₹{{ '%.0f' % p['price'] }}</strong>
                    <div>
                      <a href="{{ url_for('cart_add', pid=p['id']) }}" class="btn btn-sm btn-outline-success">Add</a>
                      <a href="{{ url_for('wishlist_toggle', pid=p['id']) }}" class="btn btn-sm btn-outline-danger">Remove</a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          {% endfor %}
        </div>
      {% else %}
        <p class="text-muted">No wishlist items. <a href="{{ url_for('shop') }}">Browse products</a>.</p>
      {% endif %}
    </section>

  {% elif page=='contact' %}
    <section class="container">
      <h3>Contact Us</h3>
      <div class="row g-3">
        <div class="col-md-6">
          <form method="post">
            <div class="mb-2"><input class="form-control" name="name" placeholder="Your name" required></div>
            <div class="mb-2"><input class="form-control" name="email" placeholder="Email" required></div>
            <div class="mb-2"><textarea class="form-control" name="message" placeholder="Message" rows="5" required></textarea></div>
            <button class="btn btn-3d">Send message</button>
          </form>
          <div class="mt-3">
            <a href="https://wa.me/919999999999" target="_blank" class="btn btn-outline-success">WhatsApp us</a>
          </div>
        </div>
        <div class="col-md-6">
          <iframe class="contact-map" src="https://maps.google.com/maps?q=New%20Delhi&t=&z=13&ie=UTF8&iwloc=&output=embed"></iframe>
        </div>
      </div>
    </section>

  {% elif page=='login' %}
    <section class="container d-flex justify-content-center">
      <div class="card p-4" style="width:420px;">
        <h4 class="mb-3">Login</h4>
        <form method="post">
          <div class="mb-2"><input name="email" class="form-control" placeholder="Email" required></div>
          <div class="mb-2"><input name="password" type="password" class="form-control" placeholder="Password" required></div>
          <button class="btn btn-3d w-100">Login</button>
        </form>
        <div class="mt-2 text-center"><small>Don't have an account? <a href="{{ url_for('signup') }}">Signup</a></small></div>
      </div>
    </section>

  {% elif page=='signup' %}
    <section class="container d-flex justify-content-center">
      <div class="card p-4" style="width:420px;">
        <h4 class="mb-3">Signup</h4>
        <form method="post">
          <div class="mb-2"><input name="name" class="form-control" placeholder="Full name" required></div>
          <div class="mb-2"><input name="email" class="form-control" placeholder="Email" required></div>
          <div class="mb-2"><input name="password" type="password" class="form-control" placeholder="Password" required></div>
          <button class="btn btn-3d w-100">Create account</button>
        </form>
      </div>
    </section>

  {% elif page=='admin' %}
    <section class="container">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Admin Panel</h3>
        <a href="{{ url_for('admin_add') }}" class="btn btn-3d">Add product</a>
      </div>
      <div class="row g-3">
        {% for p in products %}
          <div class="col-md-4">
            <div class="card">
              <img src="{{ p['image_url'] }}" class="img-fluid" style="height:180px;object-fit:cover;">
              <div class="p-2">
                <h6>{{ p['title'] }}</h6>
                <small class="text-muted">{{ p['category'] }}</small>
                <div class="mt-2 d-flex justify-content-between">
                  <a href="{{ url_for('admin_edit', pid=p['id']) }}" class="btn btn-sm btn-outline-secondary">Edit</a>
                  <a href="{{ url_for('admin_delete', pid=p['id']) }}" class="btn btn-sm btn-outline-danger">Delete</a>
                </div>
              </div>
            </div>
          </div>
        {% endfor %}
      </div>
    </section>

  {% elif page=='admin_add' %}
    <section class="container">
      <h3>Add Product</h3>
      <form method="post">
        <div class="mb-2"><input name="title" class="form-control" placeholder="Title" required></div>
        <div class="mb-2"><input name="category" class="form-control" placeholder="Category" required></div>
        <div class="mb-2"><input name="price" type="number" step="0.01" class="form-control" placeholder="Price" required></div>
        <div class="mb-2"><input name="image_url" class="form-control" placeholder="Image URL"></div>
        <div class="mb-2"><textarea name="description" class="form-control" rows="4" placeholder="Description"></textarea></div>
        <button class="btn btn-3d">Add Product</button>
      </form>
    </section>

  {% elif page=='admin_edit' %}
    <section class="container">
      <h3>Edit Product</h3>
      <form method="post">
        <div class="mb-2"><input name="title" class="form-control" value="{{ product['title'] }}" required></div>
        <div class="mb-2"><input name="category" class="form-control" value="{{ product['category'] }}" required></div>
        <div class="mb-2"><input name="price" type="number" step="0.01" class="form-control" value="{{ product['price'] }}" required></div>
        <div class="mb-2"><input name="image_url" class="form-control" value="{{ product['image_url'] }}"></div>
        <div class="mb-2"><textarea name="description" class="form-control" rows="4">{{ product['description'] }}</textarea></div>
        <button class="btn btn-3d">Save Changes</button>
      </form>
    </section>
  {% endif %}

  <footer class="footer mt-5">
    <div class="container">
      <div class="row">
        <div class="col-md-4">
          <h5 style="color:#f5e6db">Classical Wood Express</h5>
          <p class="text-muted small">Handcrafted premium wooden furniture — mahogany, oak, walnut. Quality that lasts generations.</p>
        </div>
        <div class="col-md-4">
          <h6 style="color:#f5e6db">Quick Links</h6>
          <ul class="list-unstyled small">
            <li><a class="text-muted" href="{{ url_for('shop') }}">Shop</a></li>
            <li><a class="text-muted" href="{{ url_for('contact') }}">Contact</a></li>
            <li><a class="text-muted" href="{{ url_for('wishlist') }}">Wishlist</a></li>
          </ul>
        </div>
        <div class="col-md-4 text-md-end">
          <h6 style="color:#f5e6db">Follow</h6>
          <div class="d-flex gap-2 justify-content-md-end">
            <a class="btn btn-sm btn-outline-light rounded-pill">Instagram</a>
            <a class="btn btn-sm btn-outline-light rounded-pill">Facebook</a>
            <a class="btn btn-sm btn-outline-light rounded-pill">Pinterest</a>
          </div>
        </div>
      </div>
    </div>
  </footer>

  <!-- FAQ Chatbot bubble & popup -->
  <div class="faq-bubble">
    <div class="bubble" id="faqBubble">?</div>
    <div class="chat-popup" id="chatPopup">
      <div class="chat-head d-flex align-items-center justify-content-between">
        <div>
          <div style="font-weight:800">FAQ Assistant</div>
          <small>Ask about orders, delivery, returns</small>
        </div>
        <div><button class="btn btn-sm btn-outline-light" id="chatClose">Close</button></div>
      </div>
      <div class="chat-body" id="chatBody">
        <div class="small text-muted">Try: "shipping", "delivery time", "returns", "payment".</div>
      </div>
      <div class="chat-input">
        <input type="text" id="chatInput" class="form-control" placeholder="Type a question..." />
        <button class="btn btn-3d" id="chatSend">Send</button>
      </div>
    </div>
  </div>

  <!-- Bootstrap 5 JS -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

  <script>
    // tiny tilt effect for cards/images
    function tilt(e, el) {
      let rect = el.getBoundingClientRect();
      let x = e.clientX - rect.left;
      let y = e.clientY - rect.top;
      let cx = rect.width / 2;
      let cy = rect.height / 2;
      let dx = (x - cx) / cx;
      let dy = (y - cy) / cy;
      let rY = dx * 6; // rotateY
      let rX = -dy * 6; // rotateX
      el.style.transform = `perspective(900px) rotateX(${rX}deg) rotateY(${rY}deg) translateZ(8px)`;
    }
    function tiltReset(el) { el.style.transform = 'none'; }

    // FAQ chatbot toggle & simple fetch
    const faqBubble = document.getElementById('faqBubble');
    const chatPopup = document.getElementById('chatPopup');
    const chatClose = document.getElementById('chatClose');
    const chatSend = document.getElementById('chatSend');
    const chatInput = document.getElementById('chatInput');
    const chatBody = document.getElementById('chatBody');

    faqBubble.addEventListener('click', ()=> {
      chatPopup.style.display = chatPopup.style.display==='block' ? 'none' : 'block';
    });
    chatClose.addEventListener('click', ()=> chatPopup.style.display='none');

    function appendChat(role, text) {
      let el = document.createElement('div');
      el.style.marginBottom = '8px';
      if (role==='user') {
        el.innerHTML = `<div style="text-align:right"><div style="display:inline-block;background:#ffeacc;padding:8px;border-radius:10px;">${text}</div></div>`;
      } else {
        el.innerHTML = `<div style="text-align:left"><div style="display:inline-block;background:#f1f1f1;padding:8px;border-radius:10px;">${text}</div></div>`;
      }
      chatBody.appendChild(el); chatBody.scrollTop = chatBody.scrollHeight;
    }

    chatSend.addEventListener('click', async ()=>{
      let q = chatInput.value.trim(); if(!q) return;
      appendChat('user', q);
      chatInput.value = '';
      appendChat('bot', 'Thinking...');
      try {
        let res = await fetch('{{ url_for("faq_chat") }}', {
          method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({q})
        });
        let data = await res.json();
        // remove 'Thinking...' then append answer
        chatBody.lastChild.remove();
        appendChat('bot', data.answer);
      } catch (e) {
        chatBody.lastChild.remove();
        appendChat('bot', 'Oops — something went wrong.');
      }
    });

    // small animation pulse for CTA
    setInterval(()=> {
      let cta = document.querySelector('.btn-3d');
      if(cta) { cta.animate([{transform:'translateY(0)'},{transform:'translateY(-6px)'},{transform:'translateY(0)'}], {duration:1800, iterations:1}); }
    }, 6000);

  </script>
</body>
</html>
"""

##### ---------- Run ---------- #####
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
