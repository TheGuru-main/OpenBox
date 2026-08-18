let currentPhone = localStorage.getItem('openbox_phone') || '';
const API = '/api/v1';
let currentFileOwner = null;
let activeChatPhone = null;

// Register service worker on page load
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => console.log('SW registered'))
      .catch(err => console.log('SW registration failed', err));
  });
}

// Show signup/login screen if no phone
if (!currentPhone) {
  document.body.innerHTML = `
    <div style="max-width:400px;margin:auto;padding:2rem;">
      <h1>OpenBox</h1>
      <input id="signupName" placeholder="Full name">
      <input id="signupPhone" placeholder="Phone">
      <input id="signupPassword" type="password" placeholder="Password">
      <button onclick="signup()">Sign Up</button>
      <button onclick="login()">Login</button>
    </div>
  `;

  window.signup = async () => {
    const res = await fetch('/api/v1/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: document.getElementById('signupName').value,
        phone: document.getElementById('signupPhone').value,
        password: document.getElementById('signupPassword').value
      })
    });
    if (res.ok) {
      currentPhone = document.getElementById('signupPhone').value;
      localStorage.setItem('openbox_phone', currentPhone);
      location.reload();
    } else {
      alert('Signup failed');
    }
  };

  window.login = async () => {
    const res = await fetch('/api/v1/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone: document.getElementById('signupPhone').value,
        password: document.getElementById('signupPassword').value
      })
    });
    if (res.ok) {
      currentPhone = document.getElementById('signupPhone').value;
      localStorage.setItem('openbox_phone', currentPhone);
      location.reload();
    } else {
      alert('Login failed');
    }
  };
} else {
  // Initialize main app
  loadFiles('app');
  loadFiles('game');
  loadFiles('video');
  setupNavigation();
  setupUploadButtons();
  setupSidebarLinks();
}

function setupNavigation() {
  // Bottom nav
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
      document.getElementById('screen-' + btn.dataset.screen).classList.add('active');
    });
  });

  // Sidebar open/close
  document.getElementById('btnOpenSidebar').addEventListener('click', () => {
    document.getElementById('sidebar').classList.add('open');
  });
  document.getElementById('btnCloseSidebar').addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('open');
  });
}

function setupSidebarLinks() {
  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const screen = link.dataset.screen;
      document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
      document.getElementById('screen-' + screen).classList.add('active');
      document.getElementById('sidebar').classList.remove('open');
      if (screen === 'messages') {
        loadConversations();
      }
    });
  });
}

function setupUploadButtons() {
  document.getElementById('btnShowUpload').addEventListener('click', showUploadModal);
  document.getElementById('btnShowUploadGames').addEventListener('click', showUploadModal);
  document.getElementById('btnShowUploadVideos').addEventListener('click', showUploadModal);
  document.getElementById('btnUpload').addEventListener('click', uploadFile);
  document.getElementById('btnMessageOwner').addEventListener('click', messageOwnerFromFile);
}

async function loadFiles(category) {
  const res = await fetch(`/api/v1/files?category=${category}`);
  const files = await res.json();
  const container = document.getElementById(category + 'sContainer');
  container.innerHTML = files.map(f => `
    <div class="card" onclick="openFileDetails('${f.id}')">
      <h3>${f.filename}</h3>
      <small>${String.fromCharCode(65+f.gsp_col)}${f.gsp_row} · ${f.size_bytes} bytes</small>
      <br><small>Price: $${f.price}</small>
    </div>
  `).join('') || '<p>No files</p>';
}

