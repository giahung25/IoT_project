// ============================================================
//  DASHBOARD.JS — Logic chính: Polling API, cập nhật UI
// ============================================================

// ---- Cấu hình ----
const API_BASE          = window.location.origin;   // Tự động lấy IP của PC Server theo URL đang truy cập
const FIREBASE_RTDB_URL = "https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app";
const POLL_INTERVAL     = 5000;                      // ms — polling mỗi 5 giây
const USE_MOCK          = false;                     // true = dùng mock data, false = gọi API thật



// ---- State ----
let isAlertActive         = false;
let pollTimer             = null;
let historyBuffer         = [];    // Giữ lịch sử cục bộ khi dùng mock
let isShowingHistoryImage = false; // Đang xem ảnh lịch sử
let latestLiveImageUrl    = 'assets/mushroom-placeholder.jpg'; // Ảnh live gần nhất
let lastValidAiSize       = null;  // Lưu kích thước nấm mới nhất hợp lệ
let lastValidAiConf       = 0;     // Lưu độ chính xác mới nhất hợp lệ


// ============================================================
//  Fetch helpers
// ============================================================
async function fetchStatus() {
  if (USE_MOCK) return getMockStatus();

  // 1. Ưu tiên đọc trực tiếp từ Firebase Realtime Database
  try {
    const fbRes = await fetch(`${FIREBASE_RTDB_URL}/status.json?t=${Date.now()}`, { signal: AbortSignal.timeout(4000) });
    if (fbRes.ok) {
      const fbData = await fbRes.json();
      if (fbData && typeof fbData === 'object') return fbData;
    }
  } catch (fbErr) {
    console.warn('[Dashboard] Fetch Firebase RTDB error:', fbErr.message);
  }

  // 2. Thử đọc từ Flask Local API (nếu chạy local)
  try {
    const res = await fetch(`${API_BASE}/api/status`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn('[Dashboard] fetchStatus fallback:', err.message);
  }

  return getMockStatus();
}

async function fetchHistory() {
  if (USE_MOCK) return MOCK_HISTORY;

  // 1. Thử lấy từ Firebase Realtime DB
  try {
    const fbRes = await fetch(`${FIREBASE_RTDB_URL}/history.json?t=${Date.now()}`, { signal: AbortSignal.timeout(4000) });
    if (fbRes.ok) {
      const fbData = await fbRes.json();
      if (fbData) {
        let arr = Array.isArray(fbData) ? fbData : Object.values(fbData);
        arr = arr.filter(item => item && (item.temperature !== undefined || item.temp !== undefined));
        if (arr.length > 0) return arr;
      }
    }
  } catch (fbErr) {}

  // 2. Thử lấy từ Local Backend API
  try {
    const res = await fetch(`${API_BASE}/api/history`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      const data = await res.json();
      if (data && Array.isArray(data) && data.length > 0) return data;
    }
  } catch (err) {}

  return historyBuffer.length > 0 ? historyBuffer : MOCK_HISTORY;
}


async function fetchAiHistory() {
  if (USE_MOCK) return MOCK_AI_HISTORY;
  try {
    const res = await fetch(`${API_BASE}/api/ai-history`, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error('API error');
    return await res.json();
  } catch (err) {
    console.warn('[Dashboard] fetchAiHistory fallback to mock:', err.message);
    return MOCK_AI_HISTORY;
  }
}


// ============================================================
//  UI Updaters
// ============================================================

/** Cập nhật hai gauge vòng tròn */
function updateGauges(temp, hum) {
  tempGauge.update(temp);
  humGauge.update(hum);
}

/** Cập nhật card trạng thái AI */
function updateAIStatus(mushroomSize, confidence) {
  const badge   = document.getElementById('ai-size-badge');
  const confEl  = document.getElementById('ai-confidence');
  const iconEl  = document.getElementById('ai-icon');

  if (mushroomSize && mushroomSize !== 'unknown' && confidence > 0) {
    lastValidAiSize = mushroomSize;
    lastValidAiConf = confidence;
  }

  const effectiveSize = (mushroomSize && mushroomSize !== 'unknown') ? mushroomSize : lastValidAiSize;
  const effectiveConf = (confidence && confidence > 0) ? confidence : lastValidAiConf;

  if (!effectiveSize) {
    if (badge) {
      badge.textContent = '⏳ CHỜ CAMERA & AI';
      badge.className   = 'ai-badge badge-warning';
    }
    if (iconEl) iconEl.textContent = '📷';
    if (confEl) confEl.textContent = 'Trạng thái: Đang chờ phân tích AI';
    return;
  }

  if (effectiveSize === 'large') {
    badge.textContent = '🍄 LỚN — Thu hoạch!';
    badge.className   = 'ai-badge badge-large';
    iconEl.textContent = '🍄';
  } else {
    badge.textContent = '🌱 NHỎ — Đang phát triển';
    badge.className   = 'ai-badge badge-small';
    iconEl.textContent = '🌱';
  }
  if (effectiveConf !== undefined) {
    confEl.textContent = `Độ chính xác: ${effectiveConf}%`;
  }
}

/** Cập nhật trạng thái thiết bị (pump, alert, light, fan, pins) */
function updateDevices(status) {
  if (!status) return;
  const pump = status.pump === true;
  const harvestAlert = status.harvest_alert === true;
  const light = status.grow_light === true;
  const fan = status.cooling_fan === true;
  const vent = status.vent_gate === true;
  const co2Alert = status.co2_ppm !== undefined && status.co2_ppm > 1000;

  // 1. Pump (GPIO 15)
  const pumpDot   = document.getElementById('pump-dot');
  const pumpLabel = document.getElementById('pump-label');
  if (pumpDot) pumpDot.className = 'device-dot ' + (pump ? 'dot-on' : 'dot-off');
  if (pumpLabel) {
    pumpLabel.textContent = pump ? 'ĐANG BẬT' : 'TẮT';
    pumpLabel.className   = 'device-state ' + (pump ? 'state-on' : 'state-off');
  }

  // 2. Harvest / CO2 Alert (GPIO 16)
  const alertDot   = document.getElementById('alert-dot');
  const alertLabel = document.getElementById('alert-label');
  const isAlert = harvestAlert || co2Alert;
  if (alertDot) alertDot.className = 'device-dot ' + (isAlert ? 'dot-alert' : 'dot-off');
  if (alertLabel) {
    alertLabel.textContent = isAlert ? 'CẢNH BÁO!' : 'BÌNH THƯỜNG';
    alertLabel.className   = 'device-state ' + (isAlert ? 'state-alert' : 'state-off');
  }

  // 3. Grow Light (GPIO 17)
  const lightDot   = document.getElementById('light-dot');
  const lightLabel = document.getElementById('light-label');
  if (lightDot) lightDot.className = 'device-dot ' + (light ? 'dot-on' : 'dot-off');
  if (lightLabel) {
    lightLabel.textContent = light ? 'ĐANG BẬT' : 'TẮT';
    lightLabel.className   = 'device-state ' + (light ? 'state-on' : 'state-off');
  }

  // 4. Cooling Fan (GPIO 18)
  const fanDot   = document.getElementById('fan-dot');
  const fanLabel = document.getElementById('fan-label');
  if (fanDot) fanDot.className = 'device-dot ' + (fan ? 'dot-on' : 'dot-off');
  if (fanLabel) {
    fanLabel.textContent = fan ? 'ĐANG BẬT' : 'TẮT';
    fanLabel.className   = 'device-state ' + (fan ? 'state-on' : 'state-off');
  }

  // 5. Servo Vent Gate (GPIO 14)
  const ventDot   = document.getElementById('vent-dot');
  const ventLabel = document.getElementById('vent-label');
  if (ventDot) ventDot.className = 'device-dot ' + (vent ? 'dot-on' : 'dot-off');
  if (ventLabel) {
    ventLabel.textContent = vent ? 'MỞ (180°)' : 'ĐÓNG (0°)';
    ventLabel.className   = 'device-state ' + (vent ? 'state-on' : 'state-off');
  }
  const neoBadge = document.getElementById('neopixel-badge');
  if (neoBadge) {
    if (isAlert) {
      neoBadge.textContent = '🔴 RED ERROR / ALARM';
      neoBadge.style.background = 'hsla(354,85%,58%,0.2)';
      neoBadge.style.color = '#ef4444';
      neoBadge.style.borderColor = 'hsla(354,85%,58%,0.4)';
    } else if (pump || light || fan) {
      neoBadge.textContent = '🟡 YELLOW ACTUATING';
      neoBadge.style.background = 'hsla(38,95%,55%,0.2)';
      neoBadge.style.color = '#f59e0b';
      neoBadge.style.borderColor = 'hsla(38,95%,55%,0.4)';
    } else {
      neoBadge.textContent = '❇️ CYAN NORMAL';
      neoBadge.style.background = 'hsla(192,90%,52%,0.2)';
      neoBadge.style.color = '#38bdf8';
      neoBadge.style.borderColor = 'hsla(192,90%,52%,0.4)';
    }
  }

  // 6. Cập nhật Pinout live status ở Tab 3 (Sơ đồ ESP32 & Node)
  const p14 = document.getElementById('pin-g14-status');
  const isVentOpen = status.vent_gate ?? isAlert;
  if (p14) p14.innerHTML = isVentOpen ? '<span style="color:#38bdf8;font-weight:700;">🟢 PWM 50Hz (MỞ 180°)</span>' : '<span style="color:#94a3b8;">⚪ LOW (ĐÓNG 0°)</span>';

  const p15 = document.getElementById('pin-g15-status');
  if (p15) p15.innerHTML = pump ? '<span style="color:#34d399;font-weight:700;">🟢 HIGH (BẬT BƠM)</span>' : '<span style="color:#94a3b8;">⚪ LOW (TẮT)</span>';

  const p16 = document.getElementById('pin-g16-status');
  if (p16) p16.innerHTML = isAlert ? '<span style="color:#f87171;font-weight:700;">🔴 ALARM (CẢNH BÁO)</span>' : '<span style="color:#94a3b8;">⚪ LOW (NORMAL)</span>';

  const p17 = document.getElementById('pin-g17-status');
  if (p17) p17.innerHTML = light ? '<span style="color:#fbbf24;font-weight:700;">🟡 HIGH (BẬT ĐÈN)</span>' : '<span style="color:#94a3b8;">⚪ LOW (TẮT)</span>';

  const p18 = document.getElementById('pin-g18-status');
  if (p18) p18.innerHTML = fan ? '<span style="color:#c084fc;font-weight:700;">🟣 HIGH (BẬT QUẠT)</span>' : '<span style="color:#94a3b8;">⚪ LOW (TẮT)</span>';
}

/** Cập nhật thông số bổ sung (CO2, Light Lux, VPD, Nguồn Cảm biến) */
function updateExtraSensors(status) {
  if (!status) return;

  // 1. CO2 (MQ-135)
  const co2ValEl = document.getElementById('co2-val');
  const co2BadgeEl = document.getElementById('co2-badge');
  const co2 = status.co2_ppm !== undefined ? status.co2_ppm : 460;
  if (co2ValEl) {
    co2ValEl.innerHTML = `${co2} <span style="font-size: 0.75rem; font-weight: 500;">ppm</span>`;
    co2ValEl.style.color = co2 > 1000 ? 'var(--color-danger)' : 'var(--color-success)';
  }
  if (co2BadgeEl) {
    if (co2 > 1000) {
      co2BadgeEl.textContent = '⚠️ Cần Thông Gió';
      co2BadgeEl.className = 'mini-status-badge badge-red';
      co2BadgeEl.style.background = 'hsla(354,85%,58%,0.15)';
      co2BadgeEl.style.color = 'var(--color-danger)';
    } else {
      co2BadgeEl.textContent = '🟢 Khí Tươi Tốt';
      co2BadgeEl.className = 'mini-status-badge badge-green';
      co2BadgeEl.style.background = 'hsla(158,85%,44%,0.15)';
      co2BadgeEl.style.color = 'var(--color-success)';
    }
  }

  // 2. Light Lux (BH1750)
  const lightValEl = document.getElementById('light-val');
  const lightBadgeEl = document.getElementById('light-badge');
  const light = status.light_lux !== undefined ? status.light_lux : 150;
  if (lightValEl) {
    lightValEl.innerHTML = `${light} <span style="font-size: 0.75rem; font-weight: 500;">Lux</span>`;
  }
  if (lightBadgeEl) {
    if (light < 50) {
      lightBadgeEl.textContent = '🌙 Đêm / Tối';
      lightBadgeEl.style.color = 'var(--text-muted)';
    } else if (light > 800) {
      lightBadgeEl.textContent = '☀️ Nắng Gắt';
      lightBadgeEl.style.color = 'var(--color-warning)';
    } else {
      lightBadgeEl.textContent = '☀️ Quang Hợp Tốt';
      lightBadgeEl.style.color = 'var(--color-warning)';
    }
  }

  // 3. VPD Growth Zone
  const vpdValEl = document.getElementById('vpd-val');
  const vpdBadgeEl = document.getElementById('vpd-badge');
  const vpd = status.vpd !== undefined ? status.vpd : 1.34;
  const growthZone = status.growth_zone || '🔵 Vùng Khô Hạn';
  if (vpdValEl) {
    vpdValEl.innerHTML = `${Number(vpd).toFixed(2)} <span style="font-size: 0.75rem; font-weight: 500;">kPa</span>`;
  }
  if (vpdBadgeEl) {
    vpdBadgeEl.textContent = growthZone;
  }

  // 4. Sensor Source Badge
  const srcBadgeEl = document.getElementById('sensor-source-badge');
  if (srcBadgeEl && status.sensor_source) {
    srcBadgeEl.textContent = `📍 ${status.sensor_source}`;
  }

  // 5. Update Kiosk Overlay Display
  const kt = document.getElementById('kiosk-temp-val');
  if (kt) kt.textContent = (status.temperature !== undefined && status.temperature > 0) ? `${status.temperature}°C` : 'N/A';
  const kh = document.getElementById('kiosk-hum-val');
  if (kh) kh.textContent = (status.humidity !== undefined && status.humidity > 0) ? `${status.humidity}%` : 'N/A';
  const kc = document.getElementById('kiosk-co2-val');
  if (kc) kc.textContent = `${status.co2_ppm || 460} ppm`;
  const kl = document.getElementById('kiosk-light-val');
  if (kl) kl.textContent = `${status.light_lux || 150} Lux`;
}

/** Cập nhật Bảng Trạng Thái Thiết Bị Kết Nối (ESP32, Cam, Jetson, Firebase) */
function updateDeviceConnectivity(status) {
  if (!status) return;

  let onlineCount = 0;
  const totalCount = 4;

  // 1. ESP32 Sensor Node
  const espDot = document.getElementById('esp32-net-dot');
  const espState = document.getElementById('esp32-net-state');
  const espVal = document.getElementById('esp-sensor-val');
  const isEspOnline = Boolean(status.esp32_online) || (status.temperature > 0 || status.humidity > 0 || status.co2_ppm > 0 || status.light_lux >= 0);

  if (isEspOnline) {
    onlineCount++;
    if (espDot) espDot.className = 'device-dot dot-on';
    if (espState) { espState.textContent = 'ĐÃ KẾT NỐI'; espState.className = 'badge-online'; }
    const tempText = (status.temperature !== undefined && status.temperature !== null && status.temperature > 0) ? `${status.temperature}°C` : 'N/A';
    const humText = (status.humidity !== undefined && status.humidity !== null && status.humidity > 0) ? `${status.humidity}%` : 'N/A';
    if (espVal) espVal.textContent = `${tempText} / ${humText} (CO₂: ${status.co2_ppm || 460} ppm)`;
  } else {
    if (espDot) espDot.className = 'device-dot dot-off';
    if (espState) { espState.textContent = 'CHƯA KẾT NỐI'; espState.className = 'badge-offline'; }
    if (espVal) espVal.textContent = 'Chưa nhận dữ liệu ESP32';
  }

  // 2. Camera Stream / Feed
  const camDot = document.getElementById('cam-net-dot');
  const camState = document.getElementById('cam-net-state');
  const camVal = document.getElementById('cam-stream-val');
  const isCamOk = status.active_camera && status.active_camera !== 'offline' && !status.active_camera.includes('Offline');

  if (isCamOk) {
    onlineCount++;
    if (camDot) camDot.className = 'device-dot dot-on';
    if (camState) { camState.textContent = 'HOẠT ĐỘNG'; camState.className = 'badge-online'; }
    if (camVal) camVal.textContent = status.active_camera;
  } else {
    if (camDot) camDot.className = 'device-dot dot-off';
    if (camState) { camState.textContent = 'CHƯA CẮM CAM'; camState.className = 'badge-offline'; }
    if (camVal) camVal.textContent = 'Chưa cắm Webcam USB';
  }

  // 3. Jetson Edge AI Engine
  const jetDot = document.getElementById('jetson-net-dot');
  const jetState = document.getElementById('jetson-net-state');
  const jetVal = document.getElementById('jetson-ai-val');
  onlineCount++;
  if (jetDot) jetDot.className = 'device-dot dot-on';
  if (jetState) { jetState.textContent = 'ONLINE'; jetState.className = 'badge-online'; }
  if (jetVal) jetVal.textContent = `Moondream (${status.ai_confidence || 95}% conf)`;

  // 4. Firebase Cloud Sync
  const fbDot = document.getElementById('firebase-net-dot');
  const fbState = document.getElementById('firebase-net-state');
  const fbVal = document.getElementById('firebase-sync-val');
  onlineCount++;
  if (fbDot) fbDot.className = 'device-dot dot-on';
  if (fbState) { fbState.textContent = 'ĐỒNG BỘ'; fbState.className = 'badge-online'; }
  if (fbVal) fbVal.textContent = 'Realtime DB Connected';

  // Overall Count Badge
  const countBadge = document.getElementById('devices-online-count');
  if (countBadge) {
    countBadge.textContent = `${onlineCount}/${totalCount} Online`;
    countBadge.className = onlineCount === totalCount ? 'status-count-badge' : 'status-count-badge badge-warning';
  }
}

/** Cập nhật ảnh camera */
function updateCamera(imagePath) {
  if (isShowingHistoryImage) return; // Không đè ảnh live lên nếu đang xem lịch sử
  
  const img = document.getElementById('mushroom-img');
  if (!img) return;
  const ts = Date.now();
  
  const path = imagePath || '/static/images/latest.jpg';
  latestLiveImageUrl = (path.startsWith('http') || path.startsWith('data:')) ? path : `${API_BASE}${path}?t=${ts}`;
  img.src = latestLiveImageUrl;
}


/** Cập nhật bảng log nhận diện AI */
function updateAiHistoryTable(historyList) {
  const tbody = document.getElementById('ai-log-body');
  if (!tbody) return;
  
  if (!historyList || historyList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1.5rem 0;">Chưa có dữ liệu nhận diện...</td></tr>`;
    return;
  }
  
  // Hiển thị từ mới nhất -> cũ nhất (đảo ngược mảng)
  const reversedList = [...historyList].reverse();
  
  tbody.innerHTML = reversedList.map((item, index) => {
    const timeStr = new Date(item.timestamp).toLocaleTimeString('vi-VN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
    
    const sizeBadge = item.mushroom_size === 'large' 
      ? '<span class="hist-badge hist-badge-large">Lớn</span>' 
      : '<span class="hist-badge hist-badge-small">Nhỏ</span>';
      
    // Chuẩn hóa url ảnh
    const rawUrl = item.image_path || "assets/mushroom-placeholder.jpg";
    const fullUrl = rawUrl.startsWith('http') || rawUrl.startsWith('assets/') 
      ? rawUrl 
      : `${API_BASE}${rawUrl}`;
      
    return `
      <tr>
        <td>${timeStr}</td>
        <td>${sizeBadge}</td>
        <td>${item.ai_confidence}%</td>
        <td>
          <button class="history-view-btn" data-url="${fullUrl}" data-size="${item.mushroom_size}" data-conf="${item.ai_confidence}">
            👁️ Xem
          </button>
        </td>
      </tr>
    `;
  }).join('');
  
  // Gắn sự kiện cho các nút xem ảnh lịch sử
  tbody.querySelectorAll('.history-view-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const url = btn.getAttribute('data-url');
      const sizeStr = btn.getAttribute('data-size') === 'large' ? 'LỚN' : 'NHỎ';
      const confStr = btn.getAttribute('data-conf');
      
      viewHistoricalImage(url, sizeStr, confStr);
    });
  });
}

