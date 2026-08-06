// ============================================================
//  GAUGES.JS — SVG Circular Gauge Component
//  Vẽ đồng hồ đo dạng vòng tròn cho nhiệt độ & độ ẩm
// ============================================================

class CircularGauge {
  /**
   * @param {string} canvasId - ID của thẻ <svg>
   * @param {object} options  - Cấu hình gauge
   */
  constructor(svgId, options = {}) {
    this.svg = document.getElementById(svgId);
    this.opts = {
      min: options.min ?? 0,
      max: options.max ?? 100,
      value: options.value ?? 0,
      unit: options.unit ?? '',
      label: options.label ?? '',
      size: options.size ?? 180,
      strokeWidth: options.strokeWidth ?? 14,
      // Ngưỡng màu [value, color]
      thresholds: options.thresholds ?? [
        [0,  '#4ade80'],  // xanh lá
        [70, '#facc15'],  // vàng
        [90, '#f87171']   // đỏ
      ],
      animate: options.animate ?? true
    };
    this._currentValue = this.opts.min;
    this._render();
  }

  _getColor(value) {
    const pct = (value - this.opts.min) / (this.opts.max - this.opts.min) * 100;
    let color = this.opts.thresholds[0][1];
    for (const [threshold, c] of this.opts.thresholds) {
      if (pct >= threshold) color = c;
    }
    return color;
  }

