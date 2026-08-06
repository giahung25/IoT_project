# Design System: AgriShroom Edge — IoT & AI Control Center

## 1. Visual Theme & Atmosphere
- **Atmosphere:** Clinical, high-precision Cockpit Control Center. The visual mood combines dark obsidian glassmorphism with high-contrast tactical telemetry.
- **Density:** Cockpit Dense (8/10) — Optimized for real-time sensor streams, AI vision feeds, and actuator controls without clutter.
- **Variance:** Offset Asymmetric (6/10) — Left-heavy 65/35 Command Center layout with distinct spatial separation for camera feed vs. actuator cards.
- **Motion:** Perpetual Micro-Interactions (6/10) — Hardware-accelerated pulse indicators, smooth SVG gauge sweeps, and spring-physics button pushes (`stiffness: 100, damping: 20`).

---

## 2. Color Palette & Roles
- **Obsidian Base** (`#090D16`) — Deep primary canvas background.
- **Elevated Glass Surface** (`#131B2E`) — Translucent card containers with 1px border.
- **Crisp Text Primary** (`#F8FAFC`) — High-readability white for readouts and titles.
- **Subtle Slate Muted** (`#94A3B8`) — Secondary labels, units, and structural metadata.
- **Structural Border** (`rgba(255, 255, 255, 0.08)`) — Crisp 1px grid divider lines.
- **Bio-Emerald Accent** (`#10B981`) — Single primary accent for normal status, active pumps, and positive AI confidence (Saturation 75%).
- **Warning Amber** (`#F59E0B`) — For dry VPD warnings, high CO₂ levels (>1000 ppm), and fan actuation.
- **Alert Crimson** (`#EF4444`) — For large mushroom harvest alert, actuator errors, and high-temp thresholds.

*Banned Colors:* Pure Black (`#000000`), Neon Purple (`#A855F7`), Oversaturated Neon Gradients.

---

## 3. Typography Architecture
- **Display / Headers:** `Outfit` (Sans-Serif) — Track-tight, bold 700/800 weight, strict hierarchy.
- **Body & Controls:** `Outfit` / `Satoshi` (Sans-Serif) — Clean legibility, max 65ch line length.
- **Telemetry & Monospace:** `JetBrains Mono` — MANDATORY for all numeric readouts, sensor units (°C, %, ppm, Lux, kPa), GPIO pin numbers, and timestamp logs.
- **Banned Typography:** Generic serifs (`Times New Roman`, `Georgia`), `Inter` for main display titles.

---

## 4. Component Stylings
- **Actuator Control Buttons:** Flat glass surface with 1px border. Tactile `-1px` Y-translate on click. Active state illuminates with subtle inner emerald or amber glow.
- **Sensor Gauge Cards:** Embedded SVG arc gauges with dark backdrop track and animated gradient value strokes. Monospace numeric readout centered at gauge origin.
- **Live Vision Feed Card:** 16:9 responsive viewport with gradient overlay footer banner displaying `moondream` Vision AI model metadata and growth stage badge (`small` / `medium` / `large`).
- **GPIO Pinout Map Table:** Structural grid listing GPIO 4/6, 5, 8/9, 14, 15-18 with live status pills (`🟢 ONLINE`, `🟡 ACTUATING`, `🔴 OFF`).
- **VietGAP Log Table:** Striped high-density data rows with `.CSV` export trigger.

---

## 5. Layout Principles
- **Grid Architecture:** CSS Grid layout with max-width `1440px` centered.
- **Command Center Split:**
  - **Left Column (65%):** Live Camera Feed + AI Analysis Banner + 4-Hour Climate History Chart.
  - **Right Column (35%):** Gauges (Temp, Hum, CO₂, Light, VPD) + Interactive Actuators Grid.
- **Mobile Responsive:** Collapses to single-column stack below `768px`. Touch targets minimum `44px`.

---

## 6. Motion & Interaction
- **Perpetual Micro-Interactions:** Pulsing LED status dots (`ping 2s infinite`), live camera badge indicator (`● LIVE`).
- **Spring Transitions:** Button presses and tab switching use spring physics (`transform 0.15s ease-out`).
- **Hardware Acceleration:** All animations strictly limited to `opacity` and `transform` (`will-change: transform`).

---

## 7. Anti-Patterns (Explicit Bans)
- ❌ **NO Emojis in production UI elements** (Use SVG icons or crisp typography badges).
- ❌ **NO Pure Black (`#000000`)** — always use Charcoal Obsidian (`#090D16`).
- ❌ **NO Neon purple gradients** or glowing borders.
- ❌ **NO 3-column equal card rows** — force asymmetric split grid.
- ❌ **NO AI Copywriting Clichés** ("Next-Gen", "Seamless", "Unleash").
- ❌ **NO Broken placeholder image URLs** — use clean local fallbacks.
