// ============================================================
//  MOCK DATA — IoT Mushroom Monitor Dashboard
//  Dùng khi chưa có backend Flask (chạy frontend-only)
// ============================================================

// Trạng thái hiện tại giả lập
const MOCK_STATUS = {
  temperature: 27.5,
  humidity: 82.0,
  mushroom_size: "small",   // "small" hoặc "large"
  pump: false,
  harvest_alert: false,
  ai_confidence: 92,
  last_updated: new Date().toISOString(),
  esp32_online: true,
  camera_image: "assets/mushroom-placeholder.jpg"
};

// Tạo 48 điểm dữ liệu lịch sử (4 giờ, mỗi 5 phút 1 điểm)
function generateMockHistory() {
  const now = Date.now();
  return Array.from({ length: 48 }, (_, i) => {
    const t = 24 + Math.sin(i * 0.3) * 4 + Math.random() * 1.5;
    const h = 78 + Math.sin(i * 0.2 + 1) * 10 + Math.random() * 3;
    return {
      timestamp: new Date(now - (47 - i) * 5 * 60 * 1000).toISOString(),
      temperature: parseFloat(t.toFixed(1)),
      humidity: parseFloat(h.toFixed(1))
    };
  });
}

const MOCK_HISTORY = generateMockHistory();

// Mô phỏng giá trị thay đổi nhẹ theo thời gian (realtime feel)
function getMockStatus() {
  const drift = (Math.random() - 0.5) * 0.4;
  return {
    ...MOCK_STATUS,
    temperature: parseFloat((MOCK_STATUS.temperature + drift).toFixed(1)),
    humidity: parseFloat((MOCK_STATUS.humidity + (Math.random() - 0.5) * 0.8).toFixed(1)),
    last_updated: new Date().toISOString()
  };
}
