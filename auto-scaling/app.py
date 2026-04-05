from flask import Flask, jsonify, request, render_template_string, session
import mysql.connector
import os, time, hashlib, secrets

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# ── DB ────────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 3306)),
    "user":     os.environ.get("DB_USER", "admin"),
    "password": os.environ.get("DB_PASS", "password"),
    "database": os.environ.get("DB_NAME", "shopscale"),
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def current_user():
    return session.get("user_id"), session.get("user_name")

# ── HTML ──────────────────────────────────────────────────────────────────────
TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ShopScale</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{--bg:#F9F7F4;--surface:#fff;--text:#1A1814;--muted:#888580;--accent:#C8A96E;--accent-dk:#9B7D45;--border:#E8E4DE;--tag:#F1EDE6;--danger:#E24B4A;--success:#3B6D11}
    body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
    a{color:inherit;text-decoration:none}
    nav{background:var(--surface);border-bottom:1px solid var(--border);padding:0 2rem;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:200}
    .logo{font-family:'Playfair Display',serif;font-size:20px;font-weight:600;cursor:pointer}.logo span{color:var(--accent)}
    .nav-right{display:flex;align-items:center;gap:1rem;font-size:13px}
    .nav-btn{padding:6px 14px;border-radius:6px;border:1px solid var(--border);background:none;cursor:pointer;font-family:'DM Sans',sans-serif;font-size:13px;color:var(--text)}
    .nav-btn.primary{background:var(--text);color:#fff;border-color:var(--text)}
    .nav-btn:hover{opacity:.85}
    .cart-btn{position:relative}.cart-count{position:absolute;top:-6px;right:-8px;background:var(--accent);color:#fff;border-radius:50%;width:18px;height:18px;font-size:10px;display:flex;align-items:center;justify-content:center;font-weight:600}
    .instance-badge{font-family:monospace;font-size:11px;background:var(--tag);color:var(--accent-dk);padding:2px 10px;border-radius:20px;border:1px solid #E0D5C5}
    .page{display:none;max-width:1200px;margin:0 auto;padding:2rem}
    .page.active{display:block}
    .hero{padding:3rem 0 1.5rem;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:1rem}
    .hero h1{font-family:'Playfair Display',serif;font-size:38px;font-weight:400;line-height:1.2}.hero h1 em{color:var(--accent);font-style:italic}
    .hero p{color:var(--muted);font-size:14px;margin-top:8px}
    .stats-row{display:flex;gap:1.5rem}.stat{text-align:right}
    .stat-num{font-family:'Playfair Display',serif;font-size:26px}.stat-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em}
    .toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:1.5rem}
    .toolbar input{flex:1;min-width:200px;padding:10px 14px;border:1px solid var(--border);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:14px;background:var(--surface);outline:none}
    .toolbar input:focus{border-color:var(--accent)}
    .filter-btn{padding:5px 14px;border-radius:20px;border:1px solid var(--border);background:var(--surface);font-family:'DM Sans',sans-serif;font-size:12px;cursor:pointer;color:var(--text)}
    .filter-btn.active,.filter-btn:hover{background:var(--accent);border-color:var(--accent);color:#fff}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:20px}
    .card{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;cursor:pointer;transition:transform .2s}
    .card:hover{transform:translateY(-3px)}
    .card-img{height:180px;display:flex;align-items:center;justify-content:center;font-size:52px}
    .card-body{padding:14px 16px 18px}
    .cat-tag{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--accent-dk);background:var(--tag);padding:2px 8px;border-radius:20px;display:inline-block;margin-bottom:8px}
    .card-name{font-family:'Playfair Display',serif;font-size:16px;margin-bottom:4px;line-height:1.3}
    .card-desc{font-size:12px;color:var(--muted);line-height:1.5;margin-bottom:12px}
    .card-foot{display:flex;justify-content:space-between;align-items:center}
    .price{font-size:18px;font-weight:500}.stock{font-size:11px;color:var(--success)}.stock.low{color:var(--danger)}
    .stars{color:var(--accent);font-size:12px}
    .btn{padding:8px 18px;border-radius:7px;border:none;cursor:pointer;font-family:'DM Sans',sans-serif;font-size:13px;font-weight:500;transition:opacity .2s}
    .btn:hover{opacity:.85}
    .btn-dark{background:var(--text);color:#fff}
    .btn-accent{background:var(--accent);color:#fff}
    .btn-outline{background:none;border:1px solid var(--border);color:var(--text)}
    .btn-sm{padding:5px 12px;font-size:12px}
    .detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:3rem;margin-bottom:3rem}
    .detail-img{height:340px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:100px;border:1px solid var(--border)}
    .detail-info h2{font-family:'Playfair Display',serif;font-size:28px;margin-bottom:.5rem}
    .detail-price{font-size:28px;font-weight:500;margin:1rem 0}
    .detail-desc{color:var(--muted);font-size:14px;line-height:1.7;margin-bottom:1.5rem}
    .qty-row{display:flex;align-items:center;gap:12px;margin-bottom:1rem}
    .qty-btn{width:32px;height:32px;border-radius:6px;border:1px solid var(--border);background:none;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center}
    .qty-val{font-size:16px;font-weight:500;min-width:24px;text-align:center}
    .reviews-section{margin-top:3rem}
    .reviews-section h3{font-family:'Playfair Display',serif;font-size:22px;margin-bottom:1.5rem}
    .review-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:12px}
    .review-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
    .review-author{font-weight:500;font-size:14px}.review-date{font-size:12px;color:var(--muted)}
    .review-body{font-size:13px;color:var(--muted);line-height:1.6;margin-top:6px}
    .review-form{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:1.5rem}
    .review-form h4{font-size:15px;font-weight:500;margin-bottom:12px}
    .form-group{margin-bottom:12px}
    .form-group label{font-size:13px;color:var(--muted);display:block;margin-bottom:4px}
    .form-group input,.form-group textarea,.form-group select{width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:13px;outline:none;background:var(--surface);color:var(--text)}
    .form-group textarea{resize:vertical;min-height:80px}
    .cart-item{display:flex;align-items:center;gap:1rem;padding:16px 0;border-bottom:1px solid var(--border)}
    .cart-emoji{font-size:36px;width:60px;height:60px;background:var(--tag);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
    .cart-info{flex:1}.cart-name{font-weight:500;font-size:15px}.cart-cat{font-size:12px;color:var(--muted)}
    .cart-price{font-size:16px;font-weight:500}
    .cart-summary{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;margin-top:1.5rem}
    .summary-row{display:flex;justify-content:space-between;font-size:14px;padding:6px 0}
    .summary-row.total{font-size:18px;font-weight:600;border-top:1px solid var(--border);padding-top:12px;margin-top:6px}
    .checkout-grid{display:grid;grid-template-columns:1fr 380px;gap:2rem}
    .section-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:1rem}
    .section-card h3{font-size:15px;font-weight:600;margin-bottom:14px}
    .input-row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .order-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:12px}
    .order-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
    .order-id{font-family:monospace;font-size:13px;color:var(--muted)}
    .badge{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:.05em}
    .badge-pending{background:#FFF8E1;color:#854F0B}
    .badge-confirmed{background:#E6F1FB;color:#185FA5}
    .badge-shipped{background:#EAF3DE;color:#3B6D11}
    .badge-delivered{background:#E1F5EE;color:#0F6E56}
    .order-items{font-size:13px;color:var(--muted);margin-bottom:10px}
    .order-total{font-size:16px;font-weight:600}
    .timeline{margin-top:16px;padding-top:16px;border-top:1px solid var(--border)}
    .timeline-step{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}
    .timeline-dot{width:10px;height:10px;border-radius:50%;margin-top:4px;flex-shrink:0}
    .dot-done{background:var(--success)}.dot-active{background:var(--accent)}.dot-pending{background:var(--border)}
    .timeline-label{font-size:13px;font-weight:500}.timeline-time{font-size:11px;color:var(--muted)}
    .auth-wrap{max-width:420px;margin:4rem auto;padding:0 1rem}
    .auth-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:2rem}
    .auth-card h2{font-family:'Playfair Display',serif;font-size:24px;margin-bottom:1.5rem}
    .alert{padding:10px 16px;border-radius:7px;font-size:13px;margin-bottom:1rem}
    .alert-success{background:#EAF3DE;color:var(--success)}.alert-error{background:#FCEBEB;color:var(--danger)}
    .empty{text-align:center;padding:4rem;color:var(--muted)}.empty h3{font-family:'Playfair Display',serif;font-size:22px;margin-bottom:.5rem}
    .loading{text-align:center;padding:3rem;color:var(--muted)}
    footer{text-align:center;padding:2rem;font-size:12px;color:var(--muted);border-top:1px solid var(--border);margin-top:3rem}
    footer code{background:var(--tag);padding:2px 6px;border-radius:4px;font-size:11px}
    @media(max-width:700px){.detail-grid,.checkout-grid,.input-row{grid-template-columns:1fr}.hero{flex-direction:column;align-items:flex-start}.stats-row{justify-content:flex-start}}
  </style>
</head>
<body>

<nav>
  <div class="logo" onclick="showPage('home')">Shop<span>Scale</span></div>
  <div class="nav-right">
    <span class="instance-badge" id="instance-badge">loading...</span>
    <button class="nav-btn cart-btn" onclick="showPage('cart')">
      Cart <span class="cart-count" id="cart-count">0</span>
    </button>
    <div id="nav-auth" style="display:flex;gap:.5rem">
      <button class="nav-btn" onclick="showPage('login')">Login</button>
      <button class="nav-btn primary" onclick="showPage('register')">Register</button>
    </div>
    <div id="nav-user" style="display:none;align-items:center;gap:.5rem">
      <span id="nav-username" style="font-size:13px;color:var(--muted)"></span>
      <button class="nav-btn" onclick="showPage('orders')">Orders</button>
      <button class="nav-btn" onclick="logout()">Logout</button>
    </div>
  </div>
</nav>

<!-- HOME -->
<div class="page active" id="page-home">
  <div class="hero">
    <div>
      <h1>Curated <em>Products</em><br>Built to Scale</h1>
      <p>Production demo · Flask + RDS MySQL · AWS Autoscaling</p>
    </div>
    <div class="stats-row">
      <div class="stat"><div class="stat-num" id="stat-total">—</div><div class="stat-label">Products</div></div>
      <div class="stat"><div class="stat-num" id="stat-cats">—</div><div class="stat-label">Categories</div></div>
      <div class="stat"><div class="stat-num" id="stat-db">—</div><div class="stat-label">DB ms</div></div>
    </div>
  </div>
  <div class="toolbar">
    <input type="text" id="search" placeholder="Search products..." oninput="filterProducts()">
    <div id="filters" style="display:flex;gap:6px;flex-wrap:wrap">
      <button class="filter-btn active" onclick="setCategory('all',this)">All</button>
    </div>
  </div>
  <div class="grid" id="grid"><div class="loading">Loading from RDS...</div></div>
</div>

<!-- PRODUCT DETAIL -->
<div class="page" id="page-detail">
  <button class="btn btn-outline btn-sm" onclick="showPage('home')" style="margin-bottom:1.5rem">← Back</button>
  <div class="detail-grid" id="detail-content"></div>
  <div class="reviews-section" id="reviews-section"></div>
</div>

<!-- CART -->
<div class="page" id="page-cart">
  <h2 style="font-family:'Playfair Display',serif;font-size:28px;margin-bottom:1.5rem">Your cart</h2>
  <div id="cart-content"></div>
</div>

<!-- CHECKOUT -->
<div class="page" id="page-checkout">
  <h2 style="font-family:'Playfair Display',serif;font-size:28px;margin-bottom:1.5rem">Checkout</h2>
  <div class="checkout-grid">
    <div>
      <div class="section-card">
        <h3>Shipping address</h3>
        <div class="form-group"><label>Full name</label><input id="co-name" placeholder="John Smith"></div>
        <div class="input-row">
          <div class="form-group"><label>Email</label><input id="co-email" placeholder="john@example.com"></div>
          <div class="form-group"><label>Phone</label><input id="co-phone" placeholder="+1 555 000 0000"></div>
        </div>
        <div class="form-group"><label>Address</label><input id="co-addr" placeholder="123 Main St"></div>
        <div class="input-row">
          <div class="form-group"><label>City</label><input id="co-city" placeholder="New York"></div>
          <div class="form-group"><label>Postal code</label><input id="co-zip" placeholder="10001"></div>
        </div>
      </div>
      <div class="section-card">
        <h3>Payment</h3>
        <div class="form-group"><label>Card number</label><input placeholder="4242 4242 4242 4242" maxlength="19"></div>
        <div class="input-row">
          <div class="form-group"><label>Expiry</label><input placeholder="MM/YY" maxlength="5"></div>
          <div class="form-group"><label>CVV</label><input placeholder="123" maxlength="3"></div>
        </div>
      </div>
    </div>
    <div>
      <div class="section-card" id="checkout-summary"></div>
      <button class="btn btn-accent" style="width:100%;padding:14px;font-size:15px;margin-top:.5rem" onclick="placeOrder()">Place order</button>
      <div id="checkout-alert" style="margin-top:.75rem"></div>
    </div>
  </div>
</div>

<!-- ORDERS -->
<div class="page" id="page-orders">
  <h2 style="font-family:'Playfair Display',serif;font-size:28px;margin-bottom:1.5rem">Your orders</h2>
  <div id="orders-content"></div>
</div>

<!-- LOGIN -->
<div class="page" id="page-login">
  <div class="auth-wrap">
    <div class="auth-card">
      <h2>Welcome back</h2>
      <div id="login-alert"></div>
      <div class="form-group"><label>Email</label><input id="login-email" type="email" placeholder="you@example.com"></div>
      <div class="form-group"><label>Password</label><input id="login-pw" type="password" placeholder="••••••••"></div>
      <button class="btn btn-dark" style="width:100%;padding:11px;margin-top:.5rem" onclick="login()">Login</button>
      <p style="text-align:center;font-size:13px;color:var(--muted);margin-top:1rem">No account? <a href="#" onclick="showPage('register')" style="color:var(--accent)">Register</a></p>
    </div>
  </div>
</div>

<!-- REGISTER -->
<div class="page" id="page-register">
  <div class="auth-wrap">
    <div class="auth-card">
      <h2>Create account</h2>
      <div id="register-alert"></div>
      <div class="form-group"><label>Full name</label><input id="reg-name" placeholder="John Smith"></div>
      <div class="form-group"><label>Email</label><input id="reg-email" type="email" placeholder="you@example.com"></div>
      <div class="form-group"><label>Password</label><input id="reg-pw" type="password" placeholder="min 6 characters"></div>
      <button class="btn btn-dark" style="width:100%;padding:11px;margin-top:.5rem" onclick="register()">Create account</button>
      <p style="text-align:center;font-size:13px;color:var(--muted);margin-top:1rem">Have an account? <a href="#" onclick="showPage('login')" style="color:var(--accent)">Login</a></p>
    </div>
  </div>
</div>

<footer>
  ShopScale &nbsp;·&nbsp; Instance: <code id="footer-instance">—</code> &nbsp;·&nbsp; Region: <code>us-east-1</code> &nbsp;·&nbsp; DB: <code>MySQL RDS</code>
</footer>

<script>
let allProducts=[], activeCategory='all';
let cart=JSON.parse(localStorage.getItem('cart')||'[]');
let currentUser=null;
const COLORS=['#FEF3E6','#E8F4FD','#EDF7ED','#FDE8F0','#F0EBF8','#FFF8E1','#E8F5E9','#FCE4EC'];

async function init(){updateCartCount();await checkSession();await loadProducts();}

function showPage(name){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  window.scrollTo(0,0);
  if(name==='cart')renderCart();
  if(name==='checkout')renderCheckoutSummary();
  if(name==='orders')loadOrders();
}

async function checkSession(){
  const res=await fetch('/api/me');const data=await res.json();
  if(data.user)setUser(data.user);
}
function setUser(user){
  currentUser=user;
  document.getElementById('nav-auth').style.display='none';
  document.getElementById('nav-user').style.display='flex';
  document.getElementById('nav-username').textContent=user.name;
}
function clearUser(){
  currentUser=null;
  document.getElementById('nav-auth').style.display='flex';
  document.getElementById('nav-user').style.display='none';
}
async function login(){
  const email=document.getElementById('login-email').value;
  const pw=document.getElementById('login-pw').value;
  const res=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password:pw})});
  const data=await res.json();
  if(data.error){showAlert('login-alert',data.error,'error');return;}
  setUser(data.user);showPage('home');
}
async function register(){
  const name=document.getElementById('reg-name').value;
  const email=document.getElementById('reg-email').value;
  const pw=document.getElementById('reg-pw').value;
  const res=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,email,password:pw})});
  const data=await res.json();
  if(data.error){showAlert('register-alert',data.error,'error');return;}
  setUser(data.user);showPage('home');
}
async function logout(){await fetch('/api/logout',{method:'POST'});clearUser();showPage('home');}

