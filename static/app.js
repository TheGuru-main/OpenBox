let currentPhone = localStorage.getItem('openbox_phone') || '';
const API = '/api/v1';

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
  // Initialise the main app
  loadFiles('app');
  loadFiles('game');
  loadFiles('video');
  setupNavigation();
  setupUploadButtons();
}

function setupNavigation() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
      document.getElementById('screen-' + btn.dataset.screen).classList.add('active');
    });
  });

  document.getElementById('btnOpenSidebar').addEventListener('click', () => {
    document.getElementById('sidebar').classList.add('open');
  });
  document.getElementById('btnCloseSidebar').addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('open');
  });
}

function setupUploadButtons() {
  document.getElementById('btnShowUpload').addEventListener('click', showUploadModal);
  document.getElementById('btnShowUploadGames').addEventListener('click', showUploadModal);
  document.getElementById('btnShowUploadVideos').addEventListener('click', showUploadModal);
  document.getElementById('btnUpload').addEventListener('click', uploadFile);
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
      if (f.category === 'video') {
        document.getElementById('videoTitle').textContent = f.filename;
        document.getElementById('videoPlayer').src = `/api/v1/stream/${f.id}`;
        document.getElementById('downloadLink').href = `/api/v1/download/${f.id}`;
        document.getElementById('videoModal').style.display = 'flex';
      } else {
        window.open(`/api/v1/download/${f.id}`, '_blank');
      }
    }
  });
}

function closeVideoModal() {
  document.getElementById('videoModal').style.display = 'none';
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