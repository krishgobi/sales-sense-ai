"""Helper: rewrite style.css with BigBasket theme."""
import os, sys

css = r"""/* ===================================================
   BigBasket-Style CSS — Sales Sense AI
   =================================================== */

:root {
  --bb-green:       #84C225;
  --bb-green-dark:  #3d7a00;
  --bb-green-light: #e8f5d0;
  --bb-red:         #e23744;
  --bb-orange:      #ff8c00;
  --bb-white:       #ffffff;
  --bb-bg:          #f2f2f2;
  --bb-card:        #ffffff;
  --bb-text:        #333333;
  --bb-muted:       #888888;
  --bb-border:      #e0e0e0;
  --bb-nav-h:       70px;
  --bb-sub-h:       42px;
  --shadow-sm:      0 1px 4px rgba(0,0,0,.08);
  --shadow-md:      0 2px 12px rgba(0,0,0,.12);
  --radius:         8px;
  --radius-sm:      4px;
  --primary:        #84C225;
  --secondary:      #3d7a00;
  --info:           #0ea5e9;
  --gray-900:       #333333;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  background: var(--bb-bg);
  color: var(--bb-text);
  font-size: 14px;
  line-height: 1.5;
  overflow-x: hidden;
}
a { text-decoration: none; color: inherit; }
img { max-width: 100%; }

/* ── Navigation ── */
.nav-bar {
  position: sticky; top: 0; z-index: 1000;
  background: var(--bb-white);
  box-shadow: var(--shadow-md);
  height: var(--bb-nav-h);
}
.nav-container {
  max-width: 1280px; margin: 0 auto; height: 100%;
  display: flex; align-items: center; padding: 0 16px; gap: 16px;
}
.nav-logo {
  display: flex; align-items: center; gap: 8px;
  font-weight: 800; font-size: 1.4rem;
  color: var(--bb-green-dark); white-space: nowrap; flex-shrink: 0;
}
.nav-logo .bb-mark {
  width: 44px; height: 44px; background: var(--bb-green);
  border-radius: 10px; display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 900; font-size: 1rem; letter-spacing: -1px;
}
.nav-search { flex: 1; max-width: 520px; min-width: 0; }
.nav-search-inner {
  display: flex; border: 2px solid var(--bb-green);
  border-radius: var(--radius); overflow: hidden; background: #fff;
}
.nav-search-inner input {
  flex: 1; border: none; outline: none; padding: 9px 14px;
  font-size: .9rem; color: var(--bb-text); background: transparent;
}
.nav-search-inner button {
  background: var(--bb-green); border: none; color: #fff;
  padding: 0 18px; cursor: pointer; font-size: 1rem; transition: background .2s;
}
.nav-search-inner button:hover { background: var(--bb-green-dark); }

.nav-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.nav-actions a {
  display: flex; align-items: center; gap: 6px; padding: 8px 12px;
  border-radius: var(--radius); font-size: .82rem; font-weight: 600;
  color: var(--bb-text); transition: background .2s; white-space: nowrap;
}
.nav-actions a:hover { background: var(--bb-bg); }
.nav-actions .btn-cart { background: var(--bb-green); color: #fff !important; position: relative; }
.nav-actions .btn-cart:hover { background: var(--bb-green-dark); }
.cart-badge {
  position: absolute; top: -6px; right: -6px;
  background: var(--bb-red); color: #fff; border-radius: 50%;
  width: 18px; height: 18px; font-size: .6rem;
  display: flex; align-items: center; justify-content: center; font-weight: 700;
}
.nav-menu { display: flex; align-items: center; gap: 2px; }
.nav-link {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 10px; border-radius: var(--radius-sm);
  font-size: .8rem; font-weight: 600; color: var(--bb-text);
  transition: color .2s, background .2s; white-space: nowrap;
}
.nav-link:hover, .nav-link.active { color: var(--bb-green-dark); background: var(--bb-green-light); }
.nav-toggle {
  display: none; background: none; border: none;
  font-size: 1.4rem; color: var(--bb-text); cursor: pointer; margin-left: auto;
}

/* ── Category Strip ── */
.category-strip {
  background: var(--bb-white); border-bottom: 1px solid var(--bb-border);
  height: var(--bb-sub-h);
  position: sticky; top: var(--bb-nav-h); z-index: 900;
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.category-strip-inner {
  max-width: 1280px; margin: 0 auto; height: 100%;
  display: flex; align-items: center; overflow-x: auto;
  padding: 0 16px; scrollbar-width: none;
}
.category-strip-inner::-webkit-scrollbar { display: none; }
.cat-pill {
  padding: 0 16px; height: 100%; display: flex; align-items: center; gap: 6px;
  font-size: .78rem; font-weight: 600; color: var(--bb-text);
  white-space: nowrap; border-bottom: 2px solid transparent;
  transition: color .2s, border-color .2s; cursor: pointer;
}
.cat-pill:hover, .cat-pill.active { color: var(--bb-green-dark); border-bottom-color: var(--bb-green); }

/* ── Main Layout ── */
.main-content {
  min-height: calc(100vh - var(--bb-nav-h) - var(--bb-sub-h) - 120px);
  padding: 20px 0 40px;
}
.main-content > .container { max-width: 1280px; }

/* ── Hero ── */
.hero-section {
  background: linear-gradient(135deg, var(--bb-green) 0%, var(--bb-green-dark) 100%);
  color: #fff; border-radius: var(--radius);
  padding: 48px 40px; margin-bottom: 28px; text-align: center;
}
.hero-section h1 { font-size: 2.2rem; font-weight: 800; margin-bottom: 10px; }
.hero-section .lead { font-size: 1.1rem; opacity: .9; margin-bottom: 6px; }
.hero-section p { opacity: .8; margin-bottom: 24px; }

/* ── Cards ── */
.card {
  background: var(--bb-card); border: 1px solid var(--bb-border);
  border-radius: var(--radius); box-shadow: var(--shadow-sm); overflow: hidden;
}
.card-header {
  background: var(--bb-white); border-bottom: 1px solid var(--bb-border);
  padding: 14px 18px; font-weight: 700; font-size: .9rem; color: var(--bb-text);
}
.card-body { padding: 18px; }

/* ── Stat Cards ── */
.stat-card {
  background: var(--bb-green); color: #fff; border-radius: var(--radius);
  padding: 24px 20px; text-align: center;
  box-shadow: var(--shadow-md); transition: transform .2s;
}
.stat-card:hover { transform: translateY(-2px); }
.stat-card.success { background: var(--bb-green); }
.stat-card.warning { background: #ff8c00; }
.stat-card.danger  { background: var(--bb-red); }
.stat-card.info    { background: #0ea5e9; }
.stat-icon { font-size: 2rem; margin-bottom: 8px; opacity: .9; }
.stat-value { font-size: 1.8rem; font-weight: 800; }
.stat-label { font-size: .78rem; opacity: .85; margin-top: 4px; }

/* ── Buttons ── */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; border-radius: var(--radius-sm);
  font-size: .84rem; font-weight: 600; cursor: pointer;
  border: 2px solid transparent; transition: all .2s;
  white-space: nowrap; text-decoration: none;
}
.btn-primary { background: var(--bb-green); color: #fff; border-color: var(--bb-green); }
.btn-primary:hover { background: var(--bb-green-dark); border-color: var(--bb-green-dark); color: #fff; }
.btn-secondary { background: #666; color: #fff; border-color: #666; }
.btn-secondary:hover { background: #444; border-color: #444; color: #fff; }
.btn-danger { background: var(--bb-red); color: #fff; border-color: var(--bb-red); }
.btn-danger:hover { background: #c0202e; border-color: #c0202e; color: #fff; }
.btn-light { background: #fff; color: var(--bb-text); border-color: var(--bb-border); }
.btn-light:hover { background: var(--bb-bg); color: var(--bb-text); }
.btn-outline-primary { background: transparent; color: var(--bb-green-dark); border-color: var(--bb-green); }
.btn-outline-primary:hover { background: var(--bb-green); color: #fff; border-color: var(--bb-green); }
.btn-success { background: var(--bb-green); color: #fff; border-color: var(--bb-green); }
.btn-success:hover { background: var(--bb-green-dark); color: #fff; }
.btn-warning { background: #ff8c00; color: #fff; border-color: #ff8c00; }
.btn-info    { background: #0ea5e9; color: #fff; border-color: #0ea5e9; }
.btn-sm { padding: 6px 12px; font-size: .78rem; }
.btn-lg { padding: 12px 28px; font-size: 1rem; }
.btn-xs { padding: 4px 10px; font-size: .72rem; }
.btn-add-bb {
  border: 1.5px solid var(--bb-green); color: var(--bb-green-dark); background: #fff;
  border-radius: var(--radius-sm); padding: 6px 20px; font-size: .82rem;
  font-weight: 700; cursor: pointer; transition: all .2s;
  text-transform: uppercase; letter-spacing: .5px;
}
.btn-add-bb:hover { background: var(--bb-green); color: #fff; border-color: var(--bb-green); }

/* ── Product Grid ── */
#productsGrid, .products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px; margin-top: 16px;
}
.product-card-wrapper .card, .bb-product-card {
  border-radius: var(--radius); border: 1px solid var(--bb-border);
  box-shadow: var(--shadow-sm); background: #fff;
  transition: box-shadow .2s, transform .2s;
  position: relative; display: flex; flex-direction: column; height: 100%;
}
.product-card-wrapper .card:hover, .bb-product-card:hover {
  box-shadow: var(--shadow-md); transform: translateY(-2px);
}
.product-img-area {
  background: #f9f9f9; height: 140px;
  display: flex; align-items: center; justify-content: center;
  border-bottom: 1px solid var(--bb-border); position: relative;
  border-radius: var(--radius) var(--radius) 0 0; overflow: hidden;
}
.product-emoji { font-size: 3.5rem; line-height: 1; filter: drop-shadow(0 2px 4px rgba(0,0,0,.1)); }
.discount-badge {
  position: absolute; top: 8px; right: 8px;
  background: var(--bb-red); color: #fff;
  font-size: .68rem; font-weight: 700; padding: 3px 7px; border-radius: 3px; z-index: 2;
}
.festival-badge-img {
  position: absolute; top: 8px; left: 8px;
  background: linear-gradient(135deg,#f59e0b,#ef4444); color: #fff;
  font-size: .65rem; font-weight: 700; padding: 3px 7px; border-radius: 3px; z-index: 2;
  max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-body { flex: 1; display: flex; flex-direction: column; padding: 12px; }
.card-title {
  font-size: .88rem; font-weight: 700; color: var(--bb-text);
  margin-bottom: 3px; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.product-category { font-size: .7rem; color: var(--bb-muted); text-transform: uppercase; letter-spacing: .5px; font-weight: 600; }
.product-price { font-size: .95rem; font-weight: 800; color: var(--bb-text); margin: 6px 0; }
.product-price .mrp { font-size: .78rem; font-weight: 400; color: var(--bb-muted); text-decoration: line-through; margin-right: 5px; }
.variant-item { border-top: 1px solid var(--bb-border); padding-top: 8px; margin-top: 6px; }

/* ── Products Header ── */
.products-header {
  background: var(--bb-white); border-radius: var(--radius);
  padding: 16px 20px; margin-bottom: 16px; box-shadow: var(--shadow-sm);
}
.products-header h1 { font-size: 1.3rem; font-weight: 800; color: var(--bb-text); margin: 0; }
.header-controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.search-input {
  flex: 1; min-width: 160px; padding: 9px 14px;
  border: 1.5px solid var(--bb-border); border-radius: var(--radius-sm);
  font-size: .84rem; outline: none; transition: border-color .2s;
}
.search-input:focus { border-color: var(--bb-green); }
.items-select {
  padding: 9px 12px; border: 1.5px solid var(--bb-border);
  border-radius: var(--radius-sm); font-size: .84rem;
  background: #fff; outline: none; cursor: pointer; transition: border-color .2s;
}
.items-select:focus { border-color: var(--bb-green); }

/* ── Form Controls ── */
.form-control, .form-select {
  display: block; width: 100%; padding: 9px 12px;
  font-size: .84rem; color: var(--bb-text); background: #fff;
  border: 1.5px solid var(--bb-border); border-radius: var(--radius-sm);
  outline: none; transition: border-color .2s;
}
.form-control:focus, .form-select:focus {
  border-color: var(--bb-green);
  box-shadow: 0 0 0 3px rgba(132,194,37,.15);
}
.form-label { font-size: .83rem; font-weight: 600; color: var(--bb-text); margin-bottom: 6px; display: block; }
.input-group { display: flex; }
.input-group .form-control { border-radius: var(--radius-sm) 0 0 var(--radius-sm) !important; border-right: none; }
.input-group .btn { border-radius: 0 var(--radius-sm) var(--radius-sm) 0 !important; }

/* ── Tables ── */
.table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.table th { background: #f7fbf0; color: var(--bb-green-dark); font-weight: 700; padding: 11px 14px; border-bottom: 2px solid var(--bb-green-light); text-align: left; }
.table td { padding: 10px 14px; border-bottom: 1px solid var(--bb-border); vertical-align: middle; }
.table tbody tr:hover { background: #fafff3; }

/* ── Badges ── */
.badge { display: inline-flex; align-items: center; padding: 3px 8px; border-radius: 3px; font-size: .68rem; font-weight: 700; letter-spacing: .3px; }
.bg-success   { background: var(--bb-green) !important; color: #fff; }
.bg-warning   { background: #ff8c00 !important; color: #fff; }
.bg-danger    { background: var(--bb-red) !important; color: #fff; }
.bg-primary   { background: var(--bb-green-dark) !important; color: #fff; }
.bg-info      { background: #0ea5e9 !important; color: #fff; }
.bg-secondary { background: #888 !important; color: #fff; }
.bg-light     { background: #f2f2f2 !important; color: #333; }

/* ── Alerts ── */
.alert { padding: 12px 16px; border-radius: var(--radius-sm); font-size: .85rem; margin-bottom: 14px; border: 1px solid transparent; }
.alert-success { background: #e8f5d0; color: var(--bb-green-dark); border-color: var(--bb-green-light); }
.alert-danger  { background: #fde8ea; color: #c0202e; border-color: #f5b4b8; }
.alert-warning { background: #fff3cd; color: #856404; border-color: #ffc107; }
.alert-info    { background: #e0f2fe; color: #0369a1; border-color: #bae6fd; }

/* ── Modals ── */
.modal-content { border: none; border-radius: var(--radius); box-shadow: 0 8px 40px rgba(0,0,0,.18); }
.modal-header { background: var(--bb-green); color: #fff; border-bottom: none; border-radius: var(--radius) var(--radius) 0 0; padding: 16px 20px; }
.modal-title { font-weight: 700; font-size: 1rem; }
.btn-close { filter: brightness(0) invert(1); }
.modal-body { padding: 24px 20px; }
.modal-footer { padding: 14px 20px; border-top: 1px solid var(--bb-border); }

/* ── Toast ── */
.toast-container { position: fixed; top: 90px; right: 16px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; pointer-events: none; }
.toast-item { background: #333; color: #fff; padding: 12px 18px; border-radius: var(--radius-sm); font-size: .84rem; box-shadow: var(--shadow-md); pointer-events: auto; animation: slideInRight .3s ease; min-width: 240px; max-width: 340px; }
.toast-item.success { background: var(--bb-green-dark); }
.toast-item.error   { background: var(--bb-red); }
.toast-item.warning { background: var(--bb-orange); }
@keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

/* ── Footer ── */
.footer { background: var(--bb-green-dark); color: rgba(255,255,255,.8); text-align: center; padding: 20px 0; font-size: .82rem; margin-top: auto; }
.footer a { color: rgba(255,255,255,.7); }
.footer a:hover { color: #fff; }

/* ── Admin ── */
.admin-header { background: var(--bb-white); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 20px; border-left: 4px solid var(--bb-green); box-shadow: var(--shadow-sm); }
.admin-header h1 { font-size: 1.5rem; font-weight: 800; color: var(--bb-text); }
.section-title { font-size: 1rem; font-weight: 700; color: var(--bb-text); margin-bottom: 14px; padding-bottom: 8px; border-bottom: 2px solid var(--bb-green-light); display: flex; align-items: center; gap: 8px; }
.quick-action-btn { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 18px 12px; background: #fff; border: 1.5px solid var(--bb-border); border-radius: var(--radius); cursor: pointer; transition: all .2s; font-size: .78rem; font-weight: 600; color: var(--bb-text); text-align: center; box-shadow: var(--shadow-sm); }
.quick-action-btn:hover { border-color: var(--bb-green); background: var(--bb-green-light); color: var(--bb-green-dark); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.quick-action-btn i, .quick-action-btn .icon { font-size: 1.6rem; color: var(--bb-green); }

/* ── Login ── */
.login-wrapper { min-height: 100vh; background: linear-gradient(135deg, var(--bb-green) 0%, var(--bb-green-dark) 100%); display: flex; align-items: center; justify-content: center; padding: 20px; }
.login-card { background: #fff; border-radius: 12px; padding: 40px; width: 100%; max-width: 420px; box-shadow: 0 20px 60px rgba(0,0,0,.25); }
.login-logo { text-align: center; margin-bottom: 28px; }
.login-logo .bb-mark-lg { width: 64px; height: 64px; background: var(--bb-green); border-radius: 16px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.5rem; color: #fff; margin-bottom: 10px; }
.login-logo h2 { font-size: 1.4rem; font-weight: 800; color: var(--bb-text); }
.login-logo p  { font-size: .82rem; color: var(--bb-muted); }

/* ── Chatbot ── */
.chatbot-wrapper { max-width: 860px; margin: 0 auto; }
.chat-window { background: #fff; border-radius: var(--radius); border: 1px solid var(--bb-border); box-shadow: var(--shadow-md); display: flex; flex-direction: column; height: 560px; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; background: #fafff3; }
.chat-bubble { max-width: 75%; padding: 10px 15px; border-radius: 12px; font-size: .88rem; line-height: 1.5; }
.chat-bubble.user { align-self: flex-end; background: var(--bb-green); color: #fff; border-bottom-right-radius: 3px; }
.chat-bubble.bot { align-self: flex-start; background: #fff; color: var(--bb-text); border: 1px solid var(--bb-border); border-bottom-left-radius: 3px; box-shadow: var(--shadow-sm); }
.chat-input-bar { display: flex; border-top: 1px solid var(--bb-border); background: #fff; }
.chat-input-bar input { flex: 1; border: none; outline: none; padding: 14px 16px; font-size: .9rem; background: transparent; }
.chat-input-bar button { background: var(--bb-green); color: #fff; border: none; padding: 0 20px; cursor: pointer; font-size: 1.1rem; transition: background .2s; }
.chat-input-bar button:hover { background: var(--bb-green-dark); }

/* ── Analytics ── */
.analytics-header { background: linear-gradient(135deg, var(--bb-green) 0%, var(--bb-green-dark) 100%); color: #fff; border-radius: var(--radius); padding: 28px 32px; margin-bottom: 24px; }
.analytics-header h1 { font-size: 1.6rem; font-weight: 800; }

/* ── Misc Helpers ── */
.notification-card { border: 1px solid var(--bb-border); border-radius: var(--radius); padding: 16px; background: #fff; box-shadow: var(--shadow-sm); transition: box-shadow .2s; }
.notification-card:hover { box-shadow: var(--shadow-md); }
.worker-stat { background: var(--bb-white); border: 1px solid var(--bb-border); border-radius: var(--radius); padding: 20px; text-align: center; box-shadow: var(--shadow-sm); }

/* ── Responsive ── */
@media (max-width: 768px) {
  .nav-search { display: none; }
  .nav-menu { display: none; position: absolute; top: var(--bb-nav-h); left: 0; right: 0; background: #fff; flex-direction: column; padding: 12px; box-shadow: var(--shadow-md); border-top: 1px solid var(--bb-border); z-index: 999; gap: 2px; }
  .nav-menu.active { display: flex; }
  .nav-link { padding: 10px 14px; width: 100%; }
  .nav-toggle { display: flex; }
  #productsGrid, .products-grid { grid-template-columns: repeat(auto-fill, minmax(148px, 1fr)); gap: 10px; }
  .hero-section { padding: 30px 20px; }
  .hero-section h1 { font-size: 1.5rem; }
  .login-card { padding: 28px 20px; }
}
@media (max-width: 480px) {
  #productsGrid, .products-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .product-img-area { height: 110px; }
  .product-emoji { font-size: 2.8rem; }
}

/* ── Utility ── */
.text-muted   { color: var(--bb-muted) !important; }
.text-success { color: var(--bb-green-dark) !important; }
.text-danger  { color: var(--bb-red) !important; }
.text-primary { color: var(--bb-green-dark) !important; }
.text-center  { text-align: center; }
.text-end     { text-align: right; }
.fw-bold   { font-weight: 700 !important; }
.fw-bolder { font-weight: 800 !important; }
.mb-0{margin-bottom:0}.mb-1{margin-bottom:4px}.mb-2{margin-bottom:8px}.mb-3{margin-bottom:16px}.mb-4{margin-bottom:24px}
.mt-1{margin-top:4px}.mt-2{margin-top:8px}.mt-3{margin-top:16px}.mt-4{margin-top:24px}
.ms-1{margin-left:4px}.ms-2{margin-left:8px}.ms-3{margin-left:16px}
.me-1{margin-right:4px}.me-2{margin-right:8px}.me-3{margin-right:16px}
.p-0{padding:0}.p-2{padding:8px}.p-3{padding:16px}.p-4{padding:24px}
.px-3{padding-left:16px;padding-right:16px}.py-2{padding-top:8px;padding-bottom:8px}
.w-100{width:100%}.h-100{height:100%}
.d-none{display:none!important}.d-flex{display:flex}.d-block{display:block}.d-inline-flex{display:inline-flex}
.align-items-center{align-items:center}.align-items-start{align-items:flex-start}
.justify-content-between{justify-content:space-between}.justify-content-center{justify-content:center}.justify-content-end{justify-content:flex-end}
.flex-wrap{flex-wrap:wrap}.flex-column{flex-direction:column}
.gap-1{gap:4px}.gap-2{gap:8px}.gap-3{gap:16px}.gap-4{gap:24px}
.rounded{border-radius:var(--radius)}.rounded-sm{border-radius:var(--radius-sm)}
.shadow-sm{box-shadow:var(--shadow-sm)}.shadow{box-shadow:var(--shadow-md)}
.border{border:1px solid var(--bb-border)}.border-0{border:none}
.overflow-hidden{overflow:hidden}.position-relative{position:relative}

/* Scrollbars */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:#f2f2f2}
::-webkit-scrollbar-thumb{background:#c0c0c0;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#888}
.no-scrollbar::-webkit-scrollbar{display:none}
.no-scrollbar{scrollbar-width:none}

/* Bootstrap grid shims */
.row{display:flex;flex-wrap:wrap;margin-right:-8px;margin-left:-8px}
.col-md-4,.col-sm-6,.col-md-6,.col-md-8,.col-md-3,.col-12,.col-md-12{padding-right:8px;padding-left:8px;width:100%}
@media(min-width:768px){
 .col-md-1{width:8.333%}.col-md-2{width:16.667%}.col-md-3{width:25%}.col-md-4{width:33.333%}
 .col-md-5{width:41.667%}.col-md-6{width:50%}.col-md-7{width:58.333%}.col-md-8{width:66.667%}
 .col-md-9{width:75%}.col-md-10{width:83.333%}.col-md-11{width:91.667%}.col-md-12{width:100%}
}
@media(min-width:576px){.col-sm-6{width:50%}}
"""

path = os.path.join(os.path.dirname(__file__), 'static', 'css', 'style.css')
with open(path, 'w', encoding='utf-8') as f:
    f.write(css)
print("CSS written:", len(css), "chars")