async function loadProducts(){
  const res=await fetch('/api/products');const data=await res.json();
  if(data.error){document.getElementById('grid').innerHTML='<div class="loading">DB not reachable</div>';return;}
  allProducts=data.products;
  document.getElementById('stat-total').textContent=data.total;
  document.getElementById('stat-cats').textContent=data.categories;
  document.getElementById('stat-db').textContent=data.db_ms+'ms';
  document.getElementById('instance-badge').textContent=data.instance_id;
  document.getElementById('footer-instance').textContent=data.instance_id;
  const cats=[...new Set(allProducts.map(p=>p.category))];
  const f=document.getElementById('filters');
  cats.forEach(cat=>{const b=document.createElement('button');b.className='filter-btn';b.textContent=cat;b.onclick=()=>setCategory(cat,b);f.appendChild(b);});
  renderGrid(allProducts);
}
function setCategory(cat,btn){activeCategory=cat;document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');filterProducts();}
function filterProducts(){
  const q=document.getElementById('search').value.toLowerCase();
  renderGrid(allProducts.filter(p=>(activeCategory==='all'||p.category===activeCategory)&&(!q||p.name.toLowerCase().includes(q)||p.description.toLowerCase().includes(q))));
}
function renderGrid(products){
  const grid=document.getElementById('grid');
  if(!products.length){grid.innerHTML='<div class="empty"><h3>No products found</h3><p>Try a different search</p></div>';return;}
  grid.innerHTML=products.map((p,i)=>`
    <div class="card" onclick="openProduct(${p.id})">
      <div class="card-img" style="background:${COLORS[i%COLORS.length]}">${p.emoji}</div>
      <div class="card-body">
        <span class="cat-tag">${p.category}</span>
        <div class="card-name">${p.name}</div>
        <div class="card-desc">${p.description.slice(0,80)}...</div>
        <div class="card-foot">
          <div><div class="price">$${p.price}</div><div class="stock ${p.stock<20?'low':''}">${p.stock<20?'Low stock: '+p.stock:'In stock: '+p.stock}</div></div>
          <div class="stars">${'★'.repeat(Math.round(p.avg_rating||4))}${'☆'.repeat(5-Math.round(p.avg_rating||4))} <span style="color:var(--muted)">(${p.review_count||0})</span></div>
        </div>
      </div>
    </div>`).join('');
}

async function openProduct(id){
  showPage('detail');
  const res=await fetch('/api/products/'+id);const p=await res.json();
  const rres=await fetch('/api/products/'+id+'/reviews');const rv=await rres.json();
  document.getElementById('detail-content').innerHTML=`
    <div><div class="detail-img" style="background:${COLORS[id%COLORS.length]}">${p.emoji}</div></div>
    <div class="detail-info">
      <span class="cat-tag">${p.category}</span>
      <h2>${p.name}</h2>
      <div class="stars" style="font-size:16px;margin:.5rem 0">${'★'.repeat(Math.round(p.avg_rating||4))}${'☆'.repeat(5-Math.round(p.avg_rating||4))} <span style="font-size:13px;color:var(--muted)">${p.review_count||0} reviews</span></div>
      <div class="detail-price">$${p.price}</div>
      <p class="detail-desc">${p.description}</p>
      <div class="qty-row">
        <button class="qty-btn" onclick="changeQty(-1)">−</button>
        <span class="qty-val" id="qty">1</span>
        <button class="qty-btn" onclick="changeQty(1)">+</button>
      </div>
      <button class="btn btn-dark" style="width:100%;padding:12px" onclick="addToCartFromDetail(${p.id},'${p.name.replace(/'/g,"\\'")}',${p.price},'${p.emoji}')">Add to cart</button>
      <div id="detail-alert" style="margin-top:.75rem"></div>
    </div>`;
  const canReview=currentUser!==null;
  document.getElementById('reviews-section').innerHTML=`
    <h3>Reviews</h3>
    ${canReview?`
    <div class="review-form">
      <h4>Write a review</h4>
      <div class="form-group"><label>Rating</label>
        <select id="rev-rating"><option value="5">★★★★★ Excellent</option><option value="4">★★★★☆ Good</option><option value="3">★★★☆☆ Average</option><option value="2">★★☆☆☆ Poor</option><option value="1">★☆☆☆☆ Terrible</option></select>
      </div>
      <div class="form-group"><label>Comment</label><textarea id="rev-comment" placeholder="Share your experience..."></textarea></div>
      <button class="btn btn-accent btn-sm" onclick="submitReview(${p.id})">Submit review</button>
      <div id="review-alert" style="margin-top:.5rem"></div>
    </div>`:`<p style="font-size:13px;color:var(--muted);margin-bottom:1.5rem"><a href="#" onclick="showPage('login')" style="color:var(--accent)">Login</a> to write a review</p>`}
    ${rv.reviews.length===0?'<p style="color:var(--muted);font-size:14px">No reviews yet. Be the first!</p>':
      rv.reviews.map(r=>`
      <div class="review-card">
        <div class="review-header">
          <span class="review-author">${r.user_name}</span>
          <div style="display:flex;align-items:center;gap:.5rem">
            <span class="stars">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</span>
            <span class="review-date">${r.created_at}</span>
          </div>
        </div>
        <div class="review-body">${r.comment}</div>
      </div>`).join('')}`;
}
function changeQty(d){const el=document.getElementById('qty');el.textContent=Math.max(1,parseInt(el.textContent)+d);}
function addToCartFromDetail(id,name,price,emoji){
  const qty=parseInt(document.getElementById('qty').textContent);
  addToCart(id,name,price,emoji,qty);
  showAlert('detail-alert',`${qty} × ${name} added to cart!`,'success');
}

function addToCart(id,name,price,emoji,qty=1){
  const existing=cart.find(i=>i.id===id);
  if(existing)existing.qty+=qty;else cart.push({id,name,price,emoji,qty});
  saveCart();
}
function saveCart(){localStorage.setItem('cart',JSON.stringify(cart));updateCartCount();}
function updateCartCount(){document.getElementById('cart-count').textContent=cart.reduce((s,i)=>s+i.qty,0);}

function renderCart(){
  const el=document.getElementById('cart-content');
  if(!cart.length){el.innerHTML='<div class="empty"><h3>Your cart is empty</h3><p>Browse products and add something!</p><br><button class="btn btn-dark" onclick="showPage(\'home\')">Browse products</button></div>';return;}
  const subtotal=cart.reduce((s,i)=>s+i.price*i.qty,0);
  const shipping=subtotal>100?0:9.99;const total=subtotal+shipping;
  el.innerHTML=`
    ${cart.map(item=>`
    <div class="cart-item">
      <div class="cart-emoji">${item.emoji}</div>
      <div class="cart-info">
        <div class="cart-name">${item.name}</div>
        <div style="display:flex;align-items:center;gap:8px;margin-top:6px">
          <button class="qty-btn" style="width:26px;height:26px;font-size:14px" onclick="cartQty(${item.id},-1)">−</button>
          <span style="font-size:14px;font-weight:500">${item.qty}</span>
          <button class="qty-btn" style="width:26px;height:26px;font-size:14px" onclick="cartQty(${item.id},1)">+</button>
          <button class="btn btn-sm btn-outline" style="color:var(--danger);border-color:var(--danger);margin-left:.5rem" onclick="removeFromCart(${item.id})">Remove</button>
        </div>
      </div>
      <div class="cart-price">$${(item.price*item.qty).toFixed(2)}</div>
    </div>`).join('')}
    <div class="cart-summary">
      <div class="summary-row"><span>Subtotal</span><span>$${subtotal.toFixed(2)}</span></div>
      <div class="summary-row"><span>Shipping</span><span>${shipping===0?'Free':'$'+shipping.toFixed(2)}</span></div>
      <div class="summary-row total"><span>Total</span><span>$${total.toFixed(2)}</span></div>
      <button class="btn btn-accent" style="width:100%;padding:12px;margin-top:1rem;font-size:14px" onclick="goCheckout()">Proceed to checkout</button>
    </div>`;
}
function cartQty(id,d){const item=cart.find(i=>i.id===id);if(!item)return;item.qty=Math.max(0,item.qty+d);if(item.qty===0)cart=cart.filter(i=>i.id!==id);saveCart();renderCart();}
function removeFromCart(id){cart=cart.filter(i=>i.id!==id);saveCart();renderCart();}
function goCheckout(){if(!currentUser){showPage('login');return;}showPage('checkout');}

function renderCheckoutSummary(){
  const subtotal=cart.reduce((s,i)=>s+i.price*i.qty,0);
  const shipping=subtotal>100?0:9.99;
  document.getElementById('checkout-summary').innerHTML=`
    <h3>Order summary</h3>
    ${cart.map(i=>`<div class="summary-row"><span>${i.name} ×${i.qty}</span><span>$${(i.price*i.qty).toFixed(2)}</span></div>`).join('')}
    <div class="summary-row"><span>Shipping</span><span>${shipping===0?'Free':'$'+shipping.toFixed(2)}</span></div>
    <div class="summary-row total"><span>Total</span><span>$${(subtotal+shipping).toFixed(2)}</span></div>`;
}
async function placeOrder(){
  const name=document.getElementById('co-name').value;
  const addr=document.getElementById('co-addr').value;
  const city=document.getElementById('co-city').value;
  if(!name||!addr||!city){showAlert('checkout-alert','Please fill in all shipping fields','error');return;}
  const subtotal=cart.reduce((s,i)=>s+i.price*i.qty,0);
  const shipping=subtotal>100?0:9.99;
  const res=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({items:cart,total:(subtotal+shipping).toFixed(2),shipping_address:`${name}, ${addr}, ${city}`})});
  const data=await res.json();
  if(data.error){showAlert('checkout-alert',data.error,'error');return;}
  cart=[];saveCart();showPage('orders');
}