  _polarToCartesian(cx, cy, r, angleDeg) {
    const rad = (angleDeg - 90) * Math.PI / 180;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad)
    };
  }

  _describeArc(cx, cy, r, startAngle, endAngle) {
    const start = this._polarToCartesian(cx, cy, r, endAngle);
    const end   = this._polarToCartesian(cx, cy, r, startAngle);
    const large = endAngle - startAngle <= 180 ? '0' : '1';
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 0 ${end.x} ${end.y}`;
  }

  _render() {
    const { size, strokeWidth, min, max, unit, label } = this.opts;
    const cx = size / 2, cy = size / 2;
    const r  = (size - strokeWidth * 2) / 2 - 4;
    const startAngle = -220, endAngle = 40;  // Cung 260 độ

    this.svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
    this.svg.setAttribute('width', size);
    this.svg.setAttribute('height', size);
    this.svg.innerHTML = '';

    // --- Background track ---
    const track = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    track.setAttribute('d', this._describeArc(cx, cy, r, startAngle, endAngle));
    track.setAttribute('fill', 'none');
    track.setAttribute('stroke', 'hsla(220,16%,25%,0.8)');
    track.setAttribute('stroke-width', strokeWidth);
    track.setAttribute('stroke-linecap', 'round');
    this.svg.appendChild(track);

    // --- Value arc ---
    const arc = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    arc.setAttribute('fill', 'none');
    arc.setAttribute('stroke-width', strokeWidth);
    arc.setAttribute('stroke-linecap', 'round');
    arc.style.transition = 'stroke 0.4s ease';
    arc.id = `arc-${this.svg.id}`;
    this.svg.appendChild(arc);
    this._arc = arc;

    // --- Glow filter ---
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <filter id="glow-${this.svg.id}">
        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
        <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>`;
    this.svg.appendChild(defs);
    arc.setAttribute('filter', `url(#glow-${this.svg.id})`);

    // --- Center value text ---
    const valueText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    valueText.setAttribute('x', cx);
    valueText.setAttribute('y', cy + 8);
    valueText.setAttribute('text-anchor', 'middle');
    valueText.setAttribute('dominant-baseline', 'middle');
    valueText.setAttribute('fill', 'hsl(0,0%,95%)');
    valueText.setAttribute('font-size', size * 0.18);
    valueText.setAttribute('font-weight', '700');
    valueText.setAttribute('font-family', 'Inter, Outfit, sans-serif');
    valueText.id = `val-${this.svg.id}`;
    this.svg.appendChild(valueText);
    this._valueText = valueText;

    // --- Unit text ---
    const unitText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    unitText.setAttribute('x', cx);
    unitText.setAttribute('y', cy + size * 0.18);
    unitText.setAttribute('text-anchor', 'middle');
    unitText.setAttribute('fill', 'hsl(220,10%,65%)');
    unitText.setAttribute('font-size', size * 0.11);
    unitText.setAttribute('font-family', 'Inter, Outfit, sans-serif');
    unitText.textContent = unit;
    this.svg.appendChild(unitText);

    // --- Label text ---
    const labelText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    labelText.setAttribute('x', cx);
    labelText.setAttribute('y', cy - size * 0.28);
    labelText.setAttribute('text-anchor', 'middle');
    labelText.setAttribute('fill', 'hsl(220,10%,55%)');
    labelText.setAttribute('font-size', size * 0.085);
    labelText.setAttribute('letter-spacing', '0.05em');
    labelText.setAttribute('font-family', 'Inter, Outfit, sans-serif');
    labelText.textContent = label.toUpperCase();
    this.svg.appendChild(labelText);

    // --- Min/Max labels ---
    const minPos = this._polarToCartesian(cx, cy, r + strokeWidth + 4, startAngle);
    const maxPos = this._polarToCartesian(cx, cy, r + strokeWidth + 4, endAngle);
    [
      [minPos, min],
      [maxPos, max]
    ].forEach(([pos, val]) => {
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      t.setAttribute('x', pos.x);
      t.setAttribute('y', pos.y + 4);
      t.setAttribute('text-anchor', 'middle');
      t.setAttribute('fill', 'hsl(220,10%,45%)');
      t.setAttribute('font-size', size * 0.075);
      t.setAttribute('font-family', 'Inter, Outfit, sans-serif');
      t.textContent = val;
      this.svg.appendChild(t);
    });

    this._cx = cx; this._cy = cy; this._r = r;
    this._startAngle = startAngle; this._endAngle = endAngle;

    // Initial draw
    this._updateArc(this._currentValue, false);
  }

  _updateArc(value, animate = true) {
    const { min, max, startAngle, endAngle } = this.opts;
    const pct = Math.max(0, Math.min(1, (value - min) / (max - min)));
    const angle = startAngle + pct * (endAngle - startAngle - (startAngle < 0 ? 0 : 0));

    // Tránh arc đầy 360°
    const clampedAngle = Math.min(angle, endAngle - 0.01);
    const d = this._describeArc(this._cx, this._cy, this._r, startAngle, clampedAngle);

    if (animate) {
      this._arc.style.transition = 'stroke 0.5s ease';
    }

    this._arc.setAttribute('d', d);
    this._arc.setAttribute('stroke', this._getColor(value));
    this._valueText.textContent = value.toFixed(1);
  }

  /**
   * Cập nhật giá trị gauge với animation
   */
  update(newValue) {
    if (this.opts.animate) {
      const start = this._currentValue;
      const end   = newValue;
      const duration = 600;
      const startTime = performance.now();

      const animate = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * ease;
        this._updateArc(current);
        if (progress < 1) requestAnimationFrame(animate);
        else this._currentValue = end;
      };
      requestAnimationFrame(animate);
    } else {
      this._currentValue = newValue;
      this._updateArc(newValue, false);
    }
  }
}

// Khởi tạo hai gauges
const tempGauge = new CircularGauge('temp-svg', {
  min: 0, max: 50, unit: '°C', label: 'Nhiệt Độ', size: 200,
  thresholds: [
    [0,  '#4ade80'],
    [60, '#facc15'],
    [80, '#f87171']
  ]
});

const humGauge = new CircularGauge('hum-svg', {
  min: 0, max: 100, unit: '%', label: 'Độ Ẩm', size: 200,
  thresholds: [
    [0,  '#f87171'],
    [40, '#facc15'],
    [60, '#38bdf8'],
    [75, '#4ade80']
  ]
});
