"""Helper: rewrite admin_ai_chat.html with BigBasket green theme."""
import os

html = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI DB Assistant – SalesSense Admin</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

    :root{
      --green:#84C225;
      --green-dark:#3d7a00;
      --green-light:#e8f5d0;
      --red:#e23744;
      --bg:#f2f2f2;
      --sidebar:#ffffff;
      --surface:#ffffff;
      --border:#e0e0e0;
      --text:#333333;
      --muted:#888888;
      --radius:8px;
    }

    html,body{height:100%;font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);overflow:hidden;}

    /* Layout */
    .layout{display:flex;height:100vh;}

    /* Sidebar */
    .sidebar{
      width:260px;min-width:260px;
      background:var(--sidebar);
      border-right:1px solid var(--border);
      display:flex;flex-direction:column;
    }
    .sidebar-top{padding:16px;border-bottom:1px solid var(--border);}
    .logo{display:flex;align-items:center;gap:10px;margin-bottom:14px;}
    .logo-mark{
      width:36px;height:36px;background:var(--green);
      border-radius:9px;display:flex;align-items:center;justify-content:center;
      font-weight:900;font-size:.9rem;color:#fff;flex-shrink:0;
    }
    .logo-text{font-weight:800;font-size:1rem;color:var(--green-dark);}
    .logo-sub{font-size:.7rem;color:var(--muted);margin-top:1px;}
    .btn-new{
      display:flex;align-items:center;justify-content:center;gap:6px;
      width:100%;padding:10px;border-radius:var(--radius);
      background:var(--green);color:#fff;font-size:.82rem;font-weight:700;
      border:none;cursor:pointer;transition:background .2s;
    }
    .btn-new:hover{background:var(--green-dark);}
    .sidebar-history{flex:1;overflow-y:auto;padding:12px;}
    .history-label{font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;}
    .history-item{
      display:flex;align-items:center;gap:8px;padding:9px 10px;
      border-radius:6px;cursor:pointer;transition:background .2s;
      font-size:.8rem;color:var(--text);border:1px solid transparent;
    }
    .history-item:hover{background:var(--green-light);border-color:var(--green);}
    .history-item.active{background:var(--green-light);border-color:var(--green);color:var(--green-dark);font-weight:600;}
    .history-item i{color:var(--green);flex-shrink:0;font-size:.8rem;}
    .history-text{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;}
    .sidebar-footer{padding:12px 16px;border-top:1px solid var(--border);}
    .sidebar-footer a{
      display:flex;align-items:center;gap:8px;padding:9px 10px;
      border-radius:6px;font-size:.8rem;font-weight:600;color:var(--text);
      text-decoration:none;transition:background .2s;
    }
    .sidebar-footer a:hover{background:var(--green-light);color:var(--green-dark);}
    .sidebar-footer a i{color:var(--green);}

    /* Main chat area */
    .main{flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg);}

    /* Header */
    .chat-header{
      background:#fff;border-bottom:1px solid var(--border);
      padding:14px 24px;display:flex;align-items:center;justify-content:space-between;
      box-shadow:0 1px 4px rgba(0,0,0,.06);
    }
    .chat-header-left{display:flex;align-items:center;gap:12px;}
    .header-avatar{
      width:38px;height:38px;background:var(--green);
      border-radius:9px;display:flex;align-items:center;justify-content:center;
      color:#fff;font-size:1rem;flex-shrink:0;
    }
    .header-title{font-weight:800;font-size:1rem;color:var(--text);}
    .header-sub{font-size:.72rem;color:var(--muted);margin-top:1px;}
    .header-badges{display:flex;align-items:center;gap:8px;}
    .badge-pill{
      padding:5px 12px;border-radius:20px;font-size:.72rem;font-weight:700;
      border:1.5px solid var(--green);color:var(--green-dark);background:#fff;
      cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:5px;
      user-select:none;
    }
    .badge-pill.active,.badge-pill:hover{background:var(--green);color:#fff;border-color:var(--green);}
    .badge-pill.deepthink-active{background:linear-gradient(135deg,var(--green),var(--green-dark));color:#fff;border-color:var(--green-dark);}
    .back-btn{
      display:flex;align-items:center;gap:6px;padding:8px 14px;
      border-radius:6px;font-size:.8rem;font-weight:600;color:var(--text);
      background:#fff;border:1.5px solid var(--border);cursor:pointer;
      transition:all .2s;text-decoration:none;
    }
    .back-btn:hover{border-color:var(--green);color:var(--green-dark);}

    /* Messages */
    .messages-wrap{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:20px;}

    /* Welcome state */
    .welcome{
      max-width:640px;margin:auto;text-align:center;padding:20px;
    }
    .welcome-icon{
      width:64px;height:64px;background:var(--green);border-radius:16px;
      display:flex;align-items:center;justify-content:center;
      font-size:1.8rem;font-weight:900;color:#fff;margin:0 auto 16px;
    }
    .welcome h2{font-size:1.4rem;font-weight:800;color:var(--text);margin-bottom:8px;}
    .welcome p{font-size:.88rem;color:var(--muted);line-height:1.6;margin-bottom:24px;}

    .suggestions{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
    .suggestion-card{
      background:#fff;border:1.5px solid var(--border);border-radius:var(--radius);
      padding:14px 16px;cursor:pointer;transition:all .2s;text-align:left;
    }
    .suggestion-card:hover{border-color:var(--green);background:var(--green-light);}
    .suggestion-icon{font-size:1.1rem;margin-bottom:6px;}
    .suggestion-title{font-size:.82rem;font-weight:700;color:var(--text);margin-bottom:3px;}
    .suggestion-sub{font-size:.74rem;color:var(--muted);}

    /* Message bubbles */
    .msg{display:flex;gap:12px;max-width:760px;}
    .msg.user{flex-direction:row-reverse;margin-left:auto;}
    .msg-avatar{
      width:34px;height:34px;border-radius:8px;flex-shrink:0;
      display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:700;
    }
    .msg.ai .msg-avatar{background:var(--green);color:#fff;}
    .msg.user .msg-avatar{background:#333;color:#fff;}
    .msg-body{flex:1;min-width:0;}
    .msg-name{font-size:.72rem;font-weight:700;color:var(--muted);margin-bottom:5px;text-transform:uppercase;letter-spacing:.4px;}
    .msg.user .msg-name{text-align:right;}
    .msg-bubble{
      padding:12px 16px;border-radius:12px;font-size:.875rem;line-height:1.65;
    }
    .msg.ai .msg-bubble{
      background:#fff;color:var(--text);
      border:1px solid var(--border);border-bottom-left-radius:3px;
      box-shadow:0 1px 4px rgba(0,0,0,.06);
    }
    .msg.user .msg-bubble{
      background:var(--green);color:#fff;
      border-bottom-right-radius:3px;
    }
    /* Markdown inside AI bubbles */
    .msg.ai .msg-bubble h1,.msg.ai .msg-bubble h2,.msg.ai .msg-bubble h3{font-size:1rem;font-weight:700;margin:10px 0 6px;}
    .msg.ai .msg-bubble p{margin:0 0 8px;}
    .msg.ai .msg-bubble p:last-child{margin-bottom:0;}
    .msg.ai .msg-bubble ul,.msg.ai .msg-bubble ol{padding-left:20px;margin-bottom:8px;}
    .msg.ai .msg-bubble li{margin-bottom:4px;}
    .msg.ai .msg-bubble code{background:#f5f5f5;padding:2px 6px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-size:.8em;}
    .msg.ai .msg-bubble pre{background:#f5f5f5;padding:14px;border-radius:6px;overflow-x:auto;margin:8px 0;}
    .msg.ai .msg-bubble pre code{background:none;padding:0;font-size:.82em;}
    .msg.ai .msg-bubble table{width:100%;border-collapse:collapse;margin:8px 0;font-size:.82rem;}
    .msg.ai .msg-bubble th{background:#e8f5d0;color:var(--green-dark);font-weight:700;padding:7px 10px;border:1px solid #cde898;text-align:left;}
    .msg.ai .msg-bubble td{padding:6px 10px;border:1px solid #e0e0e0;}
    .msg-actions{display:flex;gap:6px;margin-top:8px;}
    .msg-action-btn{
      padding:4px 10px;border-radius:4px;font-size:.7rem;font-weight:600;
      border:1px solid var(--border);background:#fff;color:var(--muted);cursor:pointer;
      transition:all .2s;display:flex;align-items:center;gap:4px;
    }
    .msg-action-btn:hover{border-color:var(--green);color:var(--green-dark);}

    /* Typing indicator */
    .typing-indicator{display:flex;align-items:center;gap:5px;padding:12px 16px;background:#fff;border:1px solid var(--border);border-radius:12px;width:fit-content;}
    .typing-dot{width:8px;height:8px;background:var(--green);border-radius:50%;animation:typingBounce .9s infinite;}
    .typing-dot:nth-child(2){animation-delay:.15s;}
    .typing-dot:nth-child(3){animation-delay:.3s;}
    @keyframes typingBounce{0%,100%{transform:translateY(0);opacity:.5;}50%{transform:translateY(-5px);opacity:1;}}

    /* Think block */
    .think-block{
      border-left:3px solid var(--green);padding:10px 14px;margin-bottom:10px;
      background:var(--green-light);border-radius:0 6px 6px 0;font-size:.8rem;color:var(--green-dark);
    }
    .think-block .think-label{font-size:.7rem;font-weight:700;text-transform:uppercase;margin-bottom:6px;opacity:.7;}

    /* Input area */
    .input-area{
      background:#fff;border-top:1px solid var(--border);padding:16px 24px;
    }
    .input-wrap{
      max-width:800px;margin:0 auto;
      border:2px solid var(--green);border-radius:var(--radius);
      background:#fff;overflow:hidden;box-shadow:0 2px 12px rgba(132,194,37,.12);
    }
    .input-toolbar{
      display:flex;align-items:center;gap:6px;padding:10px 14px 0;
    }
    .tool-btn{
      padding:5px 12px;border-radius:20px;font-size:.72rem;font-weight:700;
      border:1.5px solid var(--border);background:#fff;color:var(--text);
      cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:4px;
    }
    .tool-btn:hover,.tool-btn.active{background:var(--green);color:#fff;border-color:var(--green);}
    .input-row{display:flex;align-items:flex-end;padding:10px 14px 12px;}
    .input-field{
      flex:1;border:none;outline:none;font-size:.9rem;font-family:'Inter',sans-serif;
      color:var(--text);background:transparent;resize:none;min-height:24px;max-height:140px;
      line-height:1.5;
    }
    .input-field::placeholder{color:#bbb;}
    .send-btn{
      width:36px;height:36px;border-radius:8px;background:var(--green);
      border:none;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;
      font-size:.9rem;flex-shrink:0;margin-left:10px;transition:background .2s;
    }
    .send-btn:hover{background:var(--green-dark);}
    .send-btn:disabled{background:#ccc;cursor:not-allowed;}
    .input-hint{text-align:center;font-size:.68rem;color:var(--muted);margin-top:6px;}

    /* Scrollbar */
    ::-webkit-scrollbar{width:5px}
    ::-webkit-scrollbar-track{background:transparent}
    ::-webkit-scrollbar-thumb{background:#ddd;border-radius:3px}
    ::-webkit-scrollbar-thumb:hover{background:#bbb}

    /* Mobile */
    @media(max-width:700px){
      .sidebar{display:none;}
      .suggestions{grid-template-columns:1fr;}
    }
  </style>
</head>
<body>
<div class="layout">

  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-top">
      <div class="logo">
        <div class="logo-mark">SS</div>
        <div>
          <div class="logo-text">SalesSense AI</div>
          <div class="logo-sub">AI Database Assistant</div>
        </div>
      </div>
      <button class="btn-new" onclick="startNewChat()"><i class="fas fa-plus"></i> New Chat</button>
    </div>
    <div class="sidebar-history">
      <div class="history-label">Recent Conversations</div>
      <div id="historyList">
        <!-- filled by JS -->
      </div>
    </div>
    <div class="sidebar-footer">
      <a href="/admin/dashboard"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
      <a href="/analytics" style="margin-top:4px;"><i class="fas fa-chart-bar"></i> Analytics</a>
      <a href="/products" style="margin-top:4px;"><i class="fas fa-shopping-basket"></i> Products</a>
    </div>
  </aside>

  <!-- Main -->
  <div class="main">

    <!-- Header -->
    <div class="chat-header">
      <div class="chat-header-left">
        <div class="header-avatar"><i class="fas fa-robot"></i></div>
        <div>
          <div class="header-title">AI Database Assistant</div>
          <div class="header-sub" id="modelLabel">Using llama-3.3-70b-versatile</div>
        </div>
      </div>
      <div class="header-badges">
        <div class="badge-pill" id="deepthinkToggle" onclick="toggleDeepThink()">
          <i class="fas fa-brain"></i> DeepThink
        </div>
        <div class="badge-pill" id="searchDbToggle" onclick="toggleSearchDb()" style="display:flex;">
          <i class="fas fa-database"></i> Search DB
        </div>
        <a href="/admin/dashboard" class="back-btn"><i class="fas fa-home"></i> Dashboard</a>
      </div>
    </div>

    <!-- Messages -->
    <div class="messages-wrap" id="messagesArea">

      <!-- Welcome state - hidden once chat starts -->
      <div class="welcome" id="welcomeState">
        <div class="welcome-icon"><i class="fas fa-robot"></i></div>
        <h2>SalesSense AI Assistant</h2>
        <p>Ask me anything about your sales data, products, users, or business analytics. I'll query your MongoDB database and give you intelligent answers.</p>
        <div class="suggestions">
          <div class="suggestion-card" onclick="askSuggestion('What are the top 5 selling products this month?')">
            <div class="suggestion-icon">🏆</div>
            <div class="suggestion-title">Top Products</div>
            <div class="suggestion-sub">What are the top selling products this month?</div>
          </div>
          <div class="suggestion-card" onclick="askSuggestion('Show me total revenue and sales trends for last 30 days')">
            <div class="suggestion-icon">📈</div>
            <div class="suggestion-title">Revenue Trends</div>
            <div class="suggestion-sub">Total revenue and sales trend last 30 days</div>
          </div>
          <div class="suggestion-card" onclick="askSuggestion('Which products have low stock that need restocking?')">
            <div class="suggestion-icon">⚠️</div>
            <div class="suggestion-title">Low Stock Alert</div>
            <div class="suggestion-sub">Products that need urgent restocking</div>
          </div>
          <div class="suggestion-card" onclick="askSuggestion('Show me a breakdown of sales by category')">
            <div class="suggestion-icon">📊</div>
            <div class="suggestion-title">Category Analysis</div>
            <div class="suggestion-sub">Sales breakdown across all categories</div>
          </div>
          <div class="suggestion-card" onclick="askSuggestion('How many users do we have and who are the most active buyers?')">
            <div class="suggestion-icon">👥</div>
            <div class="suggestion-title">User Insights</div>
            <div class="suggestion-sub">User count and most active buyers</div>
          </div>
          <div class="suggestion-card" onclick="askSuggestion('What is the average order value and payment method distribution?')">
            <div class="suggestion-icon">💳</div>
            <div class="suggestion-title">Order Analytics</div>
            <div class="suggestion-sub">Average order value and payment methods</div>
          </div>
        </div>
      </div>

    </div>

    <!-- Input area -->
    <div class="input-area">
      <div class="input-wrap">
        <div class="input-toolbar">
          <button class="tool-btn" id="deepthinkBtn" onclick="toggleDeepThink()">
            <i class="fas fa-brain"></i> DeepThink
          </button>
          <button class="tool-btn active" id="searchDbBtn" onclick="toggleSearchDb()">
            <i class="fas fa-database"></i> Search DB
          </button>
        </div>
        <div class="input-row">
          <textarea class="input-field" id="msgInput" placeholder="Ask about sales, products, users, revenue…" rows="1"
                    onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
          <button class="send-btn" id="sendBtn" onclick="sendMessage()">
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
      <div class="input-hint">Enter to send &bull; Shift+Enter for new line &bull; DeepThink uses advanced reasoning</div>
    </div>
  </div>

</div>

<script>
  let sessions    = JSON.parse(localStorage.getItem('ss_ai_sessions') || '[]');
  let currentId   = null;
  let msgs        = [];
  let deepThinkOn = false;
  let searchDbOn  = true;
  let isLoading   = false;

  marked.setOptions({ breaks: true, gfm: true });

  // ── Init ────────────────────────────────────────────
  renderHistory();

  // ── Toggle DeepThink ────────────────────────────────
  function toggleDeepThink() {
    deepThinkOn = !deepThinkOn;
    document.getElementById('deepthinkToggle').classList.toggle('deepthink-active', deepThinkOn);
    document.getElementById('deepthinkBtn').classList.toggle('active', deepThinkOn);
    document.getElementById('modelLabel').textContent = deepThinkOn
      ? 'Using deepseek-r1-distill-llama-70b (DeepThink)'
      : 'Using llama-3.3-70b-versatile';
  }

  // ── Toggle Search DB ────────────────────────────────
  function toggleSearchDb() {
    searchDbOn = !searchDbOn;
    document.getElementById('searchDbToggle').classList.toggle('active', searchDbOn);
    document.getElementById('searchDbBtn').classList.toggle('active', searchDbOn);
  }

  // ── Textarea auto-resize ────────────────────────────
  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
  }

  // ── Keyboard handler ────────────────────────────────
  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  // ── Suggestion cards ────────────────────────────────
  function askSuggestion(text) {
    document.getElementById('msgInput').value = text;
    sendMessage();
  }

  // ── Start new chat ──────────────────────────────────
  function startNewChat() {
    msgs = [];
    currentId = null;
    document.getElementById('welcomeState').style.display = '';
    document.querySelectorAll('.msg').forEach(m => m.remove());
    renderHistory();
  }

  // ── Send message ─────────────────────────────────────
  async function sendMessage() {
    if (isLoading) return;
    const input = document.getElementById('msgInput');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    input.style.height = 'auto';

    // Hide welcome
    document.getElementById('welcomeState').style.display = 'none';

    // Append user msg
    appendMsg('user', text);

    // Show typing
    const typingEl = appendTyping();
    isLoading = true;
    document.getElementById('sendBtn').disabled = true;

    try {
      const res = await fetch('/admin/ai-chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, deepthink: deepThinkOn, search_db: searchDbOn })
      });
      const data = await res.json();
      typingEl.remove();
      const answer = data.answer || data.error || 'No response received.';
      appendMsg('ai', answer);
      saveSession(text);
    } catch(e) {
      typingEl.remove();
      appendMsg('ai', '⚠️ Error connecting to AI server. Please try again.');
    }

    isLoading = false;
    document.getElementById('sendBtn').disabled = false;
  }

  // ── Append message ───────────────────────────────────
  function appendMsg(role, text) {
    const area = document.getElementById('messagesArea');
    const div = document.createElement('div');
    div.className = 'msg ' + role;

    const avatarText = role === 'ai' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    const nameText   = role === 'ai' ? 'AI Assistant' : 'You';

    let bubbleContent;
    if (role === 'ai') {
      bubbleContent = marked.parse(text);
    } else {
      bubbleContent = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    div.innerHTML = `
      <div class="msg-avatar">${avatarText}</div>
      <div class="msg-body">
        <div class="msg-name">${nameText}</div>
        <div class="msg-bubble">${bubbleContent}</div>
        ${role === 'ai' ? `
        <div class="msg-actions">
          <button class="msg-action-btn" onclick="copyText(this, '${encodeURIComponent(text)}')">
            <i class="far fa-copy"></i> Copy
          </button>
          <button class="msg-action-btn" onclick="regenerate('${encodeURIComponent(text)}')">
            <i class="fas fa-redo"></i> Regenerate
          </button>
        </div>` : ''}
      </div>`;

    area.appendChild(div);
    area.scrollTop = area.scrollHeight;

    // Highlight code blocks
    div.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    return div;
  }

  // ── Typing indicator ─────────────────────────────────
  function appendTyping() {
    const area = document.getElementById('messagesArea');
    const div  = document.createElement('div');
    div.className = 'msg ai';
    div.innerHTML = `
      <div class="msg-avatar"><i class="fas fa-robot"></i></div>
      <div class="msg-body">
        <div class="msg-name">AI Assistant</div>
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <span style="font-size:.78rem;color:#888;margin-left:6px;">Thinking…</span>
        </div>
      </div>`;
    area.appendChild(div);
    area.scrollTop = area.scrollHeight;
    return div;
  }

  // ── Copy ─────────────────────────────────────────────
  function copyText(btn, encoded) {
    navigator.clipboard.writeText(decodeURIComponent(encoded)).then(() => {
      btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
      setTimeout(() => btn.innerHTML = '<i class="far fa-copy"></i> Copy', 2000);
    });
  }

  // ── Regenerate ───────────────────────────────────────
  function regenerate(encoded) {
    const text = decodeURIComponent(encoded);
    document.getElementById('msgInput').value = text;
    sendMessage();
  }

  // ── Session management ───────────────────────────────
  function saveSession(firstMsg) {
    if (!currentId) {
      currentId = Date.now().toString();
      sessions.unshift({ id: currentId, title: firstMsg.slice(0, 48), ts: Date.now() });
      if (sessions.length > 20) sessions = sessions.slice(0, 20);
      localStorage.setItem('ss_ai_sessions', JSON.stringify(sessions));
      renderHistory();
    }
  }

  function renderHistory() {
    const list = document.getElementById('historyList');
    if (!sessions.length) {
      list.innerHTML = '<div style="font-size:.75rem;color:#bbb;padding:8px 4px;">No conversations yet</div>';
      return;
    }
    list.innerHTML = sessions.slice(0, 12).map(s => `
      <div class="history-item ${s.id === currentId ? 'active' : ''}" onclick="loadSession('${s.id}')">
        <i class="fas fa-comment-dots"></i>
        <span class="history-text">${s.title}</span>
      </div>`).join('');
  }

  function loadSession(id) {
    currentId = id;
    renderHistory();
  }
</script>
</body>
</html>
"""

path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_ai_chat.html')
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print("AI chat page written:", len(html), "chars")