async function loadOrders(){
  if(!currentUser){showPage('login');return;}
  const res=await fetch('/api/orders');const data=await res.json();
  const el=document.getElementById('orders-content');
  if(!data.orders.length){el.innerHTML='<div class="empty"><h3>No orders yet</h3><p>Place your first order!</p></div>';return;}
  const statusMap={pending:'badge-pending',confirmed:'badge-confirmed',shipped:'badge-shipped',delivered:'badge-delivered'};
  const steps=['Order placed','Confirmed','Shipped','Delivered'];
  el.innerHTML=data.orders.map(o=>{
    const statusIdx=['pending','confirmed','shipped','delivered'].indexOf(o.status);
    return `<div class="order-card">
      <div class="order-header">
        <div><div style="font-weight:600;font-size:15px;margin-bottom:3px">Order #${o.id}</div><div class="order-id">${o.created_at}</div></div>
        <span class="badge ${statusMap[o.status]||'badge-pending'}">${o.status}</span>
      </div>
      <div class="order-items">${o.items_summary}</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div class="order-total">$${o.total}</div>
        <div style="font-size:12px;color:var(--muted)">Ships to: ${o.shipping_address}</div>
      </div>
      <div class="timeline">
        ${steps.map((s,i)=>`
        <div class="timeline-step">
          <div class="timeline-dot ${i<statusIdx?'dot-done':i===statusIdx?'dot-active':'dot-pending'}"></div>
          <div><div class="timeline-label" style="color:${i<=statusIdx?'var(--text)':'var(--muted)'}">${s}</div>
          ${i<=statusIdx?`<div class="timeline-time">${o.created_at}</div>`:''}</div>
        </div>`).join('')}
      </div>
    </div>`;
  }).join('');
}

