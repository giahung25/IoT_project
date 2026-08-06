// ============================================================
//  FIREBASE-CONFIG.JS — Cấu hình Firebase Web Client
// ============================================================

// Điền các thông số từ Firebase Console ➔ Project Settings ➔ Web App
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  databaseURL: "https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Biến đánh dấu có kích hoạt kết nối Firebase DB trực tiếp trên Web hay không
window.ENABLE_FIREBASE_REALTIME = false;

if (window.ENABLE_FIREBASE_REALTIME && typeof firebase !== 'undefined') {
  try {
    firebase.initializeApp(firebaseConfig);
    window.firebaseDB = firebase.database();
    console.log("🔥 [Firebase] Web App đã kết nối thành công tới Firebase Realtime Database!");
  } catch (err) {
    console.warn("🔥 [Firebase] Lỗi khởi tạo Firebase Web SDK:", err);
  }
}
