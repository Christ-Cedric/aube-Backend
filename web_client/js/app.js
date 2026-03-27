const API_BASE = '/v1';

// --- Helper ---
async function safeJson(res) {
    const text = await res.text();
    try {
        return text ? JSON.parse(text) : {};
    } catch (e) {
        throw new Error(`Failed to parse response: ${text.substring(0, 100)}... (Status: ${res.status})`);
    }
}

// --- Auth ---
function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('form').forEach(f => f.classList.add('hidden'));

    if (tab === 'login') {
        document.querySelector('button[onclick="showTab(\'login\')"]').classList.add('active');
        document.getElementById('loginForm').classList.remove('hidden');
    } else {
        document.querySelector('button[onclick="showTab(\'signup\')"]').classList.add('active');
        document.getElementById('signupForm').classList.remove('hidden');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errDiv = document.getElementById('loginError');
    errDiv.textContent = '';

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await safeJson(res);
        if (!res.ok) throw new Error(data.detail || `Login failed: ${res.status}`);

        localStorage.setItem('token', data.access_token);
        window.location.href = 'dashboard.html';
    } catch (err) {
        errDiv.textContent = err.message;
        console.error(err);
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const full_name = document.getElementById('signupName').value;
    const errDiv = document.getElementById('signupError');
    errDiv.textContent = '';

    try {
        const res = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name })
        });

        if (!res.ok) {
            const data = await safeJson(res);
            throw new Error(data.detail || `Signup failed: ${res.status}`);
        }

        alert('Account created! Please login.');
        showTab('login');
    } catch (err) {
        errDiv.textContent = err.message;
        console.error(err);
    }
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}

function checkAuth() {
    if (!localStorage.getItem('token')) {
        window.location.href = 'index.html';
    }
}

// --- Dashboard ---
async function authFetch(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };

    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    if (res.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }
    return res;
}

async function loadProfile() {
    try {
        const res = await authFetch('/user/profile');
        if (!res.ok) throw new Error('Failed to load profile');
        const user = await safeJson(res);

        document.getElementById('navEmail').textContent = user.email;
        document.getElementById('profileData').innerHTML = `
            <p><strong>Name:</strong> ${user.full_name || 'N/A'}</p>
            <p><strong>Email:</strong> ${user.email}</p>
            <p><strong>Joined:</strong> ${new Date(user.created_at).toLocaleDateString()}</p>
        `;
    } catch (err) {
        console.error(err);
        document.getElementById('profileData').textContent = `Error: ${err.message}`;
    }
}

async function loadDevices() {
    try {
        const res = await authFetch('/user/devices');
        if (!res.ok) throw new Error('Failed to load devices');
        const devices = await safeJson(res);
        const list = document.getElementById('deviceList');

        list.innerHTML = devices.map(d => `
            <li class="device-item">
                <div>
                    <strong>${d.device_name}</strong>
                    <span style="color: #666; font-size: 0.8em">(${d.device_type})</span>
                    <br>
                    <small>${d.device_id}</small>
                </div>
                <button onclick="removeDevice('${d.device_id}')" style="color: red; border:none; background:none; cursor:pointer">×</button>
            </li>
        `).join('') || '<li style="padding:1rem; color:#666">No devices added</li>';
    } catch (err) {
        console.error(err);
    }
}

// --- Devices ---
function showAddDevice() {
    document.getElementById('deviceModal').classList.remove('hidden');
}

function closeDeviceModal() {
    document.getElementById('deviceModal').classList.add('hidden');
}

async function addDevice() {
    const name = document.getElementById('newDeviceName').value;
    const id = document.getElementById('newDeviceId').value;
    const type = document.getElementById('newDeviceType').value;

    if (!name || !id || !type) return alert('All fields required');

    try {
        const res = await authFetch('/user/devices', {
            method: 'POST',
            body: JSON.stringify({
                device_name: name,
                device_id: id,
                device_type: type
            })
        });

        if (res.ok) {
            closeDeviceModal();
            loadDevices();
        } else {
            const data = await safeJson(res);
            alert(data.detail || 'Failed to add device');
        }
    } catch (err) {
        alert(err.message);
    }
}

async function removeDevice(deviceId) {
    if (!confirm('Remove this device?')) return;

    try {
        const res = await authFetch(`/user/devices/${deviceId}`, { method: 'DELETE' });
        if (!res.ok) {
            const data = await safeJson(res);
            alert(data.detail || 'Failed to remove device');
        } else {
            loadDevices();
        }
    } catch (err) {
        alert('Failed to remove device');
    }
}

// --- Subs ---
async function requestSub() {
    const deviceId = document.getElementById('devIdRequest').value;
    if (!deviceId) return alert('Enter Device ID');

    try {
        const res = await authFetch('/request_subscription', {
            method: 'POST',
            body: JSON.stringify({
                device_id: deviceId,
                payment_proof: "mock_proof_image"
            })
        });

        const data = await safeJson(res);
        if (res.ok) {
            alert('Request Sent! ID: ' + data.id);
        } else {
            alert(data.detail || 'Request failed');
        }
    } catch (e) {
        console.log(e);
        alert(e.message);
    }
}