async function submitReview(productId){
  const rating=document.getElementById('rev-rating').value;
  const comment=document.getElementById('rev-comment').value;
  if(!comment.trim()){showAlert('review-alert','Please write a comment','error');return;}
  const res=await fetch(`/api/products/${productId}/reviews`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rating:parseInt(rating),comment})});
  const data=await res.json();
  if(data.error){showAlert('review-alert',data.error,'error');return;}
  openProduct(productId);
}

function showAlert(id,msg,type){
  const el=document.getElementById(id);if(!el)return;
  el.innerHTML=`<div class="alert alert-${type}">${msg}</div>`;
  setTimeout(()=>{el.innerHTML='';},4000);
}

init();
</script>
</body>
</html>
"""

# ── HELPERS ───────────────────────────────────────────────────────────────────
def ok(data):             return jsonify(data)
def err(msg, code=400):   return jsonify({"error": msg}), code

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/health")
def health():
    try:
        db = get_db(); db.close()
        return ok({"status": "healthy", "db": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "db": str(e)}), 500

# AUTH
@app.route("/api/register", methods=["POST"])
def register():
    d = request.get_json()
    name, email, pw = d.get("name",""), d.get("email",""), d.get("password","")
    if not name or not email or not pw: return err("All fields required")
    if len(pw) < 6: return err("Password must be at least 6 characters")
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone(): cur.close(); db.close(); return err("Email already registered")
    cur.execute("INSERT INTO users (name, email, password_hash) VALUES (%s,%s,%s)",
                (name, email, hash_password(pw)))
    db.commit(); uid = cur.lastrowid; cur.close(); db.close()
    session["user_id"] = uid; session["user_name"] = name
    return ok({"user": {"id": uid, "name": name, "email": email}})

@app.route("/api/login", methods=["POST"])
def login():
    d = request.get_json()
    email, pw = d.get("email",""), d.get("password","")
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s AND password_hash=%s",
                (email, hash_password(pw)))
    user = cur.fetchone(); cur.close(); db.close()
    if not user: return err("Invalid email or password")
    session["user_id"] = user["id"]; session["user_name"] = user["name"]
    return ok({"user": {"id": user["id"], "name": user["name"], "email": user["email"]}})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear(); return ok({"status": "logged out"})

@app.route("/api/me")
def me():
    uid, _ = current_user()
    if not uid: return ok({"user": None})
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name, email FROM users WHERE id=%s", (uid,))
    user = cur.fetchone(); cur.close(); db.close()
    return ok({"user": user})

# PRODUCTS
@app.route("/api/products")
def products():
    t0 = time.time()
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT p.id, p.name, p.description, p.price, p.stock, p.emoji,
               c.name AS category,
               ROUND(COALESCE(AVG(r.rating),0),1) AS avg_rating,
               COUNT(r.id) AS review_count
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN reviews r ON r.product_id = p.id
        GROUP BY p.id, c.name
        ORDER BY p.created_at DESC
    """)
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(DISTINCT id) AS cnt FROM categories")
    cats = cur.fetchone()["cnt"]; cur.close(); db.close()
    return ok({"products": rows, "total": len(rows), "categories": cats,
               "db_ms": round((time.time()-t0)*1000),
               "instance_id": os.environ.get("INSTANCE_ID","i-local")})

