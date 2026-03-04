# PrivacyDeck — Technical Documentation

## Overview

PrivacyDeck is a hardware-software privacy control system. A physical ESP32 device sits on the desk with buttons mapped to privacy features. A Python daemon runs in the background executing OS-level privacy controls. A React dashboard provides real-time visual feedback and configuration.

---

## System Architecture

```
┌─────────────────────┐        TCP :50555         ┌──────────────────────┐
│  ESP32 Firmware     │ ────────────────────────▶ │  Python Daemon       │
│  (C++ / Arduino)    │   button events / ping     │  daemon/main.py      │
└─────────────────────┘                            └──────────┬───────────┘
                                                              │ WebSocket :50556
                                                              ▼
                                                   ┌──────────────────────┐
                                                   │  React Dashboard     │
                                                   │  (TypeScript / Vite) │
                                                   └──────────────────────┘
```

Three communication channels:
- **TCP (port 50555)** — Hardware → Daemon. Custom text protocol for button events and keepalive.
- **WebSocket (port 50556)** — Daemon ↔ Dashboard. JSON messages for state sync, toggles, and acks.
- **HTTPS / OAuth2** — Dashboard + Daemon → Google Calendar API. Token exchange handled by daemon.

---

## Languages and Stack

### Hardware Layer — `firmware/`
| | |
|---|---|
| Language | C++ (Arduino framework) |
| Platform | ESP32 (Espressif) |
| IDE | Arduino IDE / PlatformIO |
| Protocol | Custom TCP text protocol over Wi-Fi |

### Daemon Layer — `daemon/`
| | |
|---|---|
| Language | Python 3.10+ |
| Key libraries | `websockets` (async WS server), `tkinter` (GUI control window), `python-dotenv` (env vars), `subprocess` (OS commands) |
| Primary OS | macOS (partial Linux/Windows support) |
| Entry point | `daemon/main.py` (1672 lines) |

### Dashboard Layer — `src/`
| | |
|---|---|
| Language | TypeScript 5.8 |
| Framework | React 18.3 |
| Build tool | Vite 5.4 (dev server on port 8080) |
| Styling | Tailwind CSS 3.4 |
| Component library | Radix UI + shadcn/ui patterns |
| Animations | Framer Motion |
| Icons | Lucide React |
| State | React Context API |
| Forms | React Hook Form + Zod |
| Routing | React Router v6 |
| Testing | Vitest + Testing Library |
| Package manager | npm or Bun |

---

## How It Works

### 1. Startup sequence
1. Run `python daemon/main.py` — opens Tkinter control window, starts TCP server on `:50555`, starts WebSocket server on `:50556`.
2. Run `npm run dev` — dashboard serves on `http://localhost:8080`, auto-connects to `ws://localhost:50556`.
3. Power the ESP32 — it connects to Wi-Fi, opens a TCP connection to the daemon, and sends a handshake: `HELLO PRIVACYDECK_PICO 1`.

### 2. Button press flow
```
User presses physical button
  → ESP32 sends: EVENT BUTTON_1 pressed
  → Daemon receives, maps button to feature (e.g. mic-control)
  → Daemon executes OS control (e.g. mic_control.py mutes mic)
  → Daemon broadcasts: { type: "feature_update", featureId: "mic-control", active: true }
  → Dashboard receives update, re-renders feature card and avatar
```

### 3. Dashboard toggle flow
```
User clicks toggle in dashboard
  → Optimistic UI update (instant, no wait)
  → Sends: { type: "toggle", featureId: "network" } over WebSocket
  → Daemon executes OS control (e.g. airplane.py kills Wi-Fi)
  → Daemon sends: { type: "ack", featureId: "network", active: true, success: true }
  → Dashboard confirms state, clears pending lock (2-second race-condition window)
```

### 4. Privacy score
Computed in `PrivacyContext.tsx` on every state change:

```
score = exposureScore + protectionScore

exposureScore  = ((2 - exposuresActive) / 2) × 40    // camera, mic
protectionScore = (protectionsActive / 6) × 60         // network, gps, usb, clipboard, presentation, browser-clean
```

Range: 0–100. Drives avatar health state and sidebar bar colour.

---

## Privacy Features (10 total)

| ID | Name | Type | OS action |
|---|---|---|---|
| `camera-control` | Camera Control | Exposure | Blocks camera hardware access |
| `mic-control` | Microphone Control | Exposure | Mutes system microphone |
| `camera-preview` | Camera Preview | Monitor | Live camera feed on device display |
| `audio-meter` | Audio Meter | Monitor | Real-time audio level widget |
| `network` | Network Isolation | Protection | Wi-Fi kill switch (airplane mode) |
| `gps` | Instant Disable GPS | Protection | Disables location services |
| `usb-lock` | USB Safety Lock | Protection | Blocks unauthorised USB connections |
| `clipboard` | Clipboard Guard | Protection | Auto-wipes clipboard |
| `presentation` | Presentation Mode | Protection | Hides notifications |
| `browser-clean` | Browser Clean | Protection | Clears cookies, cache, history |

**Instant Privacy**: one action toggles all 10 features to maximum privacy.

---

## Daemon Modules

