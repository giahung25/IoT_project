// ============================================================
//  CHARTS.JS — Biểu đồ lịch sử nhiệt độ & độ ẩm (Chart.js)
// ============================================================

let historyChart = null;

function initHistoryChart() {
  const canvasEl = document.getElementById('history-chart');
  if (!canvasEl) return;
  const ctx = canvasEl.getContext('2d');


  // Gradient fill cho nhiệt độ
  const gradTemp = ctx.createLinearGradient(0, 0, 0, 300);
  gradTemp.addColorStop(0, 'hsla(18, 90%, 60%, 0.4)');
  gradTemp.addColorStop(1, 'hsla(18, 90%, 60%, 0.0)');

  // Gradient fill cho độ ẩm
  const gradHum = ctx.createLinearGradient(0, 0, 0, 300);
  gradHum.addColorStop(0, 'hsla(200, 80%, 60%, 0.4)');
  gradHum.addColorStop(1, 'hsla(200, 80%, 60%, 0.0)');

  historyChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Nhiệt Độ (°C)',
          data: [],
          borderColor: 'hsl(18, 90%, 60%)',
          backgroundColor: gradTemp,
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: 'hsl(18, 90%, 60%)',
          fill: true,
          tension: 0.4,
          yAxisID: 'yTemp'
        },
        {
          label: 'Độ Ẩm (%)',
          data: [],
          borderColor: 'hsl(200, 80%, 60%)',
          backgroundColor: gradHum,
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: 'hsl(200, 80%, 60%)',
          fill: true,
          tension: 0.4,
          yAxisID: 'yHum'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          labels: {
            color: 'hsl(220,10%,70%)',
            font: { family: 'Inter, Outfit, sans-serif', size: 13 },
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 20
          }
        },
        tooltip: {
          backgroundColor: 'hsla(220,20%,12%,0.95)',
          borderColor: 'hsla(0,0%,100%,0.08)',
          borderWidth: 1,
          titleColor: 'hsl(0,0%,90%)',
          bodyColor: 'hsl(220,10%,70%)',
          titleFont: { family: 'Inter, sans-serif', size: 12, weight: '600' },
          bodyFont: { family: 'Inter, sans-serif', size: 12 },
          padding: 12,
          cornerRadius: 10,
          callbacks: {
            label: ctx => {
              const unit = ctx.datasetIndex === 0 ? '°C' : '%';
              return `  ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}${unit}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'hsla(220,16%,30%,0.4)', drawBorder: false },
          ticks: {
            color: 'hsl(220,10%,55%)',
            font: { family: 'Inter, sans-serif', size: 11 },
            maxTicksLimit: 8,
            maxRotation: 0
          }
        },
        yTemp: {
          position: 'left',
          min: 15, max: 45,
          grid: { color: 'hsla(220,16%,30%,0.4)', drawBorder: false },
          ticks: {
            color: 'hsl(18,90%,60%)',
            font: { family: 'Inter, sans-serif', size: 11 },
            callback: v => `${v}°C`
          }
        },
        yHum: {
          position: 'right',
          min: 40, max: 100,
          grid: { display: false },
          ticks: {
            color: 'hsl(200,80%,60%)',
            font: { family: 'Inter, sans-serif', size: 11 },
            callback: v => `${v}%`
          }
        }
      },
      animation: {
        duration: 500,
        easing: 'easeInOutQuart'
      }
    }
  });
}

/**
 * Cập nhật biểu đồ với mảng dữ liệu mới
 * @param {Array} historyData - [{timestamp, temperature, humidity}, ...]
 */
function updateHistoryChart(historyData) {
  if (!historyChart || !Array.isArray(historyData) || historyData.length === 0) return;

  const labels = historyData.map(d => {
    const dt = new Date(d.timestamp || Date.now());
    return dt.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  });

  historyChart.data.labels = labels;
  historyChart.data.datasets[0].data = historyData.map(d => (d.temperature !== undefined ? d.temperature : (d.temp ?? 0)));
  historyChart.data.datasets[1].data = historyData.map(d => (d.humidity !== undefined ? d.humidity : (d.hum ?? 0)));
  historyChart.update();
}

