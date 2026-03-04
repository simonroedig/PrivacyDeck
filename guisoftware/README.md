# PrivacyDeck

A physical desktop privacy control panel — hardware-level privacy controls for macOS, paired with a companion dashboard app.

---

## What is PrivacyDeck?

PrivacyDeck is a two-part system:

1. **Physical device** — a microcontroller-based controller (current prototype appears to be ESP32-class hardware) that sits on your desk with buttons mapped to privacy features
2. **Companion dashboard** — a React/Vite app running locally on your Mac, showing real-time privacy status, a configurable avatar, and controls for all features

The two communicate via:
- **Wi-Fi TCP socket (port 50555)** — the hardware controller sends button events to the Python daemon
- **WebSocket (port 50556)** — the React dashboard connects to the daemon to read state, toggle features, and receive live updates

---

## Architecture

```
React Dashboard (Vite + TypeScript, port 8080)
  |  WebSocket ws://localhost:50556
Python Daemon (daemon/main.py)
  |  TCP :50555
Hardware Controller (buttons, LEDs)
```

---

## Current Hardware Status

- ✅ Physical button hardware has replaced the simulator.
- ℹ️ Based on the current prototype board shape/module, it appears to be an **ESP32 dev board** rather than a Raspberry Pi Pico; confirm by reading the silkscreen/chip label on the PCB (e.g. `ESP32`, `WROOM`, or RP2040-related marking).
- ⚠️ Main integration blockers encountered during bring-up:
  - Campus **eduroam restrictions** prevented reliable device-to-daemon networking.
  - **Python environment setup** issues delayed daemon-side testing and validation.

---

## Privacy Features

| Feature | Type | Active = |
|---|---|---|
| Camera Control | Exposure | Camera live (risk) |
| Microphone Control | Exposure | Mic active (risk) |
| Camera Preview | Monitor | Live preview on device display |
| Audio Meter | Monitor | Real-time level metering |
| Network Isolation | Protection | Wi-Fi killed (safe) |
| Instant Disable GPS | Protection | Location services off (safe) |
| USB Safety Lock | Protection | Unauthorised USB blocked (safe) |
| Clipboard Guard | Protection | Clipboard auto-wipe on (safe) |
| Presentation Mode | Protection | Notifications hidden (safe) |
| Browser Clean | Protection | Cache & cookie clearing active (safe) |

**Privacy Score (0–100%):**
- 40 pts — exposure safety (camera + mic both off = full 40)
- 60 pts — protection coverage (all guards enabled = full 60)

**Instant Privacy** — one button blocks all sensors and enables all protections simultaneously.

---

## Requirements

### Dashboard
- Node.js >= 18 or Bun

### Daemon
- Python 3.10+
- macOS (primary; Linux/Windows partial support)

---

## Getting Started

### 1. Start the Python daemon

```bash
cd daemon
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
python main.py
```

The daemon opens a Tkinter control window and starts the WebSocket server on `ws://localhost:50556`.

### 2. Start the React dashboard

```bash
npm install        # or: bun install
npm run dev        # http://localhost:8080
```

Open http://localhost:8080. The dashboard auto-connects to the daemon. Use the **Connect Device** button in the top bar if the connection indicator is red.

### 3. Configure and flash the hardware firmware

Edit `firmware/privacydeck_esp32/privacydeck_esp32.ino` before flashing:

- Set `WIFI_SSID` and `WIFI_PASSWORD` to a Wi-Fi network that your Mac and board can both access.
- Set `SERVER_HOST` to your Mac's LAN IP address (the machine running `python main.py`).
- Keep `SERVER_PORT` as `50555` unless you also change the daemon port.

Then flash the board from Arduino IDE / PlatformIO and open Serial Monitor at `115200` baud.

### 4. Verify button presses are registered in the dashboard

When connection is healthy, you should see this flow:

1. Hardware logs handshake success (`HELLO ...` / `HELLO_ACK ...`).
2. Daemon window logs `Pico TCP: connected ...` and then receives button events.
3. On press, firmware sends `EVENT BUTTON_1..4 pressed` (or `LOCK_BUTTON`).
4. Daemon responds `OK`, toggles the mapped feature, and broadcasts a WebSocket update.
5. Dashboard cards/status update immediately via `ack` / `feature_update` messages.

If presses do not appear in UI:

- Verify Mac firewall allows inbound TCP on `50555` and WS on `50556`.
- Ensure both devices are on a network that allows client-to-client traffic (many eduroam setups block this).
- Confirm button mappings in the dashboard Configuration page match expected features.
- Recheck firmware `SERVER_HOST` IP after reconnecting to a different network.

---

## Project Structure

```
privacy-dashboard-pro-main/
  daemon/
    main.py               Entry point, Tkinter GUI, server bootstrap
    ws_server.py          Async WebSocket server
    mic_control.py        Mute/unmute microphone
    webcam.py             Camera privacy level control
    audio_meter.py        Real-time audio level metering
    airplane.py           Wi-Fi kill switch (Network Isolation)
    location.py           GPS / Location Services toggle
    usb_alert_control.py  USB device alert/block
    clipboard_control.py  Clipboard wipe
    blackout.py           Screen blackout overlay
    lock_control.py       Trigger OS lock screen
    requirements.txt
  src/
    components/
      PrivacyAvatar.tsx   Robot SVG avatar with health bar and dead-eyes at 0%
      AppSidebar.tsx      Navigation sidebar with live privacy score bar
      MacOSChrome.tsx     Title bar with connection status indicator
    context/
      PrivacyContext.tsx  Feature state, WebSocket client, optimistic updates
      AvatarContext.tsx   Avatar customisation state
    pages/
      Overview.tsx        Main dashboard (feature cards + privacy score hero)
      Configuration.tsx   Physical button mapping
      AvatarPage.tsx      Full avatar customiser
      SettingsPage.tsx    App preferences
      AboutPage.tsx       About
    hooks/
      useWebSocket.ts     Reconnecting WebSocket with exponential backoff
```

---

## Avatar Health System

The robot avatar reflects your privacy score as a live health bar:

| Score | State | Visuals |
|---|---|---|
| 70–100% | Healthy | Green bar, full opacity body |
| 30–69% | At risk | Amber bar, reduced body opacity |
| 1–29% | Critical | Red bar, pulsing LOW HP badge |
| 0% | Dead | XX eyes, flat-line mouth, dizzy swirl, faded body |

---

## WebSocket Protocol

All messages are JSON over `ws://localhost:50556`.

**Daemon → Dashboard:**

| Type | Payload | When |
|---|---|---|
| `state` | `{ features, buttonMapping }` | On connect |
| `ack` | `{ featureId, active, success }` | After toggle |
| `feature_update` | `{ featureId, active }` | Push update |
| `error` | `{ message, featureId? }` | On failure |

**Dashboard → Daemon:**

| Type | Payload | Action |
|---|---|---|
| `toggle` | `{ featureId }` | Toggle a feature |
| `get_state` | — | Request full state snapshot |
| `set_button_mapping` | `{ mapping: string[] }` | Update button assignments |

---

## Running Tests

```bash
npm test            # single run
npm run test:watch  # watch mode
```

---

## License

MIT