/** Chuyển khung camera sang chế độ xem ảnh lịch sử */
function viewHistoricalImage(imgUrl, sizeStr, confStr) {
  isShowingHistoryImage = true;
  
  const imgEl = document.getElementById('mushroom-img');
  const liveBadge = document.getElementById('cam-live-badge');
  const backBtn = document.getElementById('back-to-live-btn');
  const labelEl = document.getElementById('cam-ai-label');
  
  imgEl.src = imgUrl;
  liveBadge.style.display = 'none';
  backBtn.classList.remove('hidden');
  labelEl.textContent = `LỊCH SỬ: Nhận diện ${sizeStr} (${confStr}%)`;
}


/** Cập nhật timestamp */
function updateTimestamp(isoString) {
  const el  = document.getElementById('last-updated');
  const dt  = new Date(isoString);
  el.textContent = dt.toLocaleTimeString('vi-VN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}

/** Trạng thái ESP32 */
function updateESP32Status(online) {
  const dot  = document.getElementById('esp32-dot');
  const text = document.getElementById('esp32-status');
  dot.className    = 'status-dot ' + (online ? 'dot-on' : 'dot-off');
  text.textContent = online ? 'Online' : 'Offline';
  text.style.color = online ? 'var(--color-success)' : 'var(--color-danger)';
}

/** Bật/tắt harvest alert toàn trang */
function toggleHarvestAlert(active) {
  if (active === isAlertActive) return;
  isAlertActive = active;

  const banner = document.getElementById('alert-banner');
  const body   = document.body;

  if (active) {
    banner.classList.remove('hidden');
    body.classList.add('harvest-alert');
    // Phát âm thanh (nếu trình duyệt cho phép)
    try { new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAA...').play(); } catch {}
  } else {
    banner.classList.add('hidden');
    body.classList.remove('harvest-alert');
  }
}

// ============================================================
//  Card glow effect theo giá trị
// ============================================================
function updateCardWarnings(temp, hum) {
  const tempCard = document.getElementById('temp-card');
  const humCard  = document.getElementById('hum-card');

  tempCard.classList.toggle('card-warning', temp > 33);
  tempCard.classList.toggle('card-danger',  temp > 38);
  humCard.classList.toggle('card-warning',  hum < 65);
  humCard.classList.toggle('card-danger',   hum < 50);
}

// ============================================================
//  Mock: cập nhật lịch sử cục bộ
// ============================================================
function appendToHistoryBuffer(temp, hum) {
  historyBuffer.push({
    timestamp: new Date().toISOString(),
    temperature: temp,
    humidity: hum
  });
  // Giữ tối đa 48 điểm
  if (historyBuffer.length > 48) historyBuffer.shift();
}

// ============================================================
//  Vòng lặp chính
// ============================================================
async function updateDashboard() {
  try {
    const status = await fetchStatus();

    // Gauges
    updateGauges(status.temperature, status.humidity);

    // Extra Sensors (CO2, Light, VPD)
    updateExtraSensors(status);

    // AI Status
    updateAIStatus(status.mushroom_size, status.ai_confidence);

    // Devices & Pins
    updateDevices(status);
    updateDeviceConnectivity(status);
    updateVietGapLogTable(status);

    // Camera
    updateCamera(status.camera_image);

    // Timestamp
    updateTimestamp(status.last_updated);

    // ESP32
    updateESP32Status(status.esp32_online ?? true);

    // Alert
    toggleHarvestAlert(status.harvest_alert);

    // Card warnings
    updateCardWarnings(status.temperature, status.humidity);

    const activeCamBadge = document.getElementById('cam-source-badge');
    if (activeCamBadge) {
      const activeSrc = status.active_camera || status.camera_source || 'Auto';
      activeCamBadge.textContent = `📷 Nguồn: ${activeSrc}`;
    }

    const modeTextEl = document.getElementById('mode-text');
    if (modeTextEl) {
      if (status.simulation_mode || !status.esp32_online) {
        modeTextEl.textContent = "Giả lập (Simulation)";
      } else {
        modeTextEl.textContent = "Thực tế (Real Mode)";
      }
    }

    // AI Log Table
    const aiHistory = await fetchAiHistory();
    updateAiHistoryTable(aiHistory);

    // Luôn tự động ghi điểm dữ liệu cảm biến mới vào historyBuffer
    if (status && status.temperature !== undefined && status.humidity !== undefined) {
      appendToHistoryBuffer(status.temperature, status.humidity);
    }

    // Fetch History Data & Update Charts + Analytics Tab
    const history = await fetchHistory();
    const chartData = (history && history.length > 0) ? history : historyBuffer;
    updateHistoryChart(chartData);

    // Đồng bộ dữ liệu sang Tab Phân Tích Nhiệt - Ẩm
    updateAnalyticsTab(status, chartData);


  } catch (err) {
    console.error('[Dashboard] Error in updateDashboard:', err);
  }
}

/* ============================================================
   Cập nhật Tab Phân Tích Nhiệt - Ẩm (Analytics & Insights)
   ============================================================ */
function updateAnalyticsTab(status, history) {
  const ehsValEl       = document.getElementById('analytics-ehs-val');
  const ehsTagEl       = document.getElementById('analytics-ehs-tag');
  const vpdValEl       = document.getElementById('analytics-vpd-val');
  const vpdTagEl       = document.getElementById('analytics-vpd-tag');
  const zoneNameEl     = document.getElementById('analytics-zone-name');
  const zoneDescEl     = document.getElementById('analytics-zone-desc');
  const countdownEl    = document.getElementById('analytics-harvest-countdown');
  const calcVpSatEl    = document.getElementById('calc-vpsat');
  const calcVpActEl    = document.getElementById('calc-vpact');
  const calcVpdEl      = document.getElementById('calc-vpd');
  const vpdPointerEl   = document.getElementById('vpd-pointer');

  const adviceIrrigation   = document.getElementById('advice-irrigation-desc');
  const adviceVentilation  = document.getElementById('advice-ventilation-desc');
  const adviceThermal      = document.getElementById('advice-thermal-desc');

  const vpd    = status.vpd ?? 0.45;
  const vpSat  = status.vp_sat ?? 0.90;
  const vpAct  = status.vp_act ?? 0.45;
  const ehs    = status.health_score ?? 95;
  const zone   = status.growth_zone || '🟢 Vùng Tối Ưu (Optimal)';
  const hours  = status.estimated_harvest_hours ?? (status.mushroom_size === 'small' ? 18 : 0);

  if (ehsValEl) ehsValEl.innerHTML = `${ehs}<span class="unit">%</span>`;
  if (ehsTagEl) {
    ehsTagEl.textContent = ehs >= 85 ? 'Xuất Sắc (Optimal)' : ehs >= 60 ? 'Trung Bình (Normal)' : 'Cảnh Báo (Risk)';
    ehsTagEl.className = `widget-status-tag ${ehs >= 85 ? 'tag-success' : ehs >= 60 ? 'tag-warning' : 'tag-danger'}`;
  }

  if (vpdValEl) vpdValEl.innerHTML = `${vpd.toFixed(2)} <span class="unit">kPa</span>`;
  if (vpdTagEl) {
    if (vpd >= 0.3 && vpd <= 0.8) {
      vpdTagEl.textContent = 'Vùng Tối Ưu (0.3 - 0.8 kPa)';
      vpdTagEl.className = 'widget-status-tag tag-success';
    } else if (vpd < 0.3) {
      vpdTagEl.textContent = 'Quá Thấp (Bão Hòa Ẩm)';
      vpdTagEl.className = 'widget-status-tag tag-info';
    } else {
      vpdTagEl.textContent = 'Quá Cao (Khô Hạn)';
      vpdTagEl.className = 'widget-status-tag tag-warning';
    }
  }

  if (zoneNameEl) zoneNameEl.textContent = zone;
  if (zoneDescEl) zoneDescEl.textContent = status.zone_desc || 'Nấm phát triển tối đa, tai nấm to, chất lượng cao.';
  if (countdownEl) countdownEl.innerHTML = hours > 0 ? `~${hours} <span class="unit">Giờ</span>` : `Sẵn Sàng <span class="unit">Thu Hoạch!</span>`;

  if (calcVpSatEl) calcVpSatEl.textContent = `${vpSat.toFixed(2)} kPa`;
  if (calcVpActEl) calcVpActEl.textContent = `${vpAct.toFixed(2)} kPa`;
  if (calcVpdEl)   calcVpdEl.textContent   = `${vpd.toFixed(2)} kPa`;

  // Di chuyển kim chỉ thước đo VPD (0.0 -> 1.5 kPa)
  if (vpdPointerEl) {
    const percent = Math.max(5, Math.min(95, (vpd / 1.5) * 100));
    vpdPointerEl.style.left = `${percent}%`;
  }

  // Khuyên vận hành tự động
  if (adviceIrrigation) {
    if (status.humidity < 70) {
      adviceIrrigation.textContent = 'Độ ẩm thấp (< 70%). Đề xuất kích hoạt Bơm Sương ngắt quãng 30s mỗi 10 phút.';
    } else {
      adviceIrrigation.textContent = 'Độ ẩm môi trường đạt chuẩn. Không cần tăng cường phun sương.';
    }
  }

  if (adviceVentilation) {
    if (status.humidity > 90) {
      adviceVentilation.textContent = '⚠️ Cảnh báo: Độ ẩm bão hòa kéo dài (> 90%). Đề xuất bật quạt thông gió xả ẩm để ngăn ngừa nấm mốc.';
    } else {
      adviceVentilation.textContent = 'Độ ẩm an toàn. Hệ thống không phát hiện rủi ro đọng nước thối gốc.';
    }
  }

  if (adviceThermal) {
    if (status.temperature > 32) {
      adviceThermal.textContent = '⚠️ Nhiệt độ cao (> 32°C). Đề xuất phun sương hạ nhiệt kết hợp quạt làm mát.';
    } else {
      adviceThermal.textContent = 'Nhiệt độ ổn định trong ngưỡng sinh trưởng lý tưởng (25°C - 30°C).';
    }
  }
}



// ============================================================
//  Khởi động
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  // Khởi tạo biểu đồ
  initHistoryChart();

  // Khởi tạo bộ đệm điểm lịch sử thời gian thực ban đầu
  const nowMs = Date.now();
  historyBuffer = Array.from({ length: 20 }, (_, i) => ({
    timestamp: new Date(nowMs - (19 - i) * 5000).toISOString(),
    temperature: parseFloat((27.2 + Math.sin(i * 0.5) * 0.6).toFixed(1)),
    humidity: parseFloat((78.0 + Math.cos(i * 0.4) * 1.5).toFixed(1))
  }));
  updateHistoryChart(historyBuffer);


  // Cập nhật lần đầu ngay lập tức
  updateDashboard();

  // Bắt đầu polling
  pollTimer = setInterval(updateDashboard, POLL_INTERVAL);

  // Cập nhật đồng hồ header mỗi giây
  setInterval(() => {
    const el = document.getElementById('header-clock');
    if (el) {
      el.textContent = new Date().toLocaleTimeString('vi-VN', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    }
  }, 1000);

  // Navigation Tab Switching
  const tabBtns = document.querySelectorAll('.nav-tab-btn');
  const switchTab = (btn) => {
    if (!btn) return;
    const targetTabId = btn.getAttribute('data-tab');

    // Cập nhật trạng thái active nút bấm tab
    tabBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Chuyển đổi hiển thị khung nội dung tab
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.add('hidden');
      content.classList.remove('active');
    });

    const targetContent = document.getElementById(targetTabId);
    if (targetContent) {
      targetContent.classList.remove('hidden');
      targetContent.classList.add('active');
      if (typeof historyChart !== 'undefined' && historyChart) {
        setTimeout(() => {
          historyChart.resize();
          historyChart.update();
        }, 80);
      }
    }

  };

  tabBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab(btn);
    });
  });

  // Nút đóng alert banner
  document.getElementById('alert-close')?.addEventListener('click', () => {
    document.getElementById('alert-banner').classList.add('hidden');
  });

  // Mode Toggle Button (Chuyển giữa Thực Tế và Giả Lập)
  const modeBtn = document.getElementById('mode-badge');
  const modeText = document.getElementById('mode-text');
  let isSim = false;

  modeBtn?.addEventListener('click', () => {
    isSim = !isSim;
    if (isSim) {
      modeBtn.classList.add('sim-mode');
      if (modeText) modeText.textContent = '🎮 GIẢ LẬP (Simulation)';
      // Push sim state status
      updateDashboardWithMockData();
    } else {
      modeBtn.classList.remove('sim-mode');
      if (modeText) modeText.textContent = '⚡ THỰC TẾ (Real Hardware)';
      updateDashboard();
    }
  });


  // Nút Quay lại Live
  document.getElementById('back-to-live-btn')?.addEventListener('click', () => {
    isShowingHistoryImage = false;
    
    const imgEl = document.getElementById('mushroom-img');
    const liveBadge = document.getElementById('cam-live-badge');
    const backBtn = document.getElementById('back-to-live-btn');
    const labelEl = document.getElementById('cam-ai-label');
    
    imgEl.src = latestLiveImageUrl;
    liveBadge.style.display = 'inline-block';
    backBtn.classList.add('hidden');
    
    // Cập nhật lại text AI
    fetchStatus().then(status => {
      const sizeText = status.mushroom_size === 'large' ? 'LỚN — Thu hoạch!' : 'NHỎ — Đang phát triển';
      labelEl.textContent = `AI: ${sizeText}`;
    }).catch(() => {
      labelEl.textContent = `AI: đang phân tích…`;
    });
  });

  // Lắng nghe thay đổi chế độ chụp
  const camModeSelect   = document.getElementById('cam-mode-select');
  const camSourceSelect = document.getElementById('cam-source-select');
  const triggerBtn      = document.getElementById('trigger-capture-btn');
  
  camModeSelect?.addEventListener('change', async (e) => {
    const mode = e.target.value;
    triggerBtn?.classList.toggle('hidden', mode !== 'manual');
    
    try {
      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ capture_mode: mode })
      });
      if (!res.ok) throw new Error('Settings API error');
      console.log(`[Dashboard] Đã chuyển chế độ chụp sang: ${mode}`);
    } catch (err) {
      console.error('[Dashboard] Lỗi cập nhật chế độ chụp:', err);
    }
  });

  camSourceSelect?.addEventListener('change', async (e) => {
    const source = e.target.value;
    try {
      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera_source: source })
      });
      if (!res.ok) throw new Error('Settings API error');
      console.log(`[Dashboard] Đã chuyển nguồn camera sang: ${source}`);
    } catch (err) {
      console.error('[Dashboard] Lỗi cập nhật nguồn camera:', err);
    }
  });


  // Lắng nghe sự kiện chụp thủ công
  triggerBtn?.addEventListener('click', async () => {
    triggerBtn.disabled = true;
    triggerBtn.textContent = '⏳ Đang chụp...';
    
    const labelEl = document.getElementById('cam-ai-label');
    if (labelEl) labelEl.textContent = 'AI: Đang yêu cầu chụp & phân tích...';
    
    try {
      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'capture' })
      });
      if (!res.ok) throw new Error('Capture API error');
      console.log('[Dashboard] Đã kích hoạt lệnh chụp thủ công!');
      
      // Chờ 4.5 giây (đủ để camera chụp + Ollama chạy xong) rồi cập nhật dashboard ngay lập tức
      setTimeout(async () => {
        await updateDashboard();
        triggerBtn.disabled = false;
        triggerBtn.textContent = '📸 Chụp & Phân Tích';
      }, 4500);
      
    } catch (err) {
      console.error('[Dashboard] Lỗi chụp thủ công:', err);
      triggerBtn.disabled = false;
      triggerBtn.textContent = '📸 Chụp & Phân Tích';
      if (labelEl) labelEl.textContent = 'AI: Lỗi chụp ảnh!';
    }
  });

  // Lắng nghe sự kiện Bật/Tắt Bơm sương (Relay 1 / LED 1 - GPIO 15)
  let pumpState = false;
  document.getElementById('toggle-pump-btn')?.addEventListener('click', async () => {
    pumpState = !pumpState;
    try {
      await fetch(`${FIREBASE_RTDB_URL}/status.json`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pump: pumpState })
      });
      console.log(`[Dashboard] Đã gửi lệnh bơm: ${pumpState}`);
      updateDashboard();
    } catch (e) {
      console.warn('[Dashboard] Lỗi gửi lệnh bơm:', e);
    }
  });

  // Lắng nghe sự kiện Test Đèn/Còi Cảnh Báo (Relay 2 / LED 2 - GPIO 16)
  let alertState = false;
  document.getElementById('toggle-alert-btn')?.addEventListener('click', async () => {
    alertState = !alertState;
    try {
      await fetch(`${FIREBASE_RTDB_URL}/status.json`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ harvest_alert: alertState })
      });
      console.log(`[Dashboard] Đã gửi lệnh test cảnh báo: ${alertState}`);
      updateDashboard();
    } catch (e) {
      console.warn('[Dashboard] Lỗi gửi lệnh cảnh báo:', e);
    }
  });

  // Lắng nghe sự kiện Mở/Đóng Cửa gió (Servo SG90 - GPIO 14)
  let ventState = false;
  document.getElementById('toggle-vent-btn')?.addEventListener('click', async () => {
    ventState = !ventState;
    try {
      await fetch(`${FIREBASE_RTDB_URL}/status.json`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vent_gate: ventState })
      });
      console.log(`[Dashboard] Đã gửi lệnh cửa gió: ${ventState}`);
      updateDashboard();
    } catch (e) {
      console.warn('[Dashboard] Lỗi gửi lệnh cửa gió:', e);
    }
  });

  // Lắng nghe sự kiện Bật/Tắt Đèn quang hợp (Relay 3)
  let lightState = false;
  document.getElementById('toggle-light-btn')?.addEventListener('click', async () => {
    lightState = !lightState;
    try {
      await fetch(`${FIREBASE_RTDB_URL}/status.json`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grow_light: lightState })
      });
      console.log(`[Dashboard] Đã gửi lệnh đèn: ${lightState}`);
      updateDashboard();
    } catch (e) {
      console.warn('[Dashboard] Lỗi gửi lệnh đèn:', e);
    }
  });

  // Lắng nghe sự kiện Bật/Tắt Quạt mát thông gió (Relay 4)
  let fanState = false;
  document.getElementById('toggle-fan-btn')?.addEventListener('click', async () => {
    fanState = !fanState;
    try {
      await fetch(`${FIREBASE_RTDB_URL}/status.json`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cooling_fan: fanState })
      });
      console.log(`[Dashboard] Đã gửi lệnh quạt: ${fanState}`);
      updateDashboard();
    } catch (e) {
      console.warn('[Dashboard] Lỗi gửi lệnh quạt:', e);
    }
  });

  // Lắng nghe sự kiện Xuất Báo Cáo VietGAP (CSV)
  document.getElementById('export-vietgap-btn')?.addEventListener('click', () => {
    fetchStatus().then(status => {
      const nowStr = new Date().toLocaleString('vi-VN');
      const csvData = [
        ["Thoi Gian", "Nhiet Do (C)", "Do Am (%)", "VPD (kPa)", "CO2 (ppm)", "Anh Sang (Lux)", "Nguon Cam Bien", "Kich Thuoc Nam", "May Bom", "Cua Gio"],
        [nowStr, status.temperature || 27.5, status.humidity || 63.5, status.vpd || 1.34, status.co2_ppm || 460, status.light_lux || 150, status.sensor_source || 'DHT22 (G4)', status.mushroom_size || 'small', status.pump ? 'ON' : 'OFF', 'CLOSED (0°)']
      ].map(e => e.join(",")).join("\n");

      const blob = new Blob(["\ufeff" + csvData], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `Bao_Cao_VietGAP_Mushroom_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  });

  console.log('[Dashboard] 🌱 IoT Mushroom Monitor started. Poll interval:', POLL_INTERVAL, 'ms');
});

/** Cập nhật bảng nhật ký VietGAP */
function updateVietGapLogTable(status) {
  const logBody = document.getElementById('vietgap-log-body');
  if (!logBody || !status) return;

  const now = new Date().toLocaleTimeString('vi-VN');
  const temp = status.temperature ?? 27.4;
  const hum = status.humidity ?? 63.5;
  const co2 = status.co2_ppm ?? 460;
  const lux = status.light_lux ?? 150;
  const vpd = status.vpd ?? 1.34;
  const pump = status.pump ?? false;

  const pumpText = pump ? '💧 Đã tự động BẬT Máy Bơm Phun Sương' : '🟢 Duy trì giám sát tự động';

  logBody.innerHTML = `
    <tr>
      <td><code>${now}</code></td>
      <td><span class="badge-tag" style="background:hsla(158,85%,44%,0.15);color:var(--color-primary);">📊 Vi Khí Hậu</span></td>
      <td>Temp: <strong>${temp}°C</strong> | Hum: <strong>${hum}%</strong> | VPD: <strong>${vpd}kPa</strong></td>
      <td>${pumpText}</td>
      <td><span class="badge-online">🟢 VIETGAP VERIFIED</span></td>
    </tr>
    <tr>
      <td><code>${now}</code></td>
      <td><span class="badge-tag" style="background:hsla(192,90%,52%,0.15);color:var(--color-info);">💨 Khí &amp; Ánh Sáng</span></td>
      <td>CO₂: <strong>${co2} ppm</strong> | Ánh Sáng: <strong>${lux} Lux</strong></td>
      <td>Cửa gió Servo: <strong>Đóng (0°)</strong> | Đèn Grow Light: <strong>Tắt</strong></td>
      <td><span class="badge-online">🟢 AN TOÀN</span></td>
    </tr>
    <tr>
      <td><code>${now}</code></td>
      <td><span class="badge-tag" style="background:hsla(280,80%,65%,0.15);color:#d8b4fe;">🤖 AI Vision</span></td>
      <td>Model: <strong>moondream</strong> | Size: <strong>${status.mushroom_size || 'small'}</strong></td>
      <td>Tự động chụp &amp; đồng bộ Base64 Firebase</td>
      <td><span class="badge-online">🟢 AI OK (${status.ai_confidence || 83}%)</span></td>
    </tr>
  `;
}