function openFileDetails(fileId) {
  fetch('/api/v1/files').then(r => r.json()).then(files => {
    const f = files.find(x => x.id === fileId);
    if (f) {
      currentFileOwner = f.uploaded_by;
      document.getElementById('fileTitle').textContent = f.filename;
      document.getElementById('fileDetails').innerHTML = `
        <p><strong>Category:</strong> ${f.category}</p>
        <p><strong>Size:</strong> ${f.size_bytes} bytes</p>
        <p><strong>Grid:</strong> ${String.fromCharCode(65+f.gsp_col)}${f.gsp_row}</p>
        <p><strong>Price:</strong> $${f.price}</p>
        <p><strong>Uploader:</strong> ${f.uploaded_by}</p>
        <p><strong>Description:</strong> ${f.description || 'None'}</p>
      `;
      document.getElementById('downloadLink').href = `/api/v1/download/${f.id}`;
      if (f.category === 'video') {
        document.getElementById('videoPlayer').style.display = 'block';
        document.getElementById('videoPlayer').src = `/api/v1/stream/${f.id}`;
      } else {
        document.getElementById('videoPlayer').style.display = 'none';
        document.getElementById('videoPlayer').src = '';
      }
      document.getElementById('fileModal').style.display = 'flex';
    }
  });
}

function closeFileModal() {
  document.getElementById('fileModal').style.display = 'none';
  document.getElementById('videoPlayer').pause();
  document.getElementById('videoPlayer').src = '';
}

function showUploadModal() {
  document.getElementById('uploadModal').style.display = 'flex';
}

function closeUploadModal() {
  document.getElementById('uploadModal').style.display = 'none';
}

async function uploadFile() {
  const fileInput = document.getElementById('fileInput');
  const category = document.getElementById('uploadCategory').value;
  const price = document.getElementById('price').value || '0';
  const description = document.getElementById('description').value;

  if (!fileInput.files.length) return alert('Choose a file');
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('uploaded_by', currentPhone);
  formData.append('category', category);
  formData.append('price', price);
  formData.append('description', description);

  const res = await fetch('/api/v1/upload', { method: 'POST', body: formData });
  const data = await res.json();
  if (res.ok) {
    document.getElementById('uploadResult').textContent =
      'Uploaded! Grid: ' + String.fromCharCode(65 + data.gsp_col) + data.gsp_row;
    closeUploadModal();
    loadFiles(category);
  } else {
    document.getElementById('uploadResult').textContent =
      'Upload failed: ' + (data.detail || JSON.stringify(data));
  }
}

// Messaging functions
function messageOwnerFromFile() {
  if (currentFileOwner) {
    closeFileModal();
    navigateToChat(currentFileOwner);
  }
}

function navigateToChat(phone) {
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-messages').classList.add('active');
  document.getElementById('sidebar').classList.remove('open');
  loadConversations();
  openChat(phone);
}

async function loadConversations() {
  const res = await fetch('/api/v1/conversations', {
    headers: {'X-User-Phone': currentPhone}
  });
  if (res.ok) {
    const data = await res.json();
    const container = document.getElementById('conversationList');
    if (data.phones && data.phones.length) {
      container.innerHTML = data.phones.map(p => `
        <div class="conversation-item" onclick="openChat('${p}')">📱 ${p}</div>
      `).join('');
    } else {
      container.innerHTML = '<p>No conversations yet.</p>';
    }
  }
}

function openChat(phone) {
  activeChatPhone = phone;
  document.getElementById('conversationList').style.display = 'none';
  document.getElementById('chatView').style.display = 'block';
  document.getElementById('chatPartner').textContent = phone;
  loadChatMessages(phone);
}

function closeChat() {
  document.getElementById('chatView').style.display = 'none';
  document.getElementById('conversationList').style.display = 'block';
  activeChatPhone = null;
}

async function loadChatMessages(phone) {
  const res = await fetch(`/api/v1/messages?with_phone=${phone}`, {
    headers: {'X-User-Phone': currentPhone}
  });
  const messages = await res.json();
  const container = document.getElementById('chatMessages');
  container.innerHTML = messages.map(msg => `
    <div class="chat-message ${msg.from_phone === currentPhone ? 'sent' : 'received'}">
      ${msg.body}
      <small>${new Date(msg.created_at).toLocaleString()}</small>
    </div>
  `).join('');
}

async function sendMessage() {
  const input = document.getElementById('messageInput');
  const body = input.value.trim();
  if (!body || !activeChatPhone) return;
  await fetch('/api/v1/messages', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({from_phone: currentPhone, to_phone: activeChatPhone, body})
  });
  input.value = '';
  loadChatMessages(activeChatPhone);
}