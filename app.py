def get_db():
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  return conn

def hash_password(pw):
  return "".join(reversed(pw)) + "CWEX"

def generate_otp():
  return ''.join(random.choices(string.digits, k=6))

def generate_tracking_code():
  return "CWEX" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
import os
import sqlite3
import random
import string
import json
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, render_template_string, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_NAME = 'classical_wood_express.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('is_admin', False)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        price REAL,
        image_url TEXT
    )''')
    conn.commit()
    conn.close()

# --- HOME PAGE ---
@app.route('/')
def home():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, category, price, image_url FROM products ORDER BY id DESC LIMIT 8")
    featured_products = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Classical Wood Express</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
          body {
            background: radial-gradient(circle at 50% 30%, #b6864d 0%, #2d1a0b 100%);
            color: #fff;
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            perspective: 1200px;
            overflow-x: hidden;
          }
          .parallax {
            perspective: 1200px;
            transform-style: preserve-3d;
          }
          .hero-content {
            transform: translateZ(60px) scale(1.05);
            box-shadow: 0 8px 32px #b6864d99;
            background: rgba(44,27,13,0.7);
            border-radius: 18px;
            padding: 32px 0;
          }
          h2, h1, .fw-bold, .display-4 { color: #fff !important; text-shadow: 0 2px 8px #000a; }
          .wishlist-heart {
            position: absolute; top: 12px; right: 18px; font-size: 2rem; color: #ff4d4d;
            background: rgba(44,27,13,0.7); border-radius: 50%; padding: 6px; cursor: pointer; z-index: 10; transition: color 0.2s;
          }
          .wishlist-heart:hover { color: #fff; }
          .btn-3d { background: #b6864d; color: #fff; border: none; box-shadow: 0 2px 8px #0002; border-radius: 8px; }
          .btn-3d:hover { background: #a67c52; color: #fff; }
          .tagline {
            font-size: 1.7rem;
            font-weight: bold;
            color: #ffd700;
            text-shadow: 0 2px 12px #000a;
            margin-bottom: 18px;
            letter-spacing: 1px;
          }
        </style>
    </head>
    <body>
    <nav class="navbar navbar-expand-lg navbar-dark">
      <div class="container">
        <div style="position:relative;top:38px;">
          <a class="navbar-brand fw-bold d-flex align-items-center" href="/">
            <span style="display:inline-block;vertical-align:middle;margin-right:8px;">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="16" cy="16" r="16" fill="#b6864d"/>
                <ellipse cx="16" cy="18" rx="7" ry="5" fill="#4caf50"/>
                <rect x="14.5" y="18" width="3" height="7" rx="1.2" fill="#8d5524"/>
                <ellipse cx="16" cy="13" rx="4" ry="3" fill="#388e3c"/>
              </svg>
            </span>
            Classical Wood Express
          </a>
        </div>
        <div style="position:fixed;top:0;right:0;z-index:1050;background:rgba(44,27,13,0.95);padding:8px 18px 8px 8px;border-bottom-left-radius:18px;box-shadow:0 2px 12px #0003;">
          <ul class="navbar-nav flex-row gap-2 mb-0">
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/orders">Orders</a></li>
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/contact">Contact</a></li>
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/logout">Logout</a></li>
            <li class="nav-item">
              <a class="nav-link px-2 text-white" href="https://www.instagram.com/classicalwood_expressstudio?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==" target="_blank" title="Instagram">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-instagram" viewBox="0 0 16 16">
                  <path d="M8 3c1.657 0 1.86.006 2.513.036.653.03 1.09.14 1.343.237.29.107.497.236.717.456.22.22.349.427.456.717.097.253.207.69.237 1.343C12.994 6.14 13 6.343 13 8c0 1.657-.006 1.86-.036 2.513-.03.653-.14 1.09-.237 1.343-.107.29-.236.497-.456.717-.22.22-.427.349-.717.456-.253.097-.69.207-1.343.237C9.86 12.994 9.657 13 8 13c-1.657 0-1.86-.006-2.513-.036-.653-.03-1.09-.14-1.343-.237-.29-.107-.497-.236-.717-.456-.22-.22-.349-.427-.456-.717-.097-.253-.207-.69-.237-1.343C3.006 9.86 3 9.657 3 8c0-1.657.006-1.86.036-2.513.03-.653.14-1.09.237-1.343.107-.29.236-.497.456-.717.22-.22.427-.349.717-.456.253-.097.69-.207 1.343-.237C6.14 3.006 6.343 3 8 3zm0-1C6.326 2 6.107 2.007 5.447 2.037c-.667.03-1.124.14-1.513.29a2.68 2.68 0 0 0-.97.634 2.68 2.68 0 0 0-.634.97c-.15.389-.26.846-.29 1.513C2.007 6.107 2 6.326 2 8c0 1.674.007 1.893.037 2.553.03.667.14 1.124.29 1.513.15.389.36.72.634.97.25.274.581.484.97.634.389.15.846.26 1.513.29.66.03.879.037 2.553.037s1.893-.007 2.553-.037c.667-.03 1.124-.14 1.513-.29a2.68 2.68 0 0 0 .97-.634 2.68 2.68 0 0 0 .634-.97c.15-.389.26-.846.29-1.513.03-.66.037-.879.037-2.553s-.007-1.893-.037-2.553c-.03-.667-.14-1.124-.29-1.513a2.68 2.68 0 0 0-.634-.97 2.68 2.68 0 0 0-.97-.634c-.389-.15-.846-.26-1.513-.29C9.893 2.007 9.674 2 8 2z"/>
                  <path d="M8 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm0 5a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"/>
                  <circle cx="12.5" cy="3.5" r="1"/>
                </svg>
              </a>
            </li>
          </ul>
        </div>
        <div style="position:fixed;top:0;left:0;z-index:1050;padding:8px 18px 8px 8px;border-bottom-right-radius:18px;box-shadow:0 2px 12px #0003;">
          <ul class="navbar-nav flex-row gap-2 mb-0">
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/shop">Shop</a></li>
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/wishlist">Wishlist</a></li>
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/cart">Add to Cart</a></li>
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/login">Login</a></li>
            <li class="nav-item"><a class="nav-link px-2 text-white fw-bold" href="/signup">Signup</a></li>
          </ul>
        </div>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav"></div>
      </div>
    </nav>
    <div class="hero parallax">
      <div class="hero-content text-center">
  <!-- Company name and tagline removed as requested -->
        <p class="lead mb-4">Crafted Wood, Deliver Quickly</p>
        <a href="/shop" class="btn btn-3d btn-lg">Explore Shop</a>
      </div>
    </div>
    <div id="bg-3d"></div>
    <script src="https://cdn.jsdelivr.net/npm/three@0.153.0/build/three.min.js"></script>
    <script>
      const bgContainer = document.getElementById('bg-3d');
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
      const renderer = new THREE.WebGLRenderer({antialias:true,alpha:true});
      renderer.setClearColor(0x000000, 0);
      renderer.setSize(window.innerWidth, window.innerHeight);
      bgContainer.appendChild(renderer.domElement);
      scene.add(new THREE.AmbientLight(0x222222, 1.2));
      const dirLight = new THREE.DirectionalLight(0x8d5524, 1.1);
      dirLight.position.set(2,4,4);
      scene.add(dirLight);
      const plankGeometry = new THREE.BoxGeometry(2,0.2,0.5);
      const textureLoader = new THREE.TextureLoader();
      const woodTexture = textureLoader.load('https://images.unsplash.com/photo-1465101162946-4377e57745c3?fit=crop&w=500&q=80');
      const plankMaterial = new THREE.MeshStandardMaterial({map:woodTexture, roughness:0.3, metalness:0.2});
      const planks = [];
  for(let i=0;i<48;i++){
        const plank = new THREE.Mesh(plankGeometry, plankMaterial);
  plank.position.x = Math.random()*24-12;
  plank.position.y = Math.random()*12-6;
  plank.position.z = Math.random()*-18;
        plank.rotation.z = Math.random()*Math.PI;
        scene.add(plank);
        planks.push(plank);
      }
      camera.position.z = 14;
      function animate(){
        requestAnimationFrame(animate);
        planks.forEach((plank,i)=>{
          plank.rotation.x += 0.003 + i*0.0003;
          plank.rotation.y += 0.004 + i*0.0002;
          plank.position.x += Math.sin(Date.now()*0.0002+i)*0.003;
        });
        renderer.render(scene,camera);
      }
      animate();
      window.addEventListener('resize',()=>{
        renderer.setSize(window.innerWidth,window.innerHeight);
        camera.aspect = window.innerWidth/window.innerHeight;
        camera.updateProjectionMatrix();
      });
    </script>
    <div class="container py-5">
      <h2 class="text-center fw-bold mb-4">Featured Categories</h2>
      <div class="row justify-content-center mb-5">
        {% for cat in ['Chairs','Tables','Shelves','Beds'] %}
          <div class="col-6 col-md-3">
            <a href="/shop?category={{cat}}" class="d-block category-tile text-center" style="text-decoration:none;">
              <div style="
                font-size:34px;
                margin-bottom:10px;
                color:#fff;
                filter: drop-shadow(0 2px 8px #0006);
              "><i class="bi bi-box"></i></div>
              <div style="
                background: linear-gradient(135deg, #b6864d 60%, #2d1a0b 100%);
                box-shadow: 0 8px 32px #b6864d99, 0 2px 12px #0003;
                border-radius: 18px;
                padding: 32px 0 18px 0;
                margin-bottom: 8px;
                transform: perspective(600px) rotateX(8deg) scale(1.04);
                border: 2px solid #fffbe9;
                transition: transform 0.2s, box-shadow 0.2s;
                color: #fff;
                font-weight: bold;
                letter-spacing: 1px;
              " class="shadow-lg">
                {{cat}}
              </div>
            </a>
          </div>
        {% endfor %}
      </div>
      <h2 class="text-center fw-bold mb-4">Featured Products</h2>
      <div class="row">
        {% for p in featured_products %}
          <div class="col-6 col-md-3 mb-4">
            <div class="product-card h-100 position-relative">
              <a href="/wishlist/add/{{p['id']}}" class="wishlist-heart" title="Add to Wishlist">
                <i class="bi bi-heart-fill"></i>
              </a>
              <img src="{{p['image_url']}}" class="w-100" style="height:140px;object-fit:cover;">
              <div class="p-2">
                <div class="fw-bold">{{p['title']}}</div>
                <div class="text-muted">{{p['category']}}</div>
                <div class="fw-bold text-success">₹{{p['price']}}</div>
                <form method="post" action="/cart/add">
                  <input type="hidden" name="pid" value="{{p['id']}}">
                  <button class="btn btn-3d add-to-cart-btn w-100" type="submit">
                    <img src="{{p['image_url']}}" style="height:24px;width:24px;object-fit:cover;border-radius:4px;margin-right:8px;vertical-align:middle;"> Add to Cart
                  </button>
                </form>
                <a href="/product/{{p['id']}}" class="btn btn-3d mt-1 w-100">View</a>
              </div>
            </div>
          </div>
        {% endfor %}
      </div>
    </div>
    <div class="footer mt-5">
      <div class="container">
        <div class="row mb-3">
          <div class="col-6 col-md-3"><div class="fw-bold mb-2">Quick Links</div>
            <a class="quick-link d-block" href="/shop">Shop</a>
            <a class="quick-link d-block" href="/wishlist">Wishlist</a>
            <a class="quick-link d-block" href="/orders">Orders</a>
            <a class="quick-link d-block" href="/cart">Cart</a>
          </div>
          <div class="col-6 col-md-3"><div class="fw-bold mb-2">Contact</div>
            <div>Email: <a href="mailto:classicalwoodexpress@gmail.com">classicalwoodexpress@gmail.com</a></div>
            <div>Instagram: <a href="https://www.instagram.com/classicalwood_expressstudio?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==" target="_blank">@classicalwood_expressstudio</a></div>
            <div>WhatsApp: <a href="https://wa.me/919999999999">+91 99999 99999</a></div>
            <div>Location: <a href="/contact">View Map</a></div>
          </div>
          <div class="col-12 col-md-6">
            <div class="fw-bold mb-2">Newsletter</div>
            <form class="d-flex">
              <input type="email" class="form-control me-2" placeholder="Your Email">
              <button class="btn btn-3d">Subscribe</button>
            </form>
            <div class="mt-2">
              <a href="https://www.instagram.com/classicalwood_expressstudio?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==" class="me-3" target="_blank"><i class="bi bi-instagram"></i></a>
              <a href="#" class="me-3"><i class="bi bi-facebook"></i></a>
              <a href="#" class="me-3"><i class="bi bi-twitter"></i></a>
            </div>
          </div>
        </div>
        <div class="text-center small mt-3">&copy; 2025 Classical Wood Express. Crafted in India.</div>
      </div>
    </div>
    <!-- Floating Wood Chatbot -->
  <div id="wood-chatbot-btn" style="position:fixed;top:90px;right:32px;z-index:10500;transition:box-shadow 0.2s;">
      <button onclick="toggleWoodChatbot()" style="background:#b6864d;border:none;border-radius:50%;width:64px;height:64px;box-shadow:0 2px 12px #0005;display:flex;align-items:center;justify-content:center;transition:box-shadow 0.2s;">
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="18" cy="18" r="18" fill="#8d5524"/>
          <ellipse cx="18" cy="22" rx="8" ry="6" fill="#b6864d"/>
          <rect x="16" y="22" width="4" height="8" rx="2" fill="#4caf50"/>
          <ellipse cx="18" cy="15" rx="5" ry="4" fill="#388e3c"/>
        </svg>
      </button>
    </div>
    <div id="wood-chatbot-window" style="position:fixed;top:110px;right:32px;width:340px;max-width:90vw;background:#fffbe9;border-radius:18px;box-shadow:0 4px 24px #0005;z-index:10500;display:none;flex-direction:column;overflow:hidden;transition:box-shadow 0.2s;">
      <div style="background:#b6864d;color:#fff;padding:14px 18px;font-weight:bold;font-size:1.1rem;display:flex;align-items:center;gap:8px;">
        <svg width="28" height="28" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="18" cy="18" r="18" fill="#8d5524"/><ellipse cx="18" cy="22" rx="8" ry="6" fill="#b6864d"/><rect x="16" y="22" width="4" height="8" rx="2" fill="#4caf50"/><ellipse cx="18" cy="15" rx="5" ry="4" fill="#388e3c"/></svg>
        Wood AI Chatbot
        <span style="flex:1"></span>
        <button onclick="toggleWoodChatbot()" style="background:none;border:none;color:#fff;font-size:1.3rem;">&times;</button>
      </div>
      <div id="wood-chatbot-messages" style="padding:12px 16px;height:260px;overflow-y:auto;font-size:1rem;background:#fffbe9;"></div>
      <form id="wood-chatbot-form" style="display:flex;padding:10px 12px;background:#f5e6c8;gap:8px;" onsubmit="sendWoodChatbotMsg(event)">
        <input id="wood-chatbot-input" type="text" class="form-control" placeholder="Ask about products, orders, returns, prices, delivery..." autocomplete="off" style="flex:1;">
        <button class="btn btn-3d" type="submit">Send</button>
      </form>
    </div>
    <script>
    function toggleWoodChatbot() {
      const win = document.getElementById('wood-chatbot-window');
      win.style.display = win.style.display === 'none' ? 'flex' : 'none';
    }
    function sendWoodChatbotMsg(e) {
      e.preventDefault();
      const input = document.getElementById('wood-chatbot-input');
      const msg = input.value.trim();
      if (!msg) return;
      addWoodChatbotMsg('user', msg);
      input.value = '';
      setTimeout(()=>{
        addWoodChatbotMsg('bot', woodChatbotReply(msg));
      }, 400);
    }
    function addWoodChatbotMsg(sender, text) {
      const messages = document.getElementById('wood-chatbot-messages');
      const div = document.createElement('div');
      div.style.marginBottom = '10px';
      div.style.display = 'flex';
      div.style.justifyContent = sender==='user'?'flex-end':'flex-start';
      div.innerHTML = `<span style="background:${sender==='user'?'#b6864d':'#fff'};color:${sender==='user'?'#fff':'#8d5524'};padding:8px 14px;border-radius:14px;max-width:80%;display:inline-block;">${text}</span>`;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }
    function woodChatbotReply(msg) {
      msg = msg.toLowerCase();
      if (msg.includes('recommend') || msg.includes('suggest')) {
        return 'Our bestsellers: Oak Chair, Teak Table, Walnut Shelf, Premium Bed. Want details or prices?';
      }
      if (msg.includes('order') && msg.includes('track')) {
        return 'Track your order live in the Orders section. Need help with a specific order?';
      }
      if (msg.includes('hello') || msg.includes('hi') || msg.includes('hey')) {
        return 'Hello! 👋 I’m Wood AI. Ask me about products, delivery, returns, or anything wood!';
      }
      if (msg.includes('return')) {
        return 'Returns accepted within 7 days. Need help with a return or refund?';
      }
      if (msg.includes('price') || msg.includes('cost')) {
        return 'Prices are listed on each product. Looking for a specific item or price range?';
      }
      if (msg.includes('delivery') || msg.includes('ship')) {
        return 'We deliver across India, fast and safe. Want premium delivery?';
      }
      if (msg.includes('thanks') || msg.includes('thank you')) {
        return 'You’re welcome! 😊 Anything else I can help with?';
      }
      if (msg.includes('bad') || msg.includes('angry') || msg.includes('upset') || msg.includes('problem')) {
        return 'Sorry to hear that. Can I help resolve your issue or connect you to support?';
      }
      if (msg.includes('good') || msg.includes('love') || msg.includes('great') || msg.includes('awesome')) {
        return 'Glad you love our products! Want recommendations or have feedback?';
      }
      if (msg.includes('contact') || msg.includes('support')) {
        return 'You can contact us via WhatsApp, Instagram, or the Contact page.';
      }
      if (msg.includes('faq')) {
        return 'Ask me anything about products, orders, returns, or delivery!';
      }
      // Fallback: try to be more helpful
      if (msg.length < 4) {
        return 'Could you please provide more details or ask a specific question about our products, prices, delivery, or returns?';
      }
      if (msg.includes('product') || msg.includes('item')) {
        return 'We offer a wide range of wood products: chairs, tables, shelves, beds, and more. What are you looking for specifically?';
      }
      if (msg.includes('recommend') || msg.includes('suggest')) {
        return 'Our bestsellers: Oak Chair, Teak Table, Walnut Shelf, Premium Bed. Want details or prices?';
      }
      if (msg.includes('order') && msg.includes('track')) {
        return 'Track your order live in the Orders section. Need help with a specific order?';
      }
      if (msg.includes('return')) {
        return 'Returns accepted within 7 days. Need help with a return or refund?';
      }
      if (msg.includes('price') || msg.includes('cost')) {
        return 'Prices are listed on each product. Looking for a specific item or price range?';
      }
      if (msg.includes('delivery') || msg.includes('ship')) {
        return 'We deliver across India, fast and safe. Want premium delivery?';
      }
      if (msg.includes('thanks') || msg.includes('thank you')) {
        return 'You’re welcome! 😊 Anything else I can help with?';
      }
      if (msg.includes('bad') || msg.includes('angry') || msg.includes('upset') || msg.includes('problem')) {
        return 'Sorry to hear that. Can I help resolve your issue or connect you to support?';
      }
      if (msg.includes('good') || msg.includes('love') || msg.includes('great') || msg.includes('awesome')) {
        return 'Glad you love our products! Want recommendations or have feedback?';
      }
      if (msg.includes('contact') || msg.includes('support')) {
        return 'You can contact us via WhatsApp, Instagram, or the Contact page.';
      }
      if (msg.includes('faq')) {
        return 'Ask me anything about products, orders, returns, or delivery!';
      }
      return 'I’m Wood AI! How can I help you today? Ask about products, prices, delivery, returns, or anything else.';
    }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', featured_products=featured_products, is_logged_in=is_logged_in(), is_admin=is_admin())
    return render_template_string('''
    <html><head><title>Shop - Classical Wood Express</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container"><a class="navbar-brand" href="/">Classical Wood Express</a></div>
    </nav>
    <div class="container py-5">
      <h2 class="fw-bold mb-4">Shop</h2>
      <div class="row">
        {% for p in products %}
        <div class="col-6 col-md-3 mb-4">
          <div class="card h-100">
            <img src="{{p['image_url']}}" class="card-img-top" style="height:140px;object-fit:cover;">
            <div class="card-body">
              <h5 class="card-title">{{p['title']}}</h5>
              <p class="card-text">{{p['category']}}</p>
              <p class="card-text fw-bold text-success">₹{{p['price']}}</p>
              <form method="post" action="/cart/add">
                <input type="hidden" name="pid" value="{{p['id']}}">
                <button class="btn btn-primary w-100" type="submit">Add to Cart</button>
              </form>
            </div>
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
    </body></html>
    ''', products=products)
# Error handler for 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template_string('''
    <html><head><title>404 Not Found</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container"><a class="navbar-brand" href="/">Classical Wood Express</a></div>
    </nav>
    <div class="container py-5 text-center">
      <h2 class="fw-bold mb-4">404 - Page Not Found</h2>
      <p>The page you are looking for does not exist.</p>
      <a href="/" class="btn btn-primary">Go Home</a>
    </div>
    </body></html>
    '''), 404
    return render_template_string('''
    <html><head><title>Signup - Classical Wood Express</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container"><a class="navbar-brand" href="/">Classical Wood Express</a></div>
    </nav>
    <div class="container py-5">
      <h2 class="fw-bold mb-4">Signup</h2>
      <form method="post" action="/signup">
        <div class="mb-3">
          <label>Email</label>
          <input type="email" class="form-control" name="email" required>
        </div>
        <div class="mb-3">
          <label>Password</label>
          <input type="password" class="form-control" name="password" required>
        </div>
        <button class="btn btn-primary" type="submit">Sign Up</button>
      </form>
      <p class="mt-3">Already have an account? <a href="/login">Login</a></p>
    </div>
    </body></html>
    ''')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, category, price, image_url FROM products ORDER BY id DESC LIMIT 8")
    featured_products = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body {
        background: radial-gradient(circle at 50% 30%, #b6864d 0%, #2d1a0b 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .parallax {
        perspective: 1200px;
        transform-style: preserve-3d;
      }
      .hero-content {
        transform: translateZ(60px) scale(1.05);
        box-shadow: 0 8px 32px #b6864d99;
        background: rgba(44,27,13,0.7);
        border-radius: 18px;
        padding: 32px 0;
      }
      h2, h1, .fw-bold, .display-4 { color: #fff !important; text-shadow: 0 2px 8px #000a; }
      .wishlist-heart {
        position: absolute; top: 12px; right: 18px; font-size: 2rem; color: #ff4d4d;
        background: rgba(44,27,13,0.7); border-radius: 50%; padding: 6px; cursor: pointer; z-index: 10; transition: color 0.2s;
      }
      .wishlist-heart:hover { color: #fff; }
      .btn-3d { background: #b6864d; color: #fff; border: none; box-shadow: 0 2px 8px #0002; border-radius: 8px; }
      .btn-3d:hover { background: #a67c52; color: #fff; }
      .tagline {
        font-size: 1.7rem;
        font-weight: bold;
        color: #ffd700;
        text-shadow: 0 2px 12px #000a;
        margin-bottom: 18px;
        letter-spacing: 1px;
      }
    </style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark">
  <div class="container">
    <a class="navbar-brand fw-bold d-flex align-items-center" href="/">
      <span style="display:inline-block;vertical-align:middle;margin-right:8px;">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="16" cy="16" r="16" fill="#b6864d"/>
          <ellipse cx="16" cy="18" rx="7" ry="5" fill="#4caf50"/>
          <rect x="14.5" y="18" width="3" height="7" rx="1.2" fill="#8d5524"/>
          <ellipse cx="16" cy="13" rx="4" ry="3" fill="#388e3c"/>
        </svg>
      </span>
      Classical Wood Express
    </a>
    <span class="ms-2">Crafted Wood, Deliver Quickly</span>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item"><a class="nav-link" href="/shop">Shop</a></li>
        <li class="nav-item"><a class="nav-link" href="/wishlist">Wishlist</a></li>
        <li class="nav-item"><a class="nav-link" href="/orders">Orders</a></li>
        <li class="nav-item"><a class="nav-link" href="/contact">Contact</a></li>
        <li class="nav-item"><a class="nav-link" href="/cart"><i class="bi bi-cart3"></i> Cart</a></li>
        {% if is_logged_in %}
          <li class="nav-item"><a class="nav-link" href="/logout">Logout</a></li>
        {% else %}
          <li class="nav-item"><a class="nav-link" href="/login">Login/Signup</a></li>
        {% endif %}
        {% if is_admin %}
          <li class="nav-item"><a class="nav-link" href="/admin">Admin</a></li>
        {% endif %}
      </ul>
    </div>
  </div>
</nav>
<div class="hero parallax">
  <div class="hero-content text-center">
    <h1 class="display-4 fw-bold">Classical Wood Express</h1>
    <div class="tagline">India's Fastest Online Wood Store – Crafted, Delivered, Loved.</div>
    <p class="lead mb-4">Crafted Wood, Deliver Quickly</p>
    <a href="/shop" class="btn btn-3d btn-lg">Explore Shop</a>
  </div>
</div>
  <div id="bg-3d" style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;"></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.153.0/build/three.min.js"></script>
<script>
  const bgContainer = document.getElementById('bg-3d');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({antialias:true,alpha:true});
  renderer.setClearColor(0x000000, 0);
  renderer.setSize(window.innerWidth, window.innerHeight);
  bgContainer.appendChild(renderer.domElement);
  scene.add(new THREE.AmbientLight(0x222222, 1.2));
  const dirLight = new THREE.DirectionalLight(0x8d5524, 1.1);
  dirLight.position.set(2,4,4);
  scene.add(dirLight);
  const plankGeometry = new THREE.BoxGeometry(2,0.2,0.5);
  const textureLoader = new THREE.TextureLoader();
  const woodTexture = textureLoader.load('https://images.unsplash.com/photo-1465101162946-4377e57745c3?fit=crop&w=500&q=80');
  const plankMaterial = new THREE.MeshStandardMaterial({map:woodTexture, roughness:0.3, metalness:0.2});
  const planks = [];
  for(let i=0;i<24;i++){
    const plank = new THREE.Mesh(plankGeometry, plankMaterial);
    plank.position.x = Math.random()*16-8;
    plank.position.y = Math.random()*8-4;
    plank.position.z = Math.random()*-10;
    plank.rotation.z = Math.random()*Math.PI;
    scene.add(plank);
    planks.push(plank);
  }
  camera.position.z = 14;
  function animate(){
    requestAnimationFrame(animate);
    planks.forEach((plank,i)=>{
      plank.rotation.x += 0.003 + i*0.0003;
      plank.rotation.y += 0.004 + i*0.0002;
      plank.position.x += Math.sin(Date.now()*0.0002+i)*0.003;
    });
    renderer.render(scene,camera);
  }
  animate();
  window.addEventListener('resize',()=>{
    renderer.setSize(window.innerWidth,window.innerHeight);
    camera.aspect = window.innerWidth/window.innerHeight;
    camera.updateProjectionMatrix();
  });
</script>
<div class="container py-5">
  <h2 class="text-center fw-bold mb-4">Featured Categories</h2>
  <div class="row justify-content-center mb-5">
    {% for cat in ['Chairs','Tables','Shelves','Beds'] %}
      <div class="col-6 col-md-3">
        <a href="/shop?category={{cat}}" class="d-block category-tile text-center">
          <div style="font-size:34px;"><i class="bi bi-box"></i></div>
          <div class="fw-bold">{{cat}}</div>
        </a>
      </div>
    {% endfor %}
  </div>
  <h2 class="text-center fw-bold mb-4">Featured Products</h2>
  <div class="row">
    {% for p in featured_products %}
      <div class="col-6 col-md-3 mb-4">
        <div class="product-card h-100 position-relative">
          <a href="/wishlist/add/{{p['id']}}" class="wishlist-heart" title="Add to Wishlist">
            <i class="bi bi-heart-fill"></i>
          </a>
          <img src="{{p['image_url']}}" class="w-100" style="height:140px;object-fit:cover;">
          <div class="p-2">
            <div class="fw-bold">{{p['title']}}</div>
            <div class="text-muted">{{p['category']}}</div>
            <div class="fw-bold text-success">₹{{p['price']}}</div>
            <form method="post" action="/cart/add">
              <input type="hidden" name="pid" value="{{p['id']}}">
              <button class="btn btn-3d add-to-cart-btn w-100" type="submit">
                <img src="{{p['image_url']}}" style="height:24px;width:24px;object-fit:cover;border-radius:4px;margin-right:8px;vertical-align:middle;"> Add to Cart
              </button>
            </form>
            <a href="/product/{{p['id']}}" class="btn btn-3d mt-1 w-100">View</a>
          </div>
        </div>
      </div>
    {% endfor %}
  </div>
</div>
<div class="footer mt-5">
  <div class="container">
    <div class="row mb-3">
      <div class="col-6 col-md-3"><div class="fw-bold mb-2">Quick Links</div>
        <a class="quick-link d-block" href="/shop">Shop</a>
        <a class="quick-link d-block" href="/wishlist">Wishlist</a>
        <a class="quick-link d-block" href="/orders">Orders</a>
        <a class="quick-link d-block" href="/cart">Cart</a>
      </div>
      <div class="col-6 col-md-3"><div class="fw-bold mb-2">Contact</div>
        <div>Email: <a href="mailto:classicalwoodexpress@gmail.com">classicalwoodexpress@gmail.com</a></div>
        <div>Instagram: <a href="https://www.instagram.com/classicalwood_expressstudio?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==" target="_blank">@classicalwood_expressstudio</a></div>
        <div>WhatsApp: <a href="https://wa.me/919999999999">+91 99999 99999</a></div>
        <div>Location: <a href="/contact">View Map</a></div>
      </div>
      <div class="col-12 col-md-6">
        <div class="fw-bold mb-2">Newsletter</div>
        <form class="d-flex">
          <input type="email" class="form-control me-2" placeholder="Your Email">
          <button class="btn btn-3d">Subscribe</button>
        </form>
        <div class="mt-2">
          <a href="https://www.instagram.com/classicalwood_expressstudio?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==" class="me-3" target="_blank"><i class="bi bi-instagram"></i></a>
          <a href="#" class="me-3"><i class="bi bi-facebook"></i></a>
          <a href="#" class="me-3"><i class="bi bi-twitter"></i></a>
        </div>
      </div>
    </div>
    <div class="text-center small mt-3">&copy; 2025 Classical Wood Express. Crafted in India.</div>
  </div>
</div>
<!-- Floating Wood Chatbot -->
<div id="wood-chatbot-btn" style="position:fixed;bottom:32px;right:32px;z-index:9999;">
  <button onclick="toggleWoodChatbot()" style="background:#b6864d;border:none;border-radius:50%;width:64px;height:64px;box-shadow:0 2px 12px #0005;display:flex;align-items:center;justify-content:center;">
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="18" cy="18" r="18" fill="#8d5524"/>
      <ellipse cx="18" cy="22" rx="8" ry="6" fill="#b6864d"/>
      <rect x="16" y="22" width="4" height="8" rx="2" fill="#4caf50"/>
      <ellipse cx="18" cy="15" rx="5" ry="4" fill="#388e3c"/>
    </svg>
  </button>
</div>
<div id="wood-chatbot-window" style="position:fixed;bottom:110px;right:32px;width:340px;max-width:90vw;background:#fffbe9;border-radius:18px;box-shadow:0 4px 24px #0005;z-index:9999;display:none;flex-direction:column;overflow:hidden;">
  <div style="background:#b6864d;color:#fff;padding:14px 18px;font-weight:bold;font-size:1.1rem;display:flex;align-items:center;gap:8px;">
    <svg width="28" height="28" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="18" cy="18" r="18" fill="#8d5524"/><ellipse cx="18" cy="22" rx="8" ry="6" fill="#b6864d"/><rect x="16" y="22" width="4" height="8" rx="2" fill="#4caf50"/><ellipse cx="18" cy="15" rx="5" ry="4" fill="#388e3c"/></svg>
    Wood AI Chatbot
    <span style="flex:1"></span>
    <button onclick="toggleWoodChatbot()" style="background:none;border:none;color:#fff;font-size:1.3rem;">&times;</button>
  </div>
  <div id="wood-chatbot-messages" style="padding:12px 16px;height:260px;overflow-y:auto;font-size:1rem;background:#fffbe9;"></div>
  <form id="wood-chatbot-form" style="display:flex;padding:10px 12px;background:#f5e6c8;gap:8px;" onsubmit="sendWoodChatbotMsg(event)">
    <input id="wood-chatbot-input" type="text" class="form-control" placeholder="Ask about products, orders, returns, prices, delivery..." autocomplete="off" style="flex:1;">
    <button class="btn btn-3d" type="submit">Send</button>
  </form>
</div>
<script>
function toggleWoodChatbot() {
  const win = document.getElementById('wood-chatbot-window');
  win.style.display = win.style.display === 'none' ? 'flex' : 'none';
}
function sendWoodChatbotMsg(e) {
  e.preventDefault();
  const input = document.getElementById('wood-chatbot-input');
  const msg = input.value.trim();
  if (!msg) return;
  addWoodChatbotMsg('user', msg);
  input.value = '';
  setTimeout(()=>{
    addWoodChatbotMsg('bot', woodChatbotReply(msg));
  }, 400);
}
function addWoodChatbotMsg(sender, text) {
  const messages = document.getElementById('wood-chatbot-messages');
  const div = document.createElement('div');
  div.style.marginBottom = '10px';
  div.style.display = 'flex';
  div.style.justifyContent = sender==='user'?'flex-end':'flex-start';
  div.innerHTML = `<span style="background:${sender==='user'?'#b6864d':'#fff'};color:${sender==='user'?'#fff':'#8d5524'};padding:8px 14px;border-radius:14px;max-width:80%;display:inline-block;">${text}</span>`;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}
function woodChatbotReply(msg) {
  msg = msg.toLowerCase();
  if (msg.includes('recommend') || msg.includes('suggest')) {
    return 'Our bestsellers: Oak Chair, Teak Table, Walnut Shelf, Premium Bed. Want details or prices?';
  }
  if (msg.includes('order') && msg.includes('track')) {
    return 'Track your order live in the Orders section. Need help with a specific order?';
  }
  if (msg.includes('hello') || msg.includes('hi') || msg.includes('hey')) {
    return 'Hello! 👋 I’m Wood AI. Ask me about products, delivery, returns, or anything wood!';
  }
  if (msg.includes('return')) {
    return 'Returns accepted within 7 days. Need help with a return or refund?';
  }
  if (msg.includes('price') || msg.includes('cost')) {
    return 'Prices are listed on each product. Looking for a specific item or price range?';
  }
  if (msg.includes('delivery') || msg.includes('ship')) {
    return 'We deliver across India, fast and safe. Want premium delivery?';
  }
  if (msg.includes('thanks') || msg.includes('thank you')) {
    return 'You’re welcome! 😊 Anything else I can help with?';
  }
  if (msg.includes('bad') || msg.includes('angry') || msg.includes('upset') || msg.includes('problem')) {
    return 'Sorry to hear that. Can I help resolve your issue or connect you to support?';
  }
  if (msg.includes('good') || msg.includes('love') || msg.includes('great') || msg.includes('awesome')) {
    return 'Glad you love our products! Want recommendations or have feedback?';
  }
  if (msg.includes('contact') || msg.includes('support')) {
    return 'You can contact us via WhatsApp, Instagram, or the Contact page.';
  }
  if (msg.includes('faq')) {
    return 'Ask me anything about products, orders, returns, or delivery!';
  }
  return 'I’m Wood AI! Ask me about products, prices, delivery, returns, or anything else.';
}
</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''', featured_products=featured_products, is_logged_in=is_logged_in(), is_admin=is_admin())
# --- SHOP PAGE ---
@app.route('/shop')
def shop():
  conn = get_db()
  c = conn.cursor()
  category = request.args.get('category')
  search = request.args.get('search')
  sort = request.args.get('sort', 'newest')
  query = "SELECT * FROM products"
  params = []
  where = []
  if category:
    where.append("category=?")
    params.append(category)
  if search:
    where.append("(title LIKE ? OR description LIKE ?)")
    params.extend([f'%{search}%', f'%{search}%'])
  if where:
    query += " WHERE " + " AND ".join(where)
  # Sorting
  if sort == 'price_asc':
    query += " ORDER BY price ASC"
  elif sort == 'price_desc':
    query += " ORDER BY price DESC"
  elif sort == 'title_asc':
    query += " ORDER BY title ASC"
  elif sort == 'title_desc':
    query += " ORDER BY title DESC"
  else:
    query += " ORDER BY id DESC"
  c.execute(query, tuple(params))
  products = c.fetchall()
  conn.close()
  return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Shop - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      /* 3D effect for the whole page */
      body {
        background: linear-gradient(120deg, #2d1a0b 0%, #4b2e13 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .container, .product-card, .order-section, .footer, .navbar, .category-tile, .product-highlight, .product-specific {
        box-shadow: 0 8px 32px 0 rgba(70,42,15,0.22), 0 1.5px 8px 0 rgba(70,42,15,0.12);
        transform: translateZ(0px) scale(1.01) rotateX(1deg) rotateY(-1deg);
        border-radius: 12px;
      }
      .container:hover, .product-card:hover, .category-tile:hover {
        transform: scale(1.03) rotateX(3deg) rotateY(-3deg);
        box-shadow: 0 16px 48px 0 rgba(70,42,15,0.32);
      }
      h2, h1, .fw-bold, .display-4 {
        color: #fff !important;
      }
      /* Heart icon for wishlist shortcut */
      .wishlist-heart {
        position: absolute;
        top: 12px;
        right: 18px;
        font-size: 2rem;
        color: #ff4d4d;
        background: rgba(44,27,13,0.7);
        border-radius: 50%;
        padding: 6px;
        cursor: pointer;
        z-index: 10;
        transition: color 0.2s;
      }
      .wishlist-heart:hover {
        color: #fff;
      }
      .back-tab {
        position: absolute;
        top: 18px;
        left: 18px;
        z-index: 100;
        background: #b6864d;
        color: #fff;
        border-radius: 8px;
        padding: 6px 18px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 2px 8px #0002;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .back-tab:hover {
        background: #a67c52;
      }
    </style>
    </head>
    <body>
      {% if request.path != '/' %}
      <a href="javascript:history.back()" class="back-tab"><i class="bi bi-arrow-left"></i> Back</a>
      {% endif %}
    <div class="container py-5">
      <h2 class="text-center fw-bold mb-3">Shop</h2>
      <form class="mb-3 row g-2" method="get">
        <div class="col-md-4">
          <input type="text" name="search" class="form-control" placeholder="Search products..." value="{{request.args.get('search','')}}">
        </div>
        <div class="col-md-3">
          <select name="category" class="form-select" onchange="this.form.submit()">
            <option value="">All Categories</option>
            {% for cat in ['Chairs','Tables','Shelves','Beds'] %}
              <option value="{{cat}}" {% if request.args.get('category')==cat %}selected{% endif %}>{{cat}}</option>
            {% endfor %}
          </select>
        </div>
        <div class="col-md-3">
          <select name="sort" class="form-select" onchange="this.form.submit()">
            <option value="newest" {% if request.args.get('sort','newest')=='newest' %}selected{% endif %}>Newest</option>
            <option value="price_asc" {% if request.args.get('sort')=='price_asc' %}selected{% endif %}>Price: Low to High</option>
            <option value="price_desc" {% if request.args.get('sort')=='price_desc' %}selected{% endif %}>Price: High to Low</option>
            <option value="title_asc" {% if request.args.get('sort')=='title_asc' %}selected{% endif %}>Title: A-Z</option>
            <option value="title_desc" {% if request.args.get('sort')=='title_desc' %}selected{% endif %}>Title: Z-A</option>
          </select>
        </div>
        <div class="col-md-2">
          <button class="btn btn-3d w-100">Apply</button>
        </div>
      </form>
      <div class="row">
        {% for p in products %}
          <div class="col-6 col-md-3 mb-4">
            <div class="product-card h-100 position-relative">
              <a href="/wishlist/add/{{p['id']}}" class="wishlist-heart" title="Add to Wishlist">
                <i class="bi bi-heart-fill"></i>
              </a>
              <img src="{{p['image_url']}}" class="w-100" style="height:140px;object-fit:cover;">
              <div class="p-2">
                <div class="fw-bold">{{p['title']}}</div>
                <div class="text-muted">{{p['category']}}</div>
                <div class="price">₹{{p['price']}}</div>
                <a href="/product/{{p['id']}}" class="btn btn-3d mt-1 w-100">View</a>
              </div>
            </div>
          </div>
        {% endfor %}
      </div>
    </div>
    <!-- Wood AI Chatbot Styles -->
    <style>
      #woodai-bubble {
        position: fixed; bottom: 24px; right: 24px; z-index: 9999;
        width: 64px; height: 64px; background: #e0c095; border-radius: 50%;
        box-shadow: 0 4px 24px #a67c52a0;
        display:flex;align-items:center;justify-content:center;cursor:pointer;
        transition: box-shadow .15s;
      }
      #woodai-bubble:hover {box-shadow:0 8px 32px #a67c52c0;}
      #woodai-popup {
        display: none;position:fixed;bottom:100px;right:32px;z-index:9999;
        background:#fffbea;border-radius:18px;box-shadow:0 8px 32px #a67c52c0;
        padding:26px 18px;width:320px;max-width:94vw;
      }
      #woodai-popup.active {display:block;}
      .woodai-title {font-weight:bold;font-size:18px;margin-bottom:8px;}
      .woodai-msg {margin-bottom:8px;}
    </style>
    <!-- Wood AI Chatbot Bubble -->
    <div id="woodai-bubble" title="Chat with Wood AI">
      <img src="https://img.icons8.com/ios-filled/50/388e3c/chat.png" alt="Wood AI" style="width:36px;">
    </div>
    <div id="woodai-popup">
      <div class="woodai-title">Wood AI - Shopping Chatbot</div>
      <div id="woodai-chat" style="max-height:180px;overflow-y:auto;font-size:15px;"></div>
      <form id="woodai-form" autocomplete="off">
        <input type="text" id="woodai-input" class="form-control mb-2" placeholder="Ask about products, orders..." required>
        <button class="btn btn-3d w-100" type="submit">Send</button>
      </form>
    </div>
    <script>
      // Wood AI Chatbot logic
      const bubble = document.getElementById('woodai-bubble');
      const popup = document.getElementById('woodai-popup');
      const chat = document.getElementById('woodai-chat');
      const form = document.getElementById('woodai-form');
      const input = document.getElementById('woodai-input');
      bubble.onclick = () => popup.classList.toggle('active');
      form.onsubmit = (e) => {
        e.preventDefault();
        const userMsg = input.value.trim();
        if (!userMsg) return;
        chat.innerHTML += `<div class='woodai-msg'><b>You:</b> ${userMsg}</div>`;
        input.value = '';
        // Simple bot response (placeholder)
        let botMsg = "I'm Wood AI! How can I help you with shopping today?";
        if (/order|track/i.test(userMsg)) botMsg = "To track your order, use the order tracking section on the homepage.";
        else if (/price|cost/i.test(userMsg)) botMsg = "You can sort and filter products by price in the shop section.";
        else if (/category|type/i.test(userMsg)) botMsg = "We offer Chairs, Tables, Shelves, and Beds. What are you looking for?";
        else if (/wishlist/i.test(userMsg)) botMsg = "Add products to your wishlist for easy access later.";
        chat.innerHTML += `<div class='woodai-msg'><b>Wood AI:</b> ${botMsg}</div>`;
        chat.scrollTop = chat.scrollHeight;
      };
    </script>
    </body></html>
    ''', products=products)

# --- PRODUCT DETAIL PAGE ---
@app.route('/product/<int:pid>')
def product_detail(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (pid,))
    product = c.fetchone()
    # Recommendation system (simple: show 4 random products from same category)
    recommendations = []
    if product:
        c.execute("SELECT * FROM products WHERE category=? AND id!=? ORDER BY RANDOM() LIMIT 4", (product['category'], pid))
        recommendations = c.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>{{product['title']}} - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      /* 3D effect for the whole page */
      body {
        background: linear-gradient(120deg, #2d1a0b 0%, #4b2e13 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .container, .product-card, .order-section, .footer, .navbar, .category-tile, .product-highlight, .product-specific {
        box-shadow: 0 8px 32px 0 rgba(70,42,15,0.22), 0 1.5px 8px 0 rgba(70,42,15,0.12);
        transform: translateZ(0px) scale(1.01) rotateX(1deg) rotateY(-1deg);
        border-radius: 12px;
      }
      .container:hover, .product-card:hover, .category-tile:hover {
        transform: scale(1.03) rotateX(3deg) rotateY(-3deg);
        box-shadow: 0 16px 48px 0 rgba(70,42,15,0.32);
      }
      h2, h1, .fw-bold, .display-4 {
        color: #fff !important;
      }
      /* Heart icon for wishlist shortcut */
      .wishlist-heart {
        position: absolute;
        top: 12px;
        right: 18px;
        font-size: 2rem;
        color: #ff4d4d;
        background: rgba(44,27,13,0.7);
        border-radius: 50%;
        padding: 6px;
        cursor: pointer;
        z-index: 10;
        transition: color 0.2s;
      }
      .wishlist-heart:hover {
        color: #fff;
      }
      .back-tab {
        position: absolute;
        top: 18px;
        left: 18px;
        z-index: 100;
        background: #b6864d;
        color: #fff;
        border-radius: 8px;
        padding: 6px 18px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 2px 8px #0002;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .back-tab:hover {
        background: #a67c52;
      }
    </style>
    </head><body>
      {% if request.path != '/' %}
      <a href="javascript:history.back()" class="back-tab"><i class="bi bi-arrow-left"></i> Back</a>
      {% endif %}
    <div class="container py-5">
      <div class="row">
        <div class="col-md-6">
          <img src="{{product['image_url']}}" class="w-100" style="height:320px;object-fit:cover;border-radius:16px;">
        </div>
        <div class="col-md-6">
          <h2 class="fw-bold" style="color:#fff;">{{product['title']}}</h2>
          <div class="text-muted">{{product['category']}}</div>
          <div class="price">₹{{product['price']}}</div>
          <div class="mb-3">{{product['description']}}</div>
          <form method="post" action="/cart/add">
            <input type="hidden" name="pid" value="{{product['id']}}">
            <button class="btn btn-3d">Add to Cart</button>
          </form>
        </div>
      </div>
      <!-- Recommendation Section -->
      <div class="mt-5">
        <h4 class="fw-bold" style="color:#fff;">Recommended for You</h4>
        <div class="row">
          {% for rec in recommendations %}
            <div class="col-6 col-md-3 mb-3">
              <div class="product-card h-100">
                <img src="{{rec['image_url']}}" class="w-100" style="height:120px;object-fit:cover;">
                <div class="p-2">
                  <div class="fw-bold">{{rec['title']}}</div>
                  <div class="text-muted">{{rec['category']}}</div>
                  <div class="price">₹{{rec['price']}}</div>
                  <a href="/product/{{rec['id']}}" class="btn btn-3d mt-1 w-100">View</a>
                </div>
              </div>
            </div>
          {% endfor %}
        </div>
      </div>
      <!-- Policy Section -->
      <div class="mt-5">
        <h4 class="fw-bold" style="color:#fff;">Policies</h4>
        <ul class="list-group">
          <li class="list-group-item bg-dark text-white">Replacement Policy: Items can be replaced within 7 days of delivery if defective or damaged.</li>
          <li class="list-group-item bg-dark text-white">Return Policy: Returns are accepted within 7 days of delivery for unused items.</li>
          <li class="list-group-item bg-dark text-white">Delivery Policy: Premium 15-hour delivery available for select orders.</li>
        </ul>
      </div>
    </div>
    </body></html>
    ''', product=product, recommendations=recommendations)