| File | Responsibility |
|---|---|
| `main.py` | Core server, Tkinter GUI, feature state, button mapping, calendar recommendations |
| `ws_server.py` | Async WebSocket server (bridges dashboard ↔ daemon) |
| `mic_control.py` | Cross-platform microphone mute/unmute |
| `webcam.py` | Camera access control |
| `audio_meter.py` | Real-time audio metering widget |
| `airplane.py` | Wi-Fi kill switch |
| `location.py` | GPS / location services toggle |
| `usb_alert_control.py` | USB device alert and block |
| `clipboard_control.py` | Cross-platform clipboard wipe |
| `blackout.py` | Screen blackout overlay |
| `lock_control.py` | Triggers OS lock screen |

---

## Dashboard Components

| File | Responsibility |
|---|---|
| `context/PrivacyContext.tsx` | Feature state, WebSocket client, optimistic updates, study logging, calendar state |
| `context/AvatarContext.tsx` | Avatar customisation state (persisted to localStorage) |
| `components/PrivacyAvatar.tsx` | SVG robot avatar; body parts mapped to features with glow indicators |
| `components/AppSidebar.tsx` | Navigation with live privacy score bar |
| `components/MacOSChrome.tsx` | Title bar with connection status |
| `pages/Overview.tsx` | Main dashboard — feature cards, score hero, avatar |
| `pages/Configuration.tsx` | Physical button mapping UI |
| `pages/AvatarPage.tsx` | Avatar appearance customiser |
| `pages/SettingsPage.tsx` | App preferences, study mode, calendar settings |
| `hooks/useWebSocket.ts` | Reconnecting WebSocket with exponential backoff |

---

## Avatar Health System

The robot avatar (`PrivacyAvatar.tsx`) maps each feature to a body part:

| Body part | Feature |
|---|---|
| Eyes | Camera control / Camera preview |
| Mouth | Microphone control |
| Ears | Audio meter |
| Head | Presentation mode |
| Torso | Network isolation |
| Arms | USB safety lock |
| Hands | Clipboard guard |
| Feet | GPS |
| Antenna | Browser clean |

Health states driven by privacy score:

| Score | State | Visual |
|---|---|---|
| 70–100 | Healthy | Green bar, full opacity |
| 30–69 | At risk | Amber bar, reduced opacity |
| 1–29 | Critical | Red bar, pulsing LOW HP badge |
| 0 | Dead | XX eyes, flat-line mouth, dizzy swirl |

Active exposure features glow **red**; active protection features glow **green**.

---

## WebSocket Protocol

All messages are JSON over `ws://localhost:50556`.

**Daemon → Dashboard**

| `type` | Key fields | Sent when |
|---|---|---|
| `state` | `features`, `buttonMapping` | On dashboard connect |
| `ack` | `featureId`, `active`, `success` | After toggle executed |
| `feature_update` | `featureId`, `active` | External state change (hardware button) |
| `error` | `message`, `featureId?` | Execution failure |
| `google_token` | `accessToken`, `expiresAt` | OAuth2 code exchange complete |

**Dashboard → Daemon**

| `type` | Key fields | Action |
|---|---|---|
| `toggle` | `featureId` | Execute feature toggle |
| `get_state` | — | Request full state snapshot |
| `set_button_mapping` | `mapping: string[]` | Update button assignments |
| `google_oauth_exchange_code` | `code`, `state` | Exchange OAuth2 authorization code |

---

## Hardware Protocol (TCP)

Custom text-based protocol on port 50555.

```
ESP32  →  Daemon:   HELLO PRIVACYDECK_PICO 1
Daemon →  ESP32:    HELLO_ACK 1

ESP32  →  Daemon:   EVENT BUTTON_1 pressed
Daemon →  ESP32:    OK

ESP32  →  Daemon:   PING
Daemon →  ESP32:    PONG
```

Button pin mapping (default firmware):

| GPIO | Button | Default feature |
|---|---|---|
| 12 | Button 1 | camera-control |
| 13 | Button 2 | mic-control |
| 14 | Button 3 | network |
| 15 | Button 4 | gps |
| 16 | Lock button | OS lock screen |
| 2 | — | Status LED |

Debounce: 50 ms. Reconnection: exponential backoff (2 s → 30 s max).

---

## Google Calendar Integration

The daemon acts as a secure proxy for OAuth2 token exchange:

1. Dashboard constructs Google OAuth2 authorization URL and redirects user.
2. After consent, Google redirects back with an authorization code.
3. Dashboard sends `google_oauth_exchange_code` over WebSocket to daemon.
4. Daemon POSTs to `https://oauth2.googleapis.com/token` using credentials from `.env`.
5. Daemon returns `accessToken` and `expiresAt` to dashboard.
6. Dashboard calls Google Calendar API directly using the token.

The daemon also generates calendar-aware privacy recommendations by combining:
- Meeting timing and density (meetings within 20 min or 3+ meetings today)
- Network trust heuristic (derived from network isolation toggle state)
- Current protection feature states

---

## Study Data Logging

When enabled in settings, `PrivacyContext.tsx` logs every feature transition to `localStorage`:

```typescript
{
  timestamp: string,       // ISO 8601
  featureId: string,
  featureName: string,
  before: boolean,
  after: boolean,
  source: "dashboard" | "daemon",
  scoreBefore: number,
  scoreAfter: number
}
```

Max 2000 entries retained. Exportable as JSON from Settings. Never transmitted — local only.

---

## Running the Project

```bash
# Daemon
cd daemon
python3 -m venv ../.venv && source ../.venv/bin/activate
pip install -r requirements.txt
python main.py

# Dashboard
npm install
npm run dev        # http://localhost:8080

# Tests
npm test
```

---

## License

MIT