@app.route("/api/products/<int:pid>")
def product_detail(pid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, c.name AS category,
               ROUND(COALESCE(AVG(r.rating),0),1) AS avg_rating,
               COUNT(r.id) AS review_count
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN reviews r ON r.product_id = p.id
        WHERE p.id=%s GROUP BY p.id, c.name
    """, (pid,))
    row = cur.fetchone(); cur.close(); db.close()
    if not row: return err("Not found", 404)
    return ok(row)

@app.route("/api/search")
def search():
    q = request.args.get("q","")
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT p.id, p.name, p.price, p.emoji, c.name AS category
        FROM products p JOIN categories c ON p.category_id = c.id
        WHERE p.name LIKE %s OR p.description LIKE %s LIMIT 20
    """, (f"%{q}%", f"%{q}%"))
    rows = cur.fetchall(); cur.close(); db.close()
    return ok({"results": rows})

# REVIEWS
@app.route("/api/products/<int:pid>/reviews", methods=["GET"])
def get_reviews(pid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT r.id, r.rating, r.comment, u.name AS user_name,
               DATE_FORMAT(r.created_at, '%%b %%d, %%Y') AS created_at
        FROM reviews r JOIN users u ON r.user_id = u.id
        WHERE r.product_id=%s ORDER BY r.created_at DESC
    """, (pid,))
    rows = cur.fetchall(); cur.close(); db.close()
    return ok({"reviews": rows})

@app.route("/api/products/<int:pid>/reviews", methods=["POST"])
def add_review(pid):
    uid, _ = current_user()
    if not uid: return err("Login required", 401)
    d = request.get_json()
    rating, comment = d.get("rating",5), d.get("comment","").strip()
    if not comment: return err("Comment required")
    if not 1 <= rating <= 5: return err("Rating must be 1-5")
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id FROM reviews WHERE user_id=%s AND product_id=%s", (uid, pid))
    if cur.fetchone():
        cur.execute("UPDATE reviews SET rating=%s, comment=%s WHERE user_id=%s AND product_id=%s",
                    (rating, comment, uid, pid))
    else:
        cur.execute("INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (%s,%s,%s,%s)",
                    (uid, pid, rating, comment))
    db.commit(); cur.close(); db.close()
    return ok({"status": "saved"})

# CART
@app.route("/api/cart", methods=["POST"])
def add_to_cart():
    d = request.get_json(); uid, _ = current_user()
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO cart (product_id, quantity, session_id) VALUES (%s,%s,%s)",
                (d["product_id"], d.get("quantity",1),
                 str(uid) if uid else d.get("session_id","anon")))
    db.commit(); cur.close(); db.close()
    return ok({"status": "added"})

# ORDERS
@app.route("/api/orders", methods=["POST"])
def place_order():
    uid, _ = current_user()
    if not uid: return err("Login required", 401)
    d = request.get_json()
    items, total, addr = d.get("items",[]), d.get("total",0), d.get("shipping_address","")
    if not items: return err("Cart is empty")
    summary = ", ".join(f"{i['name']} ×{i['qty']}" for i in items[:3])
    if len(items) > 3: summary += f" +{len(items)-3} more"
    db = get_db(); cur = db.cursor()
    cur.execute("""INSERT INTO orders (user_id, total, status, shipping_address, items_summary)
                   VALUES (%s,%s,'confirmed',%s,%s)""", (uid, total, addr, summary))
    order_id = cur.lastrowid
    for item in items:
        cur.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s,%s,%s,%s)",
                    (order_id, item["id"], item["qty"], item["price"]))
        cur.execute("UPDATE products SET stock=GREATEST(0,stock-%s) WHERE id=%s",
                    (item["qty"], item["id"]))
    db.commit(); cur.close(); db.close()
    return ok({"order_id": order_id})

@app.route("/api/orders", methods=["GET"])
def get_orders():
    uid, _ = current_user()
    if not uid: return err("Login required", 401)
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT id, total, status, shipping_address, items_summary,
               DATE_FORMAT(created_at, '%%b %%d, %%Y %%H:%%i') AS created_at
        FROM orders WHERE user_id=%s ORDER BY created_at DESC
    """, (uid,))
    rows = cur.fetchall(); cur.close(); db.close()
    return ok({"orders": rows})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