@app.route('/product/<int:pid>/review', methods=['POST'])
def add_review(pid):
    if not is_logged_in():
        return redirect('/login')
    rating = int(request.form['rating'])
    comment = request.form['comment']
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO reviews (product_id, user_id, rating, comment, date) VALUES (?, ?, ?, ?, ?)",
              (pid, session['user_id'], rating, comment, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()
    flash('Review added!')
    return redirect(f'/product/{pid}')

# --- CART ---
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    if not cart:
        items = []
        total = 0
    else:
        conn = get_db()
        c = conn.cursor()
        items = []
        total = 0
        for pid, qty in cart.items():
            c.execute("SELECT * FROM products WHERE id=?", (pid,))
            p = c.fetchone()
            if p:
                p = dict(p)
                p['qty'] = qty
                p['subtotal'] = p['price'] * qty
                items.append(p)
                total += p['subtotal']
        conn.close()
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Cart - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      /* 3D effect for the whole page */
      body {
        background: linear-gradient(120deg, #2d1a0b 0%, #4b2e13 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .container, .product-card, .order-section, .footer, .navbar, .category-tile, .product-highlight, .product-specific {
        box-shadow: 0 8px 32px 0 rgba(70,42,15,0.22), 0 1.5px 8px 0 rgba(70,42,15,0.12);
        transform: translateZ(0px) scale(1.01) rotateX(1deg) rotateY(-1deg);
        border-radius: 12px;
      }
      .container:hover, .product-card:hover, .category-tile:hover {
        transform: scale(1.03) rotateX(3deg) rotateY(-3deg);
        box-shadow: 0 16px 48px 0 rgba(70,42,15,0.32);
      }
      h2, h1, .fw-bold, .display-4 {
        color: #fff !important;
      }
      /* Heart icon for wishlist shortcut */
      .wishlist-heart {
        position: absolute;
        top: 12px;
        right: 18px;
        font-size: 2rem;
        color: #ff4d4d;
        background: rgba(44,27,13,0.7);
        border-radius: 50%;
        padding: 6px;
        cursor: pointer;
        z-index: 10;
        transition: color 0.2s;
      }
      .wishlist-heart:hover {
        color: #fff;
      }
      .back-tab {
        position: absolute;
        top: 18px;
        left: 18px;
        z-index: 100;
        background: #b6864d;
        color: #fff;
        border-radius: 8px;
        padding: 6px 18px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 2px 8px #0002;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .back-tab:hover {
        background: #a67c52;
      }
    </style>
    </head><body>
      {% if request.path != '/' %}
      <a href="javascript:history.back()" class="back-tab"><i class="bi bi-arrow-left"></i> Back</a>
      {% endif %}
    <div class="container py-5">
      <h2 class="fw-bold mb-3">Your Cart</h2>
      {% if not items %}
        <div>No items in cart.</div>
      {% else %}
        <form method="post" action="/cart/update">
        <table class="table">
          <tr><th>Product</th><th>Qty</th><th>Price</th><th>Subtotal</th><th></th></tr>
          {% for p in items %}
            <tr>
              <td>{{p['title']}}</td>
              <td><input type="number" name="qty_{{p['id']}}" value="{{p['qty']}}" min="1" max="{{p['stock']}}" class="form-control" style="width:70px;"></td>
              <td>₹{{p['price']}}</td>
              <td>₹{{p['subtotal']}}</td>
              <td><a href="/cart/remove/{{p['id']}}" class="btn btn-sm btn-3d">Remove</a></td>
            </tr>
          {% endfor %}
        </table>
        <button class="btn btn-3d" type="submit">Update</button>
        </form>
        <div class="fw-bold">Total: ₹{{total}}</div>
        <a href="/checkout" class="btn btn-3d mt-3">Checkout (COD)</a>
      {% endif %}
    </div>
    </body></html>
    ''', items=items, total=total)

@app.route('/cart/add', methods=['POST'])
def cart_add():
  pid = str(request.form['pid'])
  cart = session.get('cart', {})
  cart[pid] = cart.get(pid, 0) + 1
  session['cart'] = cart
  return redirect('/cart')

@app.route('/cart/remove/<int:pid>')
def cart_remove(pid):
    cart = session.get('cart', {})
    if pid in cart:
        del cart[pid]
    session['cart'] = cart
    return redirect('/cart')

@app.route('/cart/update', methods=['POST'])
def cart_update():
    cart = session.get('cart', {})
    for pid in cart.keys():
        qty = int(request.form.get(f'qty_{pid}', 1))
        cart[pid] = qty
    session['cart'] = cart
    return redirect('/cart')

# --- CHECKOUT ---
@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if not is_logged_in():
        return redirect('/login')
    cart = session.get('cart', {})
    if not cart:
        return redirect('/cart')
    conn = get_db()
    c = conn.cursor()
    items = []
    total = 0
    for pid, qty in cart.items():
        c.execute("SELECT * FROM products WHERE id=?", (int(pid),))
        p = c.fetchone()
        if p:
            p = dict(p)
            p['qty'] = qty
            p['subtotal'] = p['price'] * qty
            items.append(p)
            total += p['subtotal']

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'COD')
        premium_delivery = request.form.get('premium_delivery') == 'on'
        delivery_fee = 0
        if premium_delivery:
            delivery_fee = 299  # Premium delivery fee
        grand_total = total + delivery_fee
        tracking_code = generate_tracking_code()
        order_items = json.dumps(cart)
        # Store payment method and premium delivery in status field for demo
        status = 'Pending'
        if premium_delivery:
            status += ' | Premium Delivery'
        c.execute(
            "INSERT INTO orders (user_id, items, total_amount, status, tracking_code, order_date, payment_method, premium_delivery) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(session['user_id']), order_items, grand_total, status, tracking_code, datetime.now().strftime('%Y-%m-%d %H:%M'), payment_method, int(premium_delivery))
        )
        conn.commit()
        session['cart'] = {}
        conn.close()
        flash(f'Order placed! Tracking code: {tracking_code}')
        return redirect('/orders')

    conn.close()
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Checkout - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      /* 3D effect for the whole page */
      body {
        background: linear-gradient(120deg, #2d1a0b 0%, #4b2e13 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .container, .product-card, .order-section, .footer, .navbar, .category-tile, .product-highlight, .product-specific {
        box-shadow: 0 8px 32px 0 rgba(70,42,15,0.22), 0 1.5px 8px 0 rgba(70,42,15,0.12);
        transform: translateZ(0px) scale(1.01) rotateX(1deg) rotateY(-1deg);
        border-radius: 12px;
      }
      .container:hover, .product-card:hover, .category-tile:hover {
        transform: scale(1.03) rotateX(3deg) rotateY(-3deg);
        box-shadow: 0 16px 48px 0 rgba(70,42,15,0.32);
      }
      h2, h1, .fw-bold, .display-4 {
        color: #fff !important;
      }
      /* Heart icon for wishlist shortcut */
      .wishlist-heart {
        position: absolute;
        top: 12px;
        right: 18px;
        font-size: 2rem;
        color: #ff4d4d;
        background: rgba(44,27,13,0.7);
        border-radius: 50%;
        padding: 6px;
        cursor: pointer;
        z-index: 10;
        transition: color 0.2s;
      }
      .wishlist-heart:hover {
        color: #fff;
      }
      .back-tab {
        position: absolute;
        top: 18px;
        left: 18px;
        z-index: 100;
        background: #b6864d;
        color: #fff;
        border-radius: 8px;
        padding: 6px 18px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 2px 8px #0002;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .back-tab:hover {
        background: #a67c52;
      }
    </style>
    </head><body>
      {% if request.path != '/' %}
      <a href="javascript:history.back()" class="back-tab"><i class="bi bi-arrow-left"></i> Back</a>
      {% endif %}
    <div class="container py-5">
      <h2 class="fw-bold mb-3">Checkout</h2>
      <div>Cash on Delivery only.</div>
      <table class="table">
        <tr><th>Product</th><th>Qty</th><th>Price</th><th>Subtotal</th></tr>
        {% for p in items %}
          <tr>
            <td>{{p['title']}}</td>
            <td>{{p['qty']}}</td>
            <td>₹{{p['price']}}</td>
            <td>₹{{p['subtotal']}}</td>
          </tr>
        {% endfor %}
      </table>
      <div class="fw-bold mb-3">Total: ₹{{total}}</div>
      <form method="post">
        <div class="mb-3">
          <label class="fw-bold">Payment Method:</label><br>
          <input type="radio" name="payment_method" value="COD" checked> Cash on Delivery
          <input type="radio" name="payment_method" value="Online" class="ms-3"> Online Payment (Demo)
        </div>
        <div class="mb-3">
          <label class="fw-bold">Premium Delivery:</label>
          <input type="checkbox" name="premium_delivery"> 15-Hour Delivery (+₹299)
        </div>
        <div class="fw-bold mb-3">Grand Total: ₹{{total}} <span id="premium-fee"></span></div>
        <button class="btn btn-3d" type="submit">Place Order</button>
      </form>
    </div>
    <script>
      // Update grand total on premium delivery toggle
      document.addEventListener('DOMContentLoaded', function() {
        const premiumCheckbox = document.querySelector('input[name="premium_delivery"]');
        const premiumFee = document.getElementById('premium-fee');
        const total = {{total}};
        function updateFee() {
          if (premiumCheckbox.checked) {
            premiumFee.textContent = ' + ₹299 = ₹' + (total+299);
          } else {
            premiumFee.textContent = '';
          }
        }
        if (premiumCheckbox) {
          premiumCheckbox.addEventListener('change', updateFee);
          updateFee();
        }
      });
    </script>
    </body></html>
    ''', items=items, total=total)

# --- ORDERS PAGE ---
@app.route('/orders')
def orders():
    if not is_logged_in():
        return redirect('/login')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY order_date DESC", (session['user_id'],))
    orders = c.fetchall()
    conn.close()
    status_colors = {'Pending':'#e0c095','Confirmed':'#f7c873','Packed':'#a67c52','Shipped':'#b6864d','Out for Delivery':'#e0c095','Delivered':'#339933'}
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Orders - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      /* 3D effect for the whole page */
      body {
        background: linear-gradient(120deg, #2d1a0b 0%, #4b2e13 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .container, .product-card, .order-section, .footer, .navbar, .category-tile, .product-highlight, .product-specific {
        box-shadow: 0 8px 32px 0 rgba(70,42,15,0.22), 0 1.5px 8px 0 rgba(70,42,15,0.12);
        transform: translateZ(0px) scale(1.01) rotateX(1deg) rotateY(-1deg);
        border-radius: 12px;
      }
      .container:hover, .product-card:hover, .category-tile:hover {
        transform: scale(1.03) rotateX(3deg) rotateY(-3deg);
        box-shadow: 0 16px 48px 0 rgba(70,42,15,0.32);
      }
      .order-section * {
        color: #fff !important;
      }
      .back-tab {
        position: absolute;
        top: 18px;
        left: 18px;
        z-index: 100;
        background: #b6864d;
        color: #fff;
        border-radius: 8px;
        padding: 6px 18px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 2px 8px #0002;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .back-tab:hover {
        background: #a67c52;
      }
    </style>
    </head><body>
      <a href="javascript:history.back()" class="back-tab"><i class="bi bi-arrow-left"></i> Back</a>
      <div class="container py-5 order-section">
        <h2 class="fw-bold mb-3">Your Orders</h2>
        {% for o in orders %}
          <div class="mb-4">
            <div class="fw-bold">Order #{{o['id']}}, Tracking: {{o['tracking_code']}}</div>
            <div>Date: {{o['order_date']}}</div>
            <div>Status: <span style="color:{{status_colors.get(o['status'].split(' |')[0],'#e0c095')}}">{{o['status']}}</span></div>
            <!-- Swiggy/Zepto-style stepper -->
            <div class="stepper">
              {% set steps = ['Pending','Confirmed','Packed','Shipped','Out for Delivery','Delivered'] %}
              {% set current = steps.index(o['status'].split(' |')[0]) if o['status'].split(' |')[0] in steps else 0 %}
              {% for step in steps %}
                <div class="step {% if loop.index0 < current %}completed{% elif loop.index0 == current %}active{% endif %}">
                  <span class="circle">{{loop.index}}</span><br>
                  <span>{{step}}</span>
                </div>
              {% endfor %}
            </div>
            {% if o['premium_delivery'] %}
              <div class="fw-bold text-success">Premium 15-Hour Delivery: <span id="delivery-eta-{{o['id']}}"></span></div>
              <script>
                // Calculate ETA from order_date
                (function(){
                  var orderDate = new Date("{{o['order_date']}}");
                  var eta = new Date(orderDate.getTime() + 15*60*60*1000);
                  var now = new Date();
                  var diff = eta-now;
                  var hours = Math.floor(diff/1000/60/60);
                  var mins = Math.floor((diff/1000/60)%60);
                  var etaStr = (hours>0?hours+"h ":"")+(mins>0?mins+"m":"0m");
                  document.getElementById("delivery-eta-{{o['id']}}")?.textContent = (diff>0?etaStr+" left":"Delivered");
                })();
              </script>
            {% endif %}
            <div>Total: ₹{{o['total_amount']}}</div>
          </div>
        {% endfor %}
      </div>
    </body></html>
    ''', orders=orders, status_colors=status_colors)

# --- WISHLIST PAGE ---
@app.route('/wishlist')
def wishlist():
    if not is_logged_in():
        return redirect('/login')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT w.id,p.* FROM wishlist w JOIN products p ON w.product_id=p.id WHERE w.user_id=?", (session['user_id'],))
    items = c.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Wishlist - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      /* 3D effect for the whole page */
      body {
        background: linear-gradient(120deg, #2d1a0b 0%, #4b2e13 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .container, .product-card, .order-section, .footer, .navbar, .category-tile, .product-highlight, .product-specific {
        box-shadow: 0 8px 32px 0 rgba(70,42,15,0.22), 0 1.5px 8px 0 rgba(70,42,15,0.12);
        transform: translateZ(0px) scale(1.01) rotateX(1deg) rotateY(-1deg);
        border-radius: 12px;
      }
      .container:hover, .product-card:hover, .category-tile:hover {
        transform: scale(1.03) rotateX(3deg) rotateY(-3deg);
        box-shadow: 0 16px 48px 0 rgba(70,42,15,0.32);
      }
      h2, h1, .fw-bold, .display-4 {
        color: #fff !important;
      }
      /* Heart icon for wishlist shortcut */
      .wishlist-heart {
        position: absolute;
        top: 12px;
        right: 18px;
        font-size: 2rem;
        color: #ff4d4d;
        background: rgba(44,27,13,0.7);
        border-radius: 50%;
        padding: 6px;
        cursor: pointer;
        z-index: 10;
        transition: color 0.2s;
      }
      .wishlist-heart:hover {
        color: #fff;
      }
      .back-tab {
        position: absolute;
        top: 18px;
        left: 18px;
        z-index: 100;
        background: #b6864d;
        color: #fff;
        border-radius: 8px;
        padding: 6px 18px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 2px 8px #0002;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .back-tab:hover {
        background: #a67c52;
      }
    </style>
    </head><body>
      {% if request.path != '/' %}
      <a href="javascript:history.back()" class="back-tab"><i class="bi bi-arrow-left"></i> Back</a>
      {% endif %}
    <div class="container py-5">
      <h2 class="fw-bold mb-3">Your Wishlist</h2>
      {% if not items %}
        <div>No items in wishlist.</div>
      {% else %}
        <div class="row">
          {% for p in items %}
            <div class="col-6 col-md-3 mb-4">
              <div class="product-card h-100">
                <img src="{{p['image_url']}}" class="w-100" style="height:140px;object-fit:cover;">
                <div class="p-2">
                  <div class="fw-bold">{{p['title']}}</div>
                  <div class="text-muted">{{p['category']}}</div>
                  <div class="fw-bold text-success">₹{{p['price']}}</div>
                  <form method="post" action="/cart/add">
                    <input type="hidden" name="pid" value="{{p['id']}}">
                    <button class="btn btn-3d mt-2 w-100" type="submit">Add to Cart</button>
                  </form>
                </div>
              </div>
            </div>
          {% endfor %}
        </div>
      {% endif %}
    </div>
    </body></html>
    ''', items=items)

@app.route('/wishlist/add', methods=['POST'])
def wishlist_add():
    if not is_logged_in():
        return redirect('/login')
    pid = int(request.form['pid'])
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO wishlist (user_id, product_id) VALUES (?, ?)", (session['user_id'], pid))
    conn.commit()
    conn.close()
    flash('Added to wishlist!')
    return redirect(request.referrer or '/wishlist')

@app.route('/wishlist/add/<int:pid>')
def wishlist_add_item(pid):
  if not is_logged_in():
    return redirect('/login')
  conn = get_db()
  c = conn.cursor()
  c.execute("INSERT OR IGNORE INTO wishlist (user_id, product_id) VALUES (?, ?)", (session['user_id'], pid))
  conn.commit()
  conn.close()
  flash('Added to wishlist!')
  return redirect(request.referrer or '/wishlist')

# --- AUTH ---
@app.route('/login', methods=['GET','POST'])
def login():
    tab = request.args.get('tab', 'customer')
    error = None
    if request.method == 'POST':
        if tab == 'admin':
            email = request.form['email']
            password = hash_password(request.form['password'])
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=? AND password=? AND is_admin=1", (email, password))
            user = c.fetchone()
            conn.close()
            if user:
                session['user_id'] = user['id']
                session['is_admin'] = True
                return redirect('/admin')
            else:
                error = "Invalid admin credentials."
        else:
            email = request.form['email']
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            if not user:
                error = "User not found."
            else:
                otp = generate_otp()
                c.execute("UPDATE users SET otp=? WHERE id=?", (otp, user['id']))
                conn.commit()
                conn.close()
                flash(f"Your OTP is: {otp} (demo, should send by email/SMS)")
                session['pending_user'] = user['id']
                return redirect('/otp')
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Login - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      .login-card {margin:40px auto;max-width:420px;background:#fffbea;border-radius:18px;box-shadow:0 4px 32px #a67c52a0;padding:40px;}
      .btn-3d {box-shadow:0 4px 0 0 #b6864d;border:none;background:linear-gradient(90deg,#a67c52 70%,#e0c095 100%);color:#fff;font-weight:bold;border-radius:8px;}
      .btn-3d:active {box-shadow:0 1px 0 0 #b6864d;transform:scale(.98);}
      .nav-tabs .nav-link.active {background:#e0c095;color:#fff;}
      h2, h1, .fw-bold, .display-4 {
        color: #fff !important;
      }
    </style>
    </head>
    <body>
    <div class="login-card">
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item">
          <a class="nav-link {% if tab=='customer' %}active{% endif %}" href="/login?tab=customer">Customer Login</a>
        </li>
        <li class="nav-item">
          <a class="nav-link {% if tab=='admin' %}active{% endif %}" href="/login?tab=admin">Admin Login</a>
        </li>
      </ul>
      {% if error %}<div class="alert alert-danger">{{error}}</div>{% endif %}
      {% if tab=='admin' %}
        <form method="post">
          <div class="mb-3">
            <input type="email" name="email" placeholder="Admin Email" class="form-control" required>
          </div>
          <div class="mb-3">
            <input type="password" name="password" placeholder="Password" class="form-control" required>
          </div>
          <button class="btn btn-3d w-100" type="submit">Login as Admin</button>
        </form>
      {% else %}
        <form method="post">
          <div class="mb-3">
            <input type="email" name="email" placeholder="Email" class="form-control" required>
          </div>
          <div class="mb-3">
            <input type="password" name="password" placeholder="Password (optional)" class="form-control">
          </div>
          <div class="mb-3">
            <input type="text" name="otp" placeholder="OTP (optional)" class="form-control">
            <small class="text-muted">You can log in with password or OTP. OTP is optional.</small>
            <button type="button" class="btn btn-secondary mt-2 w-100" onclick="alert('OTP sent to your email (demo only)')">Send OTP</button>
          </div>
          <button class="btn btn-3d w-100" type="submit">Login</button>
        </form>
        <div class="mt-3 text-center">
          <a href="/signup">New user? Signup here</a>
        </div>
      {% endif %}
    </div>
    </body></html>
  ''', error=error, tab=request.args.get('tab', 'customer'))


# --- SIGNUP ---
@app.route('/signup', methods=['GET','POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hash_password(request.form['password'])
        conn = get_db()
        c = conn.cursor()
    else:
      email = request.form['email']
      password = request.form.get('password')
      otp = request.form.get('otp')
      conn = get_db()
      c = conn.cursor()
      user = None
      if password:
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hash_password(password)))
        user = c.fetchone()
      elif otp:
        # Demo: accept any non-empty OTP
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
      conn.close()
      if user:
        session['user_id'] = user['id']
        session['is_admin'] = False
        return redirect('/')
      else:
        error = "Invalid credentials."

@app.route('/otp', methods=['GET','POST'])
def otp():
    error = None
    if request.method == 'POST':
        otp = request.form['otp']
        user_id = session.get('pending_user')
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=? AND otp=?", (user_id, otp))
        user = c.fetchone()
        if user:
            session['user_id'] = user['id']
            session['is_admin'] = bool(user['is_admin']);
            c.execute("UPDATE users SET verified=1, otp=NULL WHERE id=?", (user['id'],))
            conn.commit()
            conn.close()
            session.pop('pending_user', None)
            return redirect('/')
        else:
            error = "Incorrect OTP."
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>OTP Login - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.login-card {margin:40px auto;max-width:420px;background:#fffbea;border-radius:18px;box-shadow:0 4px 32px #a67c52a0;padding:40px;}.btn-3d {box-shadow:0 4px 0 0 #b6864d;border:none;background:linear-gradient(90deg,#a67c52 70%,#e0c095 100%);color:#fff;font-weight:bold;border-radius:8px;}.btn-3d:active {box-shadow:0 1px 0 0 #b6864d;transform:scale(.98);}</style>
    </head><body>
    <div class="login-card">
      <h4 class="fw-bold mb-3">OTP Login</h4>
      {% if error %}<div class="alert alert-danger">{{error}}</div>{% endif %}
      <form method="post">
        <div class="mb-3">
          <input type="text" name="otp" placeholder="Enter OTP" class="form-control" required>
        </div>
        <button class="btn btn-3d w-100" type="submit">Verify OTP</button>
      </form>
    </div>
    </body></html>
    ''', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- CONTACT PAGE ---
@app.route('/contact')
def contact():
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Contact - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body>
    <div class="container py-5">
      <h2 class="fw-bold mb-3">Contact Us</h2>
      <form>
        <div class="mb-3"><input type="text" class="form-control" placeholder="Name" required></div>
        <div class="mb-3"><input type="email" class="form-control" placeholder="Email" required></div>
        <div class="mb-3"><textarea class="form-control" placeholder="Message" required></textarea></div>
        <button class="btn btn-3d" type="submit">Send</button>
      </form>
      <div class="mt-5">
        <div class="fw-bold">WhatsApp: <a href="https://wa.me/919999999999">+91 99999 99999</a></div>
        <div class="mt-3">
          <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d14680.7940476318!2d77.5946!3d12.9716!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bae1670a1c4d6cf%3A0x4a8e8f5a8f1a1d2e!2sBangalore%2C%20India!5e0!3m2!1sen!2sin!4v1645708518439!5m2!1sen!2sin"
            width="100%" height="220" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
        </div>
      </div>
    </div>
    </body></html>
    ''')

# --- ADMIN PANEL ---
@app.route('/admin')
def admin():
    if not is_admin():
        return redirect('/login?tab=admin')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders")
    orders_count = c.fetchone()[0]
    c.execute("SELECT SUM(total_amount) FROM orders")
    revenue = c.fetchone()[0] or 0
    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()
    c.execute("SELECT * FROM orders ORDER BY order_date DESC LIMIT 10")
    orders = c.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html><html lang="en"><head>
    <title>Admin Panel - Classical Wood Express</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      /* 3D effect for the whole page */
      body {
        background: linear-gradient(120deg, #2d1a0b 0%, #4b2e13 100%);
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        min-height: 100vh;
        perspective: 1200px;
        overflow-x: hidden;
      }
      .container, .product-card, .order-section, .footer, .navbar, .category-tile, .product-highlight, .product-specific {
        box-shadow: 0 8px 32px 0 rgba(70,42,15,0.22), 0 1.5px 8px 0 rgba(70,42,15,0.12);
        transform: translateZ(0px) scale(1.01) rotateX(1deg) rotateY(-1deg);
        border-radius: 12px;
      }
      .container:hover, .product-card:hover, .category-tile:hover {
        transform: scale(1.03) rotateX(3deg) rotateY(-3deg);
        box-shadow: 0 16px 48px 0 rgba(70,42,15,0.32);
      }
      h2, h1, .fw-bold, .display-4 {
        color: #fff !important;
      }
      .back-tab {
        position: absolute;
        top: 18px;
        left: 18px;
        z-index: 100;
        background: #b6864d;
        color: #fff;
        border-radius: 8px;
        padding: 6px 18px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 2px 8px #0002;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .back-tab:hover {
        background: #a67c52;
      }
    </style>
    </head><body>
    <a href="javascript:history.back()" class="back-tab"><i class="bi bi-arrow-left"></i> Back</a>
    <div class="container py-5">
      <h2 class="fw-bold mb-3">Admin Dashboard</h2>
      <div class="row mb-4">
        <div class="col-md-3"><div class="bg-warning rounded p-3 text-center">Users<br><span class="fw-bold">{{users_count}}</span></div></div>
        <div class="col-md-3"><div class="bg-success rounded p-3 text-center">Orders<br><span class="fw-bold">{{orders_count}}</span></div></div>
        <div class="col-md-3"><div class="bg-info rounded p-3 text-center">Revenue<br><span class="fw-bold">₹{{revenue}}</span></div></div>
      </div>
      <h4 class="mb-2">Manage Products</h4>
      <a href="/admin/product/add" class="btn btn-3d mb-2">Add Product</a>
      <table class="table table-bordered">
        <tr><th>Title</th><th>Category</th><th>Price</th><th>Stock</th><th>Actions</th></tr>
        {% for p in products %}
          <tr>
            <td>{{p['title']}}</td>
            <td>{{p['category']}}</td>
            <td>₹{{p['price']}}</td>
            <td>{{p['stock']}}</td>
            <td>
              <a href="/admin/product/edit/{{p['id']}}" class="btn btn-sm btn-3d">Edit</a>
              <a href="/admin/product/delete/{{p['id']}}" class="btn btn-sm btn-danger">Delete</a>
            </td>
          </tr>
        {% endfor %}
      </table>
      <h4 class="mb-2 mt-4">Recent Orders</h4>
      <table class="table table-bordered">
        <tr><th>ID</th><th>User</th><th>Total</th><th>Status</th><th>Date</th><th>Actions</th></tr>
        {% for o in orders %}
          <tr>
            <td>{{o['id']}}</td>
            <td>{{o['user_id']}}</td>
            <td>₹{{o['total_amount']}}</td>
            <td>{{o['status']}}</td>
            <td>{{o['order_date']}}</td>
            <td>
              <a href="/admin/order/update/{{o['id']}}" class="btn btn-sm btn-3d">Update Status</a>
            </td>
          </tr>
        {% endfor %}
      </table>
    </div>
    </body></html>
    ''', users_count=users_count, orders_count=orders_count, revenue=revenue, products=products, orders=orders)

# --- ADMIN PRODUCT CRUD ---
@app.route('/admin/product/add', methods=['GET','POST'])
def admin_product_add():
    if not is_admin(): return redirect('/login?tab=admin')
    error = None
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        category = request.form['category']
        price = float(request.form['price'])
        image_url = request.form['image_url']
        stock = int(request.form['stock'])
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO products (title, description, category, price, image_url, stock) VALUES (?, ?, ?, ?, ?, ?)",
                  (title, desc, category, price, image_url, stock))
        conn.commit()
        conn.close()
        return redirect('/admin')
    return render_template_string('''
    <html><body>
    <div class="container py-5">
      <h4 class="mb-3">Add Product</h4>
      {% if error %}<div class="alert alert-danger">{{error}}</div>{%}
      <form method="post">
        <div class="mb-2"><input type="text" name="title" placeholder="Title" class="form-control" required></div>
        <div class="mb-2"><textarea name="description" placeholder="Description" class="form-control" required></div>
        <div class="mb-2">
          <select name="category" class="form-select" required>
            {% for cat in ['Chairs','Tables','Shelves','Beds'] %}
              <option value="{{cat}}">{{cat}}</option>
                       {% endfor %}
          </select>
        </div>
        <div class="mb-2"><input type="number" name="price" placeholder="Price" class="form-control" required></div>
        <div class="mb-2"><input type="url" name="image_url" placeholder="Image URL" class="form-control" required></div>
        <div class="mb-2"><input type="number" name="stock" placeholder="Stock" class="form-control" required></div>
        <button class="btn btn-3d" type="submit">Add</button>
      </form>
    </div>
    </body></html>
    ''', error=error)

@app.route('/admin/product/edit/<int:pid>', methods=['GET','POST'])
def admin_product_edit(pid):
    if not is_admin(): return redirect('/login?tab=admin')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (pid,))
    p = c.fetchone()
    if not p: return "Product not found."
    error = None
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        category = request.form['category']
        price = float(request.form['price'])
        image_url = request.form['image_url']
        stock = int(request.form['stock'])
        c.execute("UPDATE products SET title=?, description=?, category=?, price=?, image_url=?, stock=? WHERE id=?",
                  (title, desc, category, price, image_url, stock, pid))
        conn.commit()
        conn.close()
        return redirect('/admin')
    conn.close()
    return render_template_string('''
    <html><body>
    <div class="container py-5">
      <h4 class="mb-3">Edit Product</h4>
      {% if error %}<div class="alert alert-danger">{{error}}</div>{% endif %}
      <form method="post">
        <div class="mb-2"><input type="text" name="title" value="{{p['title']}}" class="form-control" required></div>
        <div class="mb-2"><textarea name="description" class="form-control" required>{{p['description']}}</textarea></div>
        <div class="mb-2">
          <select name="category" class="form-select" required>
            {% for cat in ['Chairs','Tables','Shelves','Beds'] %}
              <option value="{{cat}}" {% if p['category']==cat %}selected{% endif %}>{{cat}}</option>
            {% endfor %}
          </select>
        </div>
        <div class="mb-2"><input type="number" name="price" value="{{p['price']}}" class="form-control" required></div>
        <div class="mb-2"><input type="url" name="image_url" value="{{p['image_url']}}" class="form-control" required></div>
        <div class="mb-2"><input type="number" name="stock" value="{{p['stock']}}" class="form-control" required></div>
        <button class="btn btn-3d" type="submit">Update</button>
      </form>
    </div>
    </body></html>
    ''', p=p, error=error)

@app.route('/admin/product/delete/<int:pid>')
def admin_product_delete(pid):
    if not is_admin(): return redirect('/login?tab=admin')
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/admin/order/update/<int:oid>', methods=['GET','POST'])
def admin_order_update(oid):
    if not is_admin(): return redirect('/login?tab=admin')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id=?", (oid,))
    o = c.fetchone()
    if not o: return "Order not found."
    if request.method == 'POST':
        status = request.form['status']
        c.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
        conn.commit()
        conn.close()
        return redirect('/admin')
    conn.close()
    return render_template_string('''
    <html><body>
    <div class="container py-5">
      <h4 class="mb-3">Update Order Status</h4>
      <form method="post">
        <div class="mb-2">
          <select name="status" class="form-select">
            {% for s in ['Pending','Shipped','Out for Delivery','Delivered'] %}
              <option value="{{s}}" {% if o['status']==s %}selected{% endif %}>{{s}}</option>
            {% endfor %}
          </select>
        </div>
        <button class="btn btn-3d" type="submit">Update</button>
      </form>
    </div>
    </body></html>
    ''', o=o)

if __name__ == "__main__":
  print("\nWebsite running at: http://127.0.0.1:5000\n")
  app.run(debug=True)
