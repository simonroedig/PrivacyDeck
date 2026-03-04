import tkinter as tk
import tkinter.ttk as ttk
import socket
import threading
import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from mic_control import set_mic_mute
from lock_control import lock_os
from clipboard_control import wipe_clipboard_history
from usb_alert_control import toggle_usb_alert
from airplane import gui_toggle_airplane_mode
from location import gui_toggle_location
from blackout import show_blackout_image
from webcam import WebcamController
from audio_meter import AudioMeterWidget
from ws_server import DashboardWebSocketServer

# Load environment variables (Google OAuth credentials)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ===== STATE =====
daemon_state = {
    "mic-control":    {"active": True},
    "camera-control": {"active": True, "value": 0},
    "usb-lock":       {"active": True},
    "gps":            {"active": False},
    "network":        {"active": False},
    "clipboard":      {"active": False},
    "presentation":   {"active": True},
    "camera-preview": {"active": True},
    "audio-meter":    {"active": True},
    "browser-clean":  {"active": True},
}

button_mapping = ["camera-control", "mic-control", "network", "gps"]

# ===== DEMO MODE =====
demo_mode = False

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 50555
WS_PORT = 50556

# Demo sequence: expose all risks first, then lock everything down
_DEMO_SEQUENCE = [
    # (feature_id, active_value, delay_ms_before_next)
    ("network",       False, 600),
    ("gps",           False, 600),
    ("usb-lock",      False, 600),
    ("clipboard",     False, 600),
    ("presentation",  False, 600),
    ("browser-clean", False, 600),
    ("mic-control",   True,  800),
    ("camera-control",True,  800),
    # gradually secure everything
    ("mic-control",   False, 1200),
    ("camera-control",False, 1000),
    ("network",       True,  900),
    ("gps",           True,  900),
    ("usb-lock",      True,  700),
    ("clipboard",     True,  700),
    ("presentation",  True,  700),
    ("browser-clean", True,  700),
]

# ===== AVATAR CONFIG =====
AVATAR_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "avatar_config.json")

DEFAULT_AVATAR_CONFIG = {
    "name": "JamesBot",
    "colorScheme": "shieldBlue",
    "primaryColor": "#2563EB",
    "accentColor": "#1E3A5F",
    "bodyShape": "compact",
    "faceStyle": "friendly",
    "accessories": [],
    "animationStyle": "reactive",
}

avatar_config = {}

calendar_state = {
    "provider": "google",
    "connected": False,
    "lastSync": None,
    "error": None,
}

calendar_events = []

calendar_recommendation = None


def _start_of_week_utc(now):
    return datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())


def _build_weekly_calendar_events(now=None):
    now = now or datetime.utcnow()
    start_week = _start_of_week_utc(now)
    templates = [
        (0, 9, 0, 45, "Weekly Security Standup", False),
        (1, 13, 0, 30, "Vendor Risk Review", False),
        (2, 15, 30, 30, "1:1 (Private)", True),
        (3, 11, 0, 60, "Customer Incident Triage", False),
        (4, 16, 0, 45, "Roadmap + Privacy Deck Demo", False),
    ]
    events = []
    for idx, (day_offset, hour, minute, duration_min, title, is_private) in enumerate(templates, start=1):
        start = start_week + timedelta(days=day_offset, hours=hour, minutes=minute)
        end = start + timedelta(minutes=duration_min)
        events.append(
            {
                "id": f"evt-week-{idx}",
                "title": title,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "isPrivate": is_private,
            }
        )

    if events and datetime.fromisoformat(events[-1]["end"]) < now:
        shifted = []
        for event in events:
            shifted_start = datetime.fromisoformat(event["start"]) + timedelta(days=7)
            shifted_end = datetime.fromisoformat(event["end"]) + timedelta(days=7)
            shifted.append({**event, "start": shifted_start.isoformat(), "end": shifted_end.isoformat()})
        return shifted
    return events


network_trust = {
    "currentNetwork": "Unknown",
    "trustStatus": "caution",
    "trustScore": 50,
    "reasons": ["No active network details yet."],
}


def _load_avatar_config():
    global avatar_config
    try:
        if os.path.exists(AVATAR_CONFIG_FILE):
            with open(AVATAR_CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                avatar_config = {**DEFAULT_AVATAR_CONFIG, **loaded}
        else:
            avatar_config = DEFAULT_AVATAR_CONFIG.copy()
    except Exception:
        avatar_config = DEFAULT_AVATAR_CONFIG.copy()


def _save_avatar_config():
    try:
        with open(AVATAR_CONFIG_FILE, "w") as f:
            json.dump(avatar_config, f, indent=2)
    except Exception:
        pass


_load_avatar_config()

# ===== FEATURE METADATA =====
FEATURE_NAMES = {
    "camera-control": "Camera",
    "mic-control":    "Mic",
    "network":        "Network",
    "gps":            "GPS",
    "usb-lock":       "USB Lock",
    "clipboard":      "Clipboard",
    "presentation":   "Present.",
    "browser-clean":  "Browser",
    "camera-preview": "Cam View",
    "audio-meter":    "Audio",
}

FEATURE_ACTIVE_IS_RISK = {
    "camera-control": True,
    "mic-control":    True,
}

COLOR_PRESETS = {
    "shieldBlue":   {"primary": "#2563EB", "accent": "#1E3A5F", "label": "Shield Blue"},
    "stealthBlack": {"primary": "#374151", "accent": "#9CA3AF", "label": "Stealth Black"},
    "hackerGreen":  {"primary": "#065F46", "accent": "#34D399", "label": "Hacker Green"},
    "sunsetRed":    {"primary": "#991B1B", "accent": "#FCA5A5", "label": "Sunset Red"},
    "lavender":     {"primary": "#6D28D9", "accent": "#C4B5FD", "label": "Lavender"},
    "sand":         {"primary": "#92400E", "accent": "#FDE68A", "label": "Sand"},
}

# ===== GUI CALLBACKS REGISTRY =====
_gui_callbacks = {}


def _request_gui_update():
    """Thread-safe request to refresh all GUI elements after state changes."""
    for key, fn in list(_gui_callbacks.items()):
        try:
            root.after(0, fn)
        except Exception:
            pass


# ===== HELPER FUNCTIONS =====

def _get_feature_color(feature_id):
    """Return (bg_color, fg_color) for a feature button based on state."""
    is_active = daemon_state.get(feature_id, {}).get("active", False)
    is_risk_when_active = FEATURE_ACTIVE_IS_RISK.get(feature_id, False)
    if is_risk_when_active:
        return ("#ef4444", "#ffffff") if is_active else ("#22c55e", "#ffffff")
    else:
        return ("#22c55e", "#ffffff") if is_active else ("#374151", "#9ca3af")


def _calculate_privacy_score():
    """Calculate privacy score 0–100."""
    cam_safe = not daemon_state.get("camera-control", {}).get("active", True)
    mic_safe = not daemon_state.get("mic-control",    {}).get("active", True)
    exposure_pts = (20 if cam_safe else 0) + (20 if mic_safe else 0)
    protection_ids = ["network", "gps", "usb-lock", "clipboard", "presentation", "browser-clean"]
    protection_pts = sum(
        10 if daemon_state.get(pid, {}).get("active", False) else 0
        for pid in protection_ids
    )
    return exposure_pts + protection_pts


# ===== TCP SERVER =====
class PicoNetworkServer:
    def __init__(self, host, port, event_callback, status_callback):
        self.host = host
        self.port = port
        self.event_callback = event_callback
        self.status_callback = status_callback
        self._stop_event = threading.Event()
        self._server_socket = None
        self._accept_thread = None

    def start(self):
        if self._accept_thread is not None:
            return
        self._accept_thread = threading.Thread(target=self._run_server, daemon=True)
        self._accept_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass

    def _run_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket = server_socket
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(2)
        server_socket.settimeout(1.0)
        self.status_callback(f"Pico TCP: listening on {self.host}:{self.port}")
        while not self._stop_event.is_set():
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            client_thread = threading.Thread(
                target=self._handle_client,
                args=(conn, addr),
                daemon=True,
            )
            client_thread.start()
        self.status_callback("Pico TCP: stopped")

    def _send_line(self, conn, message):
        conn.sendall((message + "\n").encode("utf-8"))

    def _read_line(self, conn):
        data = bytearray()
        while True:
            chunk = conn.recv(1)
            if not chunk:
                return None
            if chunk == b"\n":
                break
            data.extend(chunk)
        return data.decode("utf-8", errors="replace").strip()

    def _handle_client(self, conn, addr):
        conn.settimeout(30.0)
        self.status_callback(f"Pico TCP: connection from {addr[0]}:{addr[1]}")
        try:
            hello = self._read_line(conn)
            if hello != "HELLO PRIVACYDECK_PICO 1":
                self._send_line(conn, "ERR handshake")
                return
            self._send_line(conn, "HELLO_ACK PRIVACYDECK_DAEMON 1")
            self.status_callback(f"Pico TCP: connected to {addr[0]}:{addr[1]}")
            while not self._stop_event.is_set():
                line = self._read_line(conn)
                if line is None:
                    break
                if line == "PING":
                    self._send_line(conn, "PONG")
                    continue
                if line == "EVENT LOCK_BUTTON pressed":
                    self.event_callback("lock_system")
                    self._send_line(conn, "OK")
                    continue
                if line.startswith("EVENT BUTTON_") and line.endswith(" pressed"):
                    try:
                        btn_num = int(line.split("_")[1].split(" ")[0]) - 1
                        self.event_callback(f"button_{btn_num}")
                        self._send_line(conn, "OK")
                    except (ValueError, IndexError):
                        self._send_line(conn, "ERR bad_button")
                    continue
                self._send_line(conn, "ERR unknown_event")
        except (ConnectionError, OSError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass
            self.status_callback("Pico TCP: waiting for device")


# ===== WEBSOCKET COMMAND HANDLERS =====
def get_state():
    return {
        "features":     {k: dict(v) for k, v in daemon_state.items()},
        "buttonMapping": list(button_mapping),
        "demoMode":     demo_mode,
        "avatarConfig": dict(avatar_config),
        "calendarStatus": dict(calendar_state),
        "calendarEvents": list(calendar_events),
        "calendarRecommendation": dict(calendar_recommendation) if calendar_recommendation else None,
        "networkTrust": dict(network_trust),
    }


def _build_calendar_recommendation():
    global calendar_recommendation
    if not calendar_events:
        calendar_recommendation = None
        return

    now = datetime.utcnow()
    parsed_events = []
    for event in calendar_events:
        try:
            start = datetime.fromisoformat(event["start"])
            end = datetime.fromisoformat(event["end"])
        except Exception:
            continue
        parsed_events.append((start, end, event))

    if not parsed_events:
        calendar_recommendation = None
        return

    upcoming = [item for item in parsed_events if item[1] >= now]
    if not upcoming:
        calendar_recommendation = None
        return

    next_start, _next_end, next_event = min(upcoming, key=lambda item: item[0])
    mins = max(0, int((next_start - now).total_seconds() // 60))
    weekly_total = len(parsed_events)
    today_count = sum(1 for start, _, _ in parsed_events if start.date() == now.date())
    high_focus_window = mins <= 20 or today_count >= 3

    deck_actions = []
    if daemon_state.get("mic-control", {}).get("active", True):
        deck_actions.append("mute mic")
    if daemon_state.get("camera-control", {}).get("active", True):
        deck_actions.append("block camera")
    if not daemon_state.get("presentation", {}).get("active", False):
        deck_actions.append("enable presentation mode")

    trust_state = network_trust.get("trustStatus", "caution")
    if trust_state != "trusted" and not daemon_state.get("network", {}).get("active", False):
        deck_actions.append("turn on network isolation")

    impact = 10 + (4 if high_focus_window else 0) + (6 if trust_state != "trusted" else 0)
    reason_bits = [
        f"{weekly_total} meetings this week",
        f"next meeting in {mins}m",
        f"network trust is {trust_state}",
    ]
    if next_event.get("isPrivate"):
        reason_bits.append("next event marked private")

    action_text = ", ".join(deck_actions[:3]) if deck_actions else "keep current deck state"
    calendar_recommendation = {
        "profile": "Focus Meeting Shield" if high_focus_window else "Weekly Privacy Balance",
        "reason": f"{'; '.join(reason_bits)}. Suggested PrivacyDeck actions: {action_text}.",
        "impact": impact,
    }


def _set_network_trust_from_network_feature(active):
    if active:
        network_trust.update(
            {
                "currentNetwork": "Isolated",
                "trustStatus": "trusted",
                "trustScore": 95,
                "reasons": [
                    "Network isolation is enabled.",
                    "Outbound connectivity reduced.",
                ],
            }
        )
    else:
        network_trust.update(
            {
                "currentNetwork": "Unknown Network",
                "trustStatus": "caution",
                "trustScore": 55,
                "reasons": [
                    "Network isolation is disabled.",
                    "Verify SSID security and VPN.",
                ],
            }
        )
    _build_calendar_recommendation()


def _broadcast_payload(payload):
    import asyncio as _aio

    if ws_server._loop is not None:
        _aio.run_coroutine_threadsafe(ws_server._broadcast(json.dumps(payload)), ws_server._loop)


def _exchange_google_auth_code(code: str, redirect_uri: str) -> dict:
    """Exchange Google authorization code for access token."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in daemon/.env")
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise Exception(f"Google token exchange failed ({response.status_code}): {response.text}")
    
    payload = response.json()
    if "access_token" not in payload:
        raise Exception(f"No access_token in Google response: {payload}")
    
    return {
        "accessToken": payload["access_token"],
        "expiresAt": int(datetime.utcnow().timestamp() * 1000) + (payload.get("expires_in", 3600) * 1000),
    }


def handle_command(msg):
    msg_type   = msg.get("type")
    feature_id = msg.get("featureId")

    if msg_type == "get_state":
        return {"type": "state", **get_state()}

    if msg_type == "set_button_mapping":
        global button_mapping
        button_mapping = msg.get("mapping", button_mapping)
        _request_gui_update()
        return {"type": "ack", "success": True}

    if msg_type == "set_avatar_config":
        global avatar_config
        incoming = msg.get("config", {})
        avatar_config.update(incoming)
        _save_avatar_config()
        _request_gui_update()
        # Broadcast updated state to all connected clients
        _broadcast_payload({"type": "state", **get_state()})
        return {"type": "ack", "success": True}

    if msg_type == "connect_calendar":
        provider = msg.get("provider", "google")
        calendar_state.update(
            {
                "provider": provider,
                "connected": True,
                "lastSync": datetime.utcnow().isoformat(),
                "error": None,
            }
        )
        calendar_events.clear()
        calendar_events.extend(_build_weekly_calendar_events())
        _build_calendar_recommendation()
        _broadcast_payload({"type": "calendar_status", "status": calendar_state})
        _broadcast_payload({"type": "calendar_events", "events": calendar_events})
        if calendar_recommendation:
            _broadcast_payload({"type": "calendar_recommendation", "recommendation": calendar_recommendation})
        return {"type": "ack", "success": True}

    if msg_type == "disconnect_calendar":
        calendar_state.update(
            {
                "connected": False,
                "lastSync": datetime.utcnow().isoformat(),
                "error": None,
            }
        )
        calendar_events.clear()
        _build_calendar_recommendation()
        _broadcast_payload({"type": "calendar_status", "status": calendar_state})
        _broadcast_payload({"type": "calendar_events", "events": calendar_events})
        _broadcast_payload({"type": "calendar_recommendation", "recommendation": None})
        return {"type": "ack", "success": True}

    if msg_type == "refresh_calendar":
        calendar_state["lastSync"] = datetime.utcnow().isoformat()
        if calendar_state.get("connected"):
            calendar_events.clear()
            calendar_events.extend(_build_weekly_calendar_events())
        _build_calendar_recommendation()
        _broadcast_payload({"type": "calendar_status", "status": calendar_state})
        _broadcast_payload({"type": "calendar_events", "events": calendar_events})
        _broadcast_payload({"type": "calendar_recommendation", "recommendation": calendar_recommendation})
        return {"type": "ack", "success": True}

    if msg_type == "google_oauth_exchange_code":
        code = msg.get("code")
        redirect_uri = msg.get("redirect_uri")
        if not code or not redirect_uri:
            return {"type": "error", "message": "Missing code or redirect_uri"}
        try:
            token = _exchange_google_auth_code(code, redirect_uri)
            return {"type": "google_token", "accessToken": token["accessToken"], "expiresAt": token["expiresAt"]}
        except Exception as e:
            return {"type": "error", "message": str(e)}

    if msg_type == "toggle":
        return _handle_toggle(feature_id)

    if msg_type == "action":
        return _handle_action(feature_id)

    if msg_type == "set_value":
        return _handle_set_value(feature_id, msg.get("value", 0))

    return {"type": "error", "message": f"Unknown message type: {msg_type}"}


def _handle_toggle(feature_id):
    if feature_id not in daemon_state:
        return {"type": "error", "featureId": feature_id, "message": "Unknown feature"}

    try:
        new_state = not daemon_state[feature_id]["active"]

        if feature_id == "mic-control":
            if not demo_mode:
                try:
                    set_mic_mute(new_state)
                except NotImplementedError:
                    pass
            daemon_state[feature_id]["active"] = new_state
            root.after(0, lambda: btn_toggle_mic.config(
                text=f"Mic: {'Muted' if new_state else 'Active'}"
            ))

        elif feature_id == "usb-lock":
            if not demo_mode:
                try:
                    toggle_usb_alert(new_state)
                except NotImplementedError:
                    pass
            daemon_state[feature_id]["active"] = new_state
            root.after(0, lambda: btn_toggle_usb.config(
                text=f"USB Lock: {'ON' if new_state else 'OFF'}"
            ))

        elif feature_id == "network":
            if demo_mode:
                daemon_state[feature_id]["active"] = new_state
            else:
                try:
                    success = gui_toggle_airplane_mode()
                except NotImplementedError:
                    success = False
                if success:
                    daemon_state[feature_id]["active"] = new_state
            root.after(0, lambda: btn_toggle_network.config(
                text=f"Network Isolation: {'ON' if daemon_state['network']['active'] else 'OFF'}"
            ))
            _set_network_trust_from_network_feature(daemon_state[feature_id]["active"])
            _broadcast_payload({"type": "network_trust", "payload": network_trust})

        elif feature_id == "gps":
            if demo_mode:
                daemon_state[feature_id]["active"] = new_state
            else:
                try:
                    success = gui_toggle_location()
                except NotImplementedError:
                    success = False
                if success:
                    daemon_state[feature_id]["active"] = new_state
            root.after(0, lambda: btn_toggle_gps.config(
                text=f"GPS: {'DISABLED' if daemon_state['gps']['active'] else 'TRACKING'}"
            ))

        elif feature_id == "camera-control":
            daemon_state[feature_id]["active"] = new_state

        elif feature_id == "clipboard":
            daemon_state[feature_id]["active"] = new_state
            if new_state and not demo_mode:
                try:
                    wipe_clipboard_history()
                except NotImplementedError:
                    pass

        elif feature_id == "presentation":
            daemon_state[feature_id]["active"] = new_state
            if new_state and not demo_mode:
                try:
                    show_blackout_image()
                except NotImplementedError:
                    pass

        elif feature_id == "browser-clean":
            daemon_state[feature_id]["active"] = new_state

        else:
            daemon_state[feature_id]["active"] = new_state

        ws_server.broadcast_update(feature_id, daemon_state[feature_id]["active"])
        _request_gui_update()

        return {
            "type":      "ack",
            "featureId": feature_id,
            "active":    daemon_state[feature_id]["active"],
            "success":   True,
        }

    except Exception as e:
        return {"type": "error", "featureId": feature_id, "message": str(e)}


def _handle_action(feature_id):
    try:
        if feature_id == "clipboard":
            if not demo_mode:
                wipe_clipboard_history()
        elif feature_id == "presentation":
            if not demo_mode:
                show_blackout_image()
        elif feature_id == "browser-clean":
            pass
        else:
            return {"type": "error", "featureId": feature_id, "message": "Not an action feature"}

        return {"type": "ack", "featureId": feature_id, "success": True}

    except NotImplementedError as e:
        return {"type": "error", "featureId": feature_id, "message": str(e)}
    except Exception as e:
        return {"type": "error", "featureId": feature_id, "message": str(e)}


def _handle_set_value(feature_id, value):
    try:
        if feature_id == "camera-control":
            if not demo_mode:
                webcam_controller.set_privacy_level(value)
            daemon_state[feature_id]["value"] = value
            root.after(0, lambda: slider_webcam.set(value))
            return {"type": "ack", "featureId": feature_id, "value": value, "success": True}

        return {"type": "error", "featureId": feature_id, "message": "Not a value feature"}

    except NotImplementedError as e:
        return {"type": "error", "featureId": feature_id, "message": str(e)}
    except Exception as e:
        return {"type": "error", "featureId": feature_id, "message": str(e)}


# ===== TKINTER CALLBACKS =====
def toggle_mic():
    new_state = not daemon_state["mic-control"]["active"]
    if not demo_mode:
        try:
            set_mic_mute(new_state)
        except NotImplementedError:
            pass
    daemon_state["mic-control"]["active"] = new_state
    btn_toggle_mic.config(text=f"Mic: {'Muted' if new_state else 'Active'}")
    ws_server.broadcast_update("mic-control", new_state)
    _request_gui_update()


def lock_system():
    if not demo_mode:
        try:
            lock_os()
        except NotImplementedError:
            pass


def wipe_clipboard():
    if not demo_mode:
        try:
            wipe_clipboard_history()
        except NotImplementedError:
            pass


def show_blackout():
    if not demo_mode:
        try:
            show_blackout_image()
        except NotImplementedError:
            pass


def toggle_usb():
    new_state = not daemon_state["usb-lock"]["active"]
    if not demo_mode:
        try:
            toggle_usb_alert(new_state)
        except NotImplementedError:
            pass
    daemon_state["usb-lock"]["active"] = new_state
    btn_toggle_usb.config(text=f"USB Lock: {'ON' if new_state else 'OFF'}")
    ws_server.broadcast_update("usb-lock", new_state)
    _request_gui_update()


def toggle_airplane_mode():
    if demo_mode:
        new_state = not daemon_state["network"]["active"]
        daemon_state["network"]["active"] = new_state
    else:
        try:
            success = gui_toggle_airplane_mode()
        except NotImplementedError:
            success = False
        if success:
            new_state = not daemon_state["network"]["active"]
            daemon_state["network"]["active"] = new_state
    btn_toggle_network.config(
        text=f"Network Isolation: {'ON' if daemon_state['network']['active'] else 'OFF'}"
    )
    ws_server.broadcast_update("network", daemon_state["network"]["active"])
    _request_gui_update()


def toggle_location():
    if demo_mode:
        new_state = not daemon_state["gps"]["active"]
        daemon_state["gps"]["active"] = new_state
    else:
        try:
            success = gui_toggle_location()
        except NotImplementedError:
            success = False
        if success:
            new_state = not daemon_state["gps"]["active"]
            daemon_state["gps"]["active"] = new_state
    btn_toggle_gps.config(
        text=f"GPS: {'DISABLED' if daemon_state['gps']['active'] else 'TRACKING'}"
    )
    ws_server.broadcast_update("gps", daemon_state["gps"]["active"])
    _request_gui_update()


def set_webcam_privacy(value):
    if not demo_mode:
        try:
            webcam_controller.set_privacy_level(value)
        except NotImplementedError:
            pass
    daemon_state["camera-control"]["value"] = int(value)


def update_network_status(text):
    root.after(0, lambda: network_status_label.config(text=text))


def handle_network_event(event_name):
    if event_name == "lock_system":
        root.after(0, lock_system)
    elif event_name.startswith("button_"):
        try:
            idx = int(event_name.split("_")[1])
            if 0 <= idx < len(button_mapping):
                feature_id = button_mapping[idx]
                result = _handle_toggle(feature_id)
                if result.get("success"):
                    ws_server.broadcast_update(feature_id, daemon_state[feature_id]["active"])
        except (ValueError, IndexError):
            pass


# ===== DEMO MODE CONTROLS =====
def toggle_demo_mode():
    global demo_mode
    demo_mode = not demo_mode
    if demo_mode:
        btn_demo.config(text="Demo Mode: ON", bg="#22c55e", fg="white", relief="sunken")
        demo_status_label.config(text="DEMO ACTIVE — OS calls bypassed", fg="#16a34a")
        btn_run_demo.config(state="normal")
    else:
        btn_demo.config(text="Demo Mode: OFF", bg="SystemButtonFace", fg="black", relief="raised")
        demo_status_label.config(text="", fg="gray")
        btn_run_demo.config(state="disabled")
    import asyncio
    state_msg = json.dumps({"type": "state", **get_state()})
    if ws_server._loop is not None:
        asyncio.run_coroutine_threadsafe(ws_server._broadcast(state_msg), ws_server._loop)


def run_demo_sequence():
    if not demo_mode:
        return
    btn_run_demo.config(state="disabled", text="Running...")

    def _step(idx):
        if idx >= len(_DEMO_SEQUENCE):
            root.after(0, lambda: btn_run_demo.config(state="normal", text="Run Demo Sequence"))
            return
        feature_id, new_active, delay_ms = _DEMO_SEQUENCE[idx]
        daemon_state[feature_id]["active"] = new_active
        ws_server.broadcast_update(feature_id, new_active)
        root.after(0, _refresh_button_labels)
        _request_gui_update()
        root.after(delay_ms, lambda: _step(idx + 1))

    root.after(200, lambda: _step(0))


def _refresh_button_labels():
    btn_toggle_mic.config(
        text=f"Mic: {'Muted' if not daemon_state['mic-control']['active'] else 'Active'}"
    )
    btn_toggle_usb.config(
        text=f"USB Lock: {'ON' if daemon_state['usb-lock']['active'] else 'OFF'}"
    )
    btn_toggle_network.config(
        text=f"Network Isolation: {'ON' if daemon_state['network']['active'] else 'OFF'}"
    )
    btn_toggle_gps.config(
        text=f"GPS: {'DISABLED' if daemon_state['gps']['active'] else 'TRACKING'}"
    )


def on_close():
    network_server.stop()
    ws_server.stop()
    webcam_controller.stop()
    try:
        audio_meter.stop()
    except Exception:
        pass
    root.destroy()


# ===== AVATAR DRAWING =====
def draw_avatar_on_canvas(canvas):
    """Draw the robot avatar on the given Canvas based on current state and config."""
    canvas.delete("all")

    primary  = avatar_config.get("primaryColor", "#2563EB")
    accent   = avatar_config.get("accentColor",  "#1E3A5F")
    name     = avatar_config.get("name",         "JamesBot")
    shape    = avatar_config.get("bodyShape",    "compact")
    face     = avatar_config.get("faceStyle",    "friendly")
    acc_list = avatar_config.get("accessories",  [])

    score = _calculate_privacy_score()

    if score >= 70:
        health_color = "#22c55e"
    elif score >= 30:
        health_color = "#f59e0b"
    else:
        health_color = "#ef4444"

    cam_on = daemon_state.get("camera-control", {}).get("active", True)
    mic_on = daemon_state.get("mic-control",    {}).get("active", True)
    net_on = daemon_state.get("network",        {}).get("active", False)
    gps_on = daemon_state.get("gps",            {}).get("active", False)
    usb_on = daemon_state.get("usb-lock",       {}).get("active", True)

    eye_color   = "#ef4444" if cam_on else "#22c55e"
    mouth_color = "#ef4444" if mic_on else "#22c55e"
    net_color   = "#22c55e" if net_on else "#6b7280"
    gps_color   = "#22c55e" if gps_on else "#6b7280"
    usb_color   = "#22c55e" if usb_on else "#6b7280"

    cx = 85  # center x of 170px-wide canvas

    # Body shape parameters
    if shape == "tall":
        head_y, head_h = 18, 46
        body_y, body_h = 70, 68
        leg_len = 44
    elif shape == "floating":
        head_y, head_h = 24, 44
        body_y, body_h = 74, 50
        leg_len = 28
    else:  # compact
        head_y, head_h = 22, 46
        body_y, body_h = 74, 55
        leg_len = 36

    head_x1 = cx - 27
    head_x2 = cx + 27
    head_y2  = head_y + head_h

    # == Top Hat accessory (draw before head so head sits on top) ==
    if "topHat" in acc_list:
        brim_y = head_y - 4
        canvas.create_rectangle(cx - 24, brim_y, cx + 24, brim_y + 8,
                                 fill=accent, outline=primary, width=1)
        canvas.create_rectangle(cx - 16, brim_y - 16, cx + 16, brim_y + 1,
                                 fill=accent, outline=primary, width=1)

    # == Antenna ==
    tip_y = head_y - 16
    # Second antenna (large antenna accessory)
    if "antenna" in acc_list:
        canvas.create_line(cx - 16, head_y, cx - 16, tip_y - 6,
                           fill=accent, width=2)
        canvas.create_oval(cx - 20, tip_y - 10, cx - 12, tip_y - 2,
                           fill=health_color, outline="")
    # Main antenna
    canvas.create_line(cx, head_y, cx, tip_y + 6, fill=primary, width=2)
    canvas.create_oval(cx - 5, tip_y, cx + 5, tip_y + 8,
                       fill=health_color, outline="")

    # == Head ==
    canvas.create_rectangle(head_x1, head_y, head_x2, head_y2,
                             fill=primary, outline=accent, width=2)

    eye_cy = head_y + int(head_h * 0.40)

    # == Eyes (face-style dependent) ==
    if face == "professional":
        # Single visor band
        canvas.create_rectangle(head_x1 + 5, eye_cy - 6,
                                 head_x2 - 5, eye_cy + 6,
                                 fill=eye_color, outline="")
        canvas.create_line(cx, eye_cy - 6, cx, eye_cy + 6,
                           fill=primary, width=2)
    elif face == "expressive":
        lx, rx = cx - 16, cx + 4
        canvas.create_oval(lx, eye_cy - 7, lx + 14, eye_cy + 7,
                           fill=eye_color, outline="")
        canvas.create_oval(rx, eye_cy - 7, rx + 14, eye_cy + 7,
                           fill=eye_color, outline="")
        # Eyebrows (angled for expression)
        canvas.create_line(lx - 1, eye_cy - 12, lx + 14, eye_cy - 10,
                           fill=eye_color, width=2)
        canvas.create_line(rx - 1, eye_cy - 10, rx + 15, eye_cy - 12,
                           fill=eye_color, width=2)
    else:  # friendly
        lx, rx = cx - 16, cx + 4
        canvas.create_oval(lx, eye_cy - 8, lx + 14, eye_cy + 6,
                           fill=eye_color, outline="")
        canvas.create_oval(rx, eye_cy - 8, rx + 14, eye_cy + 6,
                           fill=eye_color, outline="")

    # == Sunglasses accessory (over eyes) ==
    if "sunglasses" in acc_list:
        canvas.create_rectangle(head_x1 + 4, eye_cy - 9,
                                 cx - 2, eye_cy + 8,
                                 fill="#111827", outline=accent, width=1)
        canvas.create_rectangle(cx + 2, eye_cy - 9,
                                 head_x2 - 4, eye_cy + 8,
                                 fill="#111827", outline=accent, width=1)
        canvas.create_line(cx - 2, eye_cy - 1, cx + 2, eye_cy - 1,
                           fill=accent, width=1)

    # == Mouth ==
    mouth_y = head_y + int(head_h * 0.76)
    if score == 0:
        # Dead flat-line
        canvas.create_line(cx - 12, mouth_y, cx + 12, mouth_y,
                           fill="#ef4444", width=2, dash=(3, 2))
    elif mic_on:
        # Open/wavy (risky)
        canvas.create_arc(cx - 12, mouth_y - 6, cx + 12, mouth_y + 6,
                          start=0, extent=-180, style="arc",
                          outline=mouth_color, width=2)
    else:
        # Smile (safe)
        canvas.create_arc(cx - 12, mouth_y - 10, cx + 12, mouth_y + 6,
                          start=200, extent=140, style="arc",
                          outline=mouth_color, width=2)

    # == Scarf accessory ==
    if "scarf" in acc_list:
        scarf_y = head_y2
        canvas.create_rectangle(head_x1, scarf_y, head_x2, scarf_y + 8,
                                 fill="#f87171", outline="")

    # == Body ==
    body_x1 = cx - 24
    body_x2 = cx + 24
    body_y2  = body_y + body_h
    canvas.create_rectangle(body_x1, body_y, body_x2, body_y2,
                             fill=primary, outline=net_color, width=2)

    # Network symbol on torso
    net_sym = "◈" if net_on else "○"
    canvas.create_text(cx, body_y + body_h // 2,
                       text=net_sym, fill=net_color, font=("Helvetica", 11))

    # Star badge accessory
    if "starBadge" in acc_list:
        canvas.create_text(body_x2 - 4, body_y + 10,
                           text="★", fill="#fbbf24", font=("Helvetica", 9))

    # Key accessory
    if "key" in acc_list:
        canvas.create_text(body_x1 + 4, body_y + 10,
                           text="⚷", fill="#9ca3af", font=("Helvetica", 9))

    # == Arms ==
    arm_top = body_y + 6
    arm_bot = body_y + int(body_h * 0.55)
    arm_w   = 15
    canvas.create_rectangle(body_x1 - arm_w, arm_top, body_x1, arm_bot,
                             fill=primary, outline=usb_color, width=1)
    canvas.create_rectangle(body_x2, arm_top, body_x2 + arm_w, arm_bot,
                             fill=primary, outline=usb_color, width=1)

    # == Legs ==
    leg_top = body_y2
    leg_bot = leg_top + leg_len
    leg_w   = 13
    canvas.create_rectangle(cx - 20, leg_top, cx - 20 + leg_w, leg_bot,
                             fill=primary, outline=gps_color, width=1)
    canvas.create_rectangle(cx + 7,  leg_top, cx + 7  + leg_w, leg_bot,
                             fill=primary, outline=gps_color, width=1)

    # == Name ==
    name_y = leg_bot + 7
    canvas.create_text(cx, name_y, text=name,
                       fill="#94a3b8", font=("Helvetica", 9))

    # == Health bar ==
    bar_y  = name_y + 13
    bar_w  = 110
    bar_x  = cx - bar_w // 2
    canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + 6,
                             fill="#1e293b", outline="#334155")
    fill_w = int(bar_w * score / 100)
    if fill_w > 0:
        canvas.create_rectangle(bar_x, bar_y, bar_x + fill_w, bar_y + 6,
                                 fill=health_color, outline="")
    canvas.create_text(cx, bar_y + 15,
                       text=f"Privacy  {score}%",
                       fill=health_color, font=("Helvetica", 8))


# ===== GUI =====
root = tk.Tk()
root.title("PrivacyDeck Control")
root.geometry("530x740")
root.resizable(False, True)
root.configure(bg="#0f172a")

# ── Status bar ──────────────────────────────────────────────────────────────
top_bar = tk.Frame(root, bg="#0f172a", pady=4)
top_bar.pack(fill="x", padx=10)

tk.Label(top_bar, text="PrivacyDeck Control",
         font=("Helvetica", 13, "bold"), bg="#0f172a", fg="#f1f5f9").pack(side="left")

network_status_label = tk.Label(top_bar, text="Starting…",
                                 font=("Helvetica", 9), bg="#0f172a", fg="#64748b")
network_status_label.pack(side="right")

ttk.Separator(root, orient="horizontal").pack(fill="x")

# ── Notebook ─────────────────────────────────────────────────────────────────
style = ttk.Style()
style.theme_use("clam")
style.configure("TNotebook",        background="#0f172a", borderwidth=0)
style.configure("TNotebook.Tab",    background="#1e293b", foreground="#94a3b8",
                padding=[12, 5],    font=("Helvetica", 10))
style.map("TNotebook.Tab",
          background=[("selected", "#334155")],
          foreground=[("selected", "#f1f5f9")])
style.configure("TFrame", background="#0f172a")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=8, pady=6)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Simulator
# ─────────────────────────────────────────────────────────────────────────────
tab_sim = ttk.Frame(notebook)
notebook.add(tab_sim, text="  Simulator  ")

# Inner scroll canvas for the simulator tab (so it can expand vertically)
sim_scroll_frame = tk.Frame(tab_sim, bg="#0f172a")
sim_scroll_frame.pack(fill="both", expand=True, padx=6, pady=4)

# Two-column layout: device on left, avatar on right
sim_cols = tk.Frame(sim_scroll_frame, bg="#0f172a")
sim_cols.pack(fill="both", expand=True)

# ── Device body (left column) ────────────────────────────────────────────────
device_outer = tk.Frame(sim_cols, bg="#0f172a")
device_outer.pack(side="left", fill="both", expand=True, padx=(0, 6))

device_body = tk.Frame(device_outer, bg="#1e293b",
                        relief="flat", bd=0, padx=12, pady=12)
device_body.pack(fill="x")

# Device label
tk.Label(device_body,
         text="PrivacyDeck Pro",
         font=("Helvetica", 10, "bold"),
         bg="#1e293b", fg="#64748b").pack(anchor="center", pady=(0, 4))

# LED indicator row
led_frame = tk.Frame(device_body, bg="#1e293b")
led_frame.pack(anchor="center", pady=(0, 8))
_sim_led = tk.Canvas(led_frame, width=10, height=10, bg="#1e293b",
                      highlightthickness=0)
_sim_led.pack(side="left", padx=(0, 4))
_sim_led.create_oval(1, 1, 9, 9, fill="#22c55e", outline="")
tk.Label(led_frame, text="device active",
         font=("Helvetica", 8), bg="#1e293b", fg="#475569").pack(side="left")

# 2×2 grid of configurable buttons
btn_grid = tk.Frame(device_body, bg="#1e293b")
btn_grid.pack(anchor="center", pady=(0, 10))

_device_btn_refs = []   # list of (container_frame, tk.Button) tuples

BUTTON_COLORS_ORDERED = ["#82b366", "#82b366", "#82b366", "#82b366"]

for row in range(2):
    for col in range(2):
        idx = row * 2 + col
        container = tk.Frame(btn_grid, width=112, height=88, bg="#1e293b")
        container.grid(row=row, column=col, padx=5, pady=5)
        container.pack_propagate(False)

        feature_id = button_mapping[idx] if idx < len(button_mapping) else "camera-control"
        bg_c, fg_c = _get_feature_color(feature_id)
        state_txt  = "ON" if daemon_state.get(feature_id, {}).get("active", False) else "OFF"
        fname      = FEATURE_NAMES.get(feature_id, feature_id)

        btn = tk.Button(
            container,
            text=f"BTN {idx + 1}\n{fname}\n[{state_txt}]",
            font=("Helvetica", 9, "bold"),
            bg=bg_c, fg=fg_c,
            activebackground=bg_c, activeforeground=fg_c,
            relief="flat", bd=0, cursor="hand2",
            command=lambda i=idx: handle_network_event(f"button_{i}"),
        )
        btn.pack(fill="both", expand=True)
        _device_btn_refs.append((container, btn))

# LOCK button (mandatory)
lock_sep = tk.Frame(device_body, bg="#334155", height=1)
lock_sep.pack(fill="x", pady=(4, 8))

lock_container = tk.Frame(device_body, width=254, height=56, bg="#1e293b")
lock_container.pack(anchor="center")
lock_container.pack_propagate(False)

btn_sim_lock = tk.Button(
    lock_container,
    text="🔒  LOCK SYSTEM  🔒",
    font=("Helvetica", 10, "bold"),
    bg="#7c3aed", fg="#ffffff",
    activebackground="#6d28d9", activeforeground="#ffffff",
    relief="flat", bd=0, cursor="hand2",
    command=lambda: handle_network_event("lock_system"),
)
btn_sim_lock.pack(fill="both", expand=True)

# ── Avatar panel (right column) ──────────────────────────────────────────────
avatar_outer = tk.Frame(sim_cols, bg="#0f172a")
avatar_outer.pack(side="left", fill="y")

avatar_panel = tk.Frame(avatar_outer, bg="#1e293b",
                         relief="flat", bd=0, padx=8, pady=8)
avatar_panel.pack(fill="both", expand=True)

tk.Label(avatar_panel, text="Avatar",
         font=("Helvetica", 10, "bold"),
         bg="#1e293b", fg="#64748b").pack()

avatar_canvas = tk.Canvas(avatar_panel, width=170, height=230,
                            bg="#0f172a", highlightthickness=0)
avatar_canvas.pack(pady=(4, 0))


def update_avatar_canvas():
    draw_avatar_on_canvas(avatar_canvas)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Controls
# ─────────────────────────────────────────────────────────────────────────────
tab_ctrl = ttk.Frame(notebook)
notebook.add(tab_ctrl, text="  Controls  ")

ctrl_inner = tk.Frame(tab_ctrl, bg="#0f172a")
ctrl_inner.pack(fill="both", expand=True, padx=8, pady=6)

# Demo mode section
demo_frame = tk.Frame(ctrl_inner, bg="#1e293b", padx=10, pady=10, relief="flat")
demo_frame.pack(fill="x", pady=(0, 8))

tk.Label(demo_frame, text="Demo Mode",
         font=("Helvetica", 10, "bold"),
         bg="#1e293b", fg="#f1f5f9").pack()

btn_demo = tk.Button(
    demo_frame, text="Demo Mode: OFF", width=22, height=2,
    command=toggle_demo_mode,
    bg="#1e293b", fg="#94a3b8", relief="raised",
)
btn_demo.pack(pady=(4, 2))

demo_status_label = tk.Label(demo_frame, text="", fg="gray",
                               font=("Helvetica", 9), bg="#1e293b")
demo_status_label.pack()

btn_run_demo = tk.Button(
    demo_frame, text="Run Demo Sequence", width=22, height=2,
    state="disabled", command=run_demo_sequence,
    bg="#1e293b", fg="#64748b", relief="raised",
)
btn_run_demo.pack(pady=(4, 2))

# Webcam + audio meter (side by side)
top_row = tk.Frame(ctrl_inner, bg="#0f172a")
top_row.pack(pady=6)

webcam_controller = WebcamController(top_row)
try:
    webcam_controller._frame.pack_forget()
except Exception:
    pass
webcam_controller._frame.pack(side="left", padx=(0, 6))

audio_meter = AudioMeterWidget(top_row, width=80, height=160)
audio_meter.pack(side="left")

# Start servers (needs webcam_controller and audio_meter to exist)
network_server = PicoNetworkServer(
    host=SERVER_HOST,
    port=SERVER_PORT,
    event_callback=handle_network_event,
    status_callback=update_network_status,
)
network_server.start()

ws_server = DashboardWebSocketServer(
    port=WS_PORT,
    get_state=get_state,
    handle_command=handle_command,
    status_callback=update_network_status,
)
ws_server.start()

# Toggle buttons
label_toggle = tk.Label(ctrl_inner, text="Feature Toggles:",
                         font=("Helvetica", 9, "bold"),
                         bg="#0f172a", fg="#94a3b8")
label_toggle.pack(pady=(8, 0))

btn_toggle_mic = tk.Button(
    ctrl_inner, text="Mic: Active", width=22, height=2,
    command=toggle_mic,
)
btn_toggle_mic.pack(pady=3)

btn_toggle_usb = tk.Button(
    ctrl_inner, text="USB Lock: ON", width=22, height=2,
    command=toggle_usb,
)
btn_toggle_usb.pack(pady=3)

btn_toggle_network = tk.Button(
    ctrl_inner, text="Network Isolation: OFF", width=22, height=2,
    command=toggle_airplane_mode,
)
btn_toggle_network.pack(pady=3)

btn_toggle_gps = tk.Button(
    ctrl_inner, text="GPS: TRACKING", width=22, height=2,
    command=toggle_location,
)
btn_toggle_gps.pack(pady=3)

label_webcam = tk.Label(ctrl_inner, text="Webcam Privacy",
                         font=("Helvetica", 9), bg="#0f172a", fg="#94a3b8")
label_webcam.pack(pady=(6, 0))

slider_webcam = tk.Scale(
    ctrl_inner, from_=0, to=100,
    orient="horizontal", length=220,
    command=set_webcam_privacy,
    bg="#0f172a", fg="#94a3b8", highlightthickness=0,
    troughcolor="#1e293b",
)
slider_webcam.set(0)
slider_webcam.pack(pady=(0, 6))
set_webcam_privacy(0)

tk.Label(ctrl_inner, text="Actions:",
         font=("Helvetica", 9, "bold"),
         bg="#0f172a", fg="#94a3b8").pack(pady=(6, 0))

btn_lock = tk.Button(
    ctrl_inner, text="Lock OS", width=22, height=2,
    command=lock_system,
)
btn_lock.pack(pady=3)

btn_clipboard = tk.Button(
    ctrl_inner, text="Wipe Clipboard History", width=22, height=2,
    command=wipe_clipboard,
)
btn_clipboard.pack(pady=3)

btn_blackout = tk.Button(
    ctrl_inner, text="Blackout Screen", width=22, height=2,
    command=show_blackout,
)
btn_blackout.pack(pady=3)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Avatar Config
# ─────────────────────────────────────────────────────────────────────────────
tab_avatar = ttk.Frame(notebook)
notebook.add(tab_avatar, text="  Avatar  ")

av_scroll = tk.Frame(tab_avatar, bg="#0f172a")
av_scroll.pack(fill="both", expand=True, padx=8, pady=6)

tk.Label(av_scroll, text="Avatar Configuration",
         font=("Helvetica", 12, "bold"),
         bg="#0f172a", fg="#f1f5f9").pack(pady=(0, 6))

# ── Name ────────────────────────────────────────────────────────────────────
name_frame = tk.Frame(av_scroll, bg="#1e293b", padx=10, pady=8)
name_frame.pack(fill="x", pady=(0, 6))

tk.Label(name_frame, text="Name", font=("Helvetica", 9, "bold"),
         bg="#1e293b", fg="#94a3b8").pack(anchor="w")

av_name_var = tk.StringVar(value=avatar_config.get("name", "JamesBot"))
name_entry = tk.Entry(name_frame, textvariable=av_name_var,
                       font=("Helvetica", 10), width=20,
                       bg="#334155", fg="#f1f5f9",
                       insertbackground="#f1f5f9",
                       relief="flat", bd=4)
name_entry.pack(anchor="w", pady=(4, 0))

# ── Color Scheme ─────────────────────────────────────────────────────────────
color_frame = tk.Frame(av_scroll, bg="#1e293b", padx=10, pady=8)
color_frame.pack(fill="x", pady=(0, 6))

tk.Label(color_frame, text="Color Scheme", font=("Helvetica", 9, "bold"),
         bg="#1e293b", fg="#94a3b8").pack(anchor="w")

av_color_var = tk.StringVar(value=avatar_config.get("colorScheme", "shieldBlue"))
av_primary_var = tk.StringVar(value=avatar_config.get("primaryColor", "#2563EB"))
av_accent_var  = tk.StringVar(value=avatar_config.get("accentColor",  "#1E3A5F"))

color_btn_frame = tk.Frame(color_frame, bg="#1e293b")
color_btn_frame.pack(anchor="w", pady=(6, 0))

_color_btns = {}
for scheme_key, scheme_val in COLOR_PRESETS.items():
    btn_c = tk.Button(
        color_btn_frame,
        text=scheme_val["label"],
        font=("Helvetica", 8),
        bg=scheme_val["primary"], fg="#ffffff",
        activebackground=scheme_val["primary"],
        relief="raised", bd=2, padx=6, pady=3,
        cursor="hand2",
    )
    btn_c.pack(side="left", padx=2, pady=2)
    _color_btns[scheme_key] = btn_c


def _select_color_scheme(key):
    av_color_var.set(key)
    preset = COLOR_PRESETS[key]
    av_primary_var.set(preset["primary"])
    av_accent_var.set(preset["accent"])
    for k, b in _color_btns.items():
        b.config(relief="sunken" if k == key else "raised")


for scheme_key in COLOR_PRESETS:
    _color_btns[scheme_key].config(
        command=lambda k=scheme_key: _select_color_scheme(k)
    )

# Highlight current selection
_select_color_scheme(av_color_var.get())

# Custom color pickers
custom_row = tk.Frame(color_frame, bg="#1e293b")
custom_row.pack(anchor="w", pady=(4, 0))

tk.Label(custom_row, text="Primary:", font=("Helvetica", 8),
         bg="#1e293b", fg="#94a3b8").pack(side="left")
_prim_swatch = tk.Label(custom_row, bg=av_primary_var.get(),
                         width=4, relief="raised", cursor="hand2")
_prim_swatch.pack(side="left", padx=4)
tk.Label(custom_row, text=av_primary_var.get(),
         textvariable=av_primary_var,
         font=("Helvetica", 8), bg="#1e293b", fg="#94a3b8").pack(side="left")

tk.Label(custom_row, text="  Accent:", font=("Helvetica", 8),
         bg="#1e293b", fg="#94a3b8").pack(side="left")
_acc_swatch = tk.Label(custom_row, bg=av_accent_var.get(),
                        width=4, relief="raised", cursor="hand2")
_acc_swatch.pack(side="left", padx=4)


def _pick_primary():
    import tkinter.colorchooser as cc
    color = cc.askcolor(color=av_primary_var.get(), title="Primary Color")[1]
    if color:
        av_primary_var.set(color)
        _prim_swatch.config(bg=color)
        av_color_var.set("custom")
        for b in _color_btns.values():
            b.config(relief="raised")


def _pick_accent():
    import tkinter.colorchooser as cc
    color = cc.askcolor(color=av_accent_var.get(), title="Accent Color")[1]
    if color:
        av_accent_var.set(color)
        _acc_swatch.config(bg=color)
        av_color_var.set("custom")
        for b in _color_btns.values():
            b.config(relief="raised")


_prim_swatch.bind("<Button-1>", lambda e: _pick_primary())
_acc_swatch.bind("<Button-1>",  lambda e: _pick_accent())

# ── Body Shape ───────────────────────────────────────────────────────────────
shape_frame = tk.Frame(av_scroll, bg="#1e293b", padx=10, pady=8)
shape_frame.pack(fill="x", pady=(0, 6))

tk.Label(shape_frame, text="Body Shape", font=("Helvetica", 9, "bold"),
         bg="#1e293b", fg="#94a3b8").pack(anchor="w")

av_shape_var = tk.StringVar(value=avatar_config.get("bodyShape", "compact"))
shape_row = tk.Frame(shape_frame, bg="#1e293b")
shape_row.pack(anchor="w", pady=(4, 0))

for shape_id, shape_label in [("compact", "Compact"), ("tall", "Tall"), ("floating", "Floating")]:
    tk.Radiobutton(
        shape_row, text=shape_label, variable=av_shape_var, value=shape_id,
        font=("Helvetica", 9), bg="#1e293b", fg="#f1f5f9",
        activebackground="#1e293b", activeforeground="#f1f5f9",
        selectcolor="#334155",
    ).pack(side="left", padx=8)

# ── Face Style ───────────────────────────────────────────────────────────────
face_frame = tk.Frame(av_scroll, bg="#1e293b", padx=10, pady=8)
face_frame.pack(fill="x", pady=(0, 6))

tk.Label(face_frame, text="Face Style", font=("Helvetica", 9, "bold"),
         bg="#1e293b", fg="#94a3b8").pack(anchor="w")

av_face_var = tk.StringVar(value=avatar_config.get("faceStyle", "friendly"))
face_row = tk.Frame(face_frame, bg="#1e293b")
face_row.pack(anchor="w", pady=(4, 0))

for face_id, face_label in [("friendly", "Friendly"), ("professional", "Professional"), ("expressive", "Expressive")]:
    tk.Radiobutton(
        face_row, text=face_label, variable=av_face_var, value=face_id,
        font=("Helvetica", 9), bg="#1e293b", fg="#f1f5f9",
        activebackground="#1e293b", activeforeground="#f1f5f9",
        selectcolor="#334155",
    ).pack(side="left", padx=6)

# ── Accessories ──────────────────────────────────────────────────────────────
acc_frame = tk.Frame(av_scroll, bg="#1e293b", padx=10, pady=8)
acc_frame.pack(fill="x", pady=(0, 6))

tk.Label(acc_frame, text="Accessories", font=("Helvetica", 9, "bold"),
         bg="#1e293b", fg="#94a3b8").pack(anchor="w")

_ACCESSORY_LIST = [
    ("topHat",     "Top Hat"),
    ("sunglasses", "Sunglasses"),
    ("scarf",      "Scarf"),
    ("starBadge",  "Star Badge"),
    ("antenna",    "Large Antenna"),
    ("key",        "Key"),
]

_acc_vars = {}
acc_grid = tk.Frame(acc_frame, bg="#1e293b")
acc_grid.pack(anchor="w", pady=(4, 0))

current_accessories = list(avatar_config.get("accessories", []))
for i, (acc_id, acc_label) in enumerate(_ACCESSORY_LIST):
    var = tk.BooleanVar(value=acc_id in current_accessories)
    _acc_vars[acc_id] = var
    row_i, col_i = divmod(i, 3)
    tk.Checkbutton(
        acc_grid, text=acc_label, variable=var,
        font=("Helvetica", 9), bg="#1e293b", fg="#f1f5f9",
        activebackground="#1e293b", activeforeground="#f1f5f9",
        selectcolor="#334155",
    ).grid(row=row_i, column=col_i, sticky="w", padx=4, pady=2)

# ── Animation Style ──────────────────────────────────────────────────────────
anim_frame = tk.Frame(av_scroll, bg="#1e293b", padx=10, pady=8)
anim_frame.pack(fill="x", pady=(0, 6))

tk.Label(anim_frame, text="Animation Style", font=("Helvetica", 9, "bold"),
         bg="#1e293b", fg="#94a3b8").pack(anchor="w")

av_anim_var = tk.StringVar(value=avatar_config.get("animationStyle", "reactive"))
anim_row = tk.Frame(anim_frame, bg="#1e293b")
anim_row.pack(anchor="w", pady=(4, 0))

for anim_id, anim_label in [("reactive", "Reactive"), ("lively", "Lively")]:
    tk.Radiobutton(
        anim_row, text=anim_label, variable=av_anim_var, value=anim_id,
        font=("Helvetica", 9), bg="#1e293b", fg="#f1f5f9",
        activebackground="#1e293b", activeforeground="#f1f5f9",
        selectcolor="#334155",
    ).pack(side="left", padx=8)


# ── Apply / Reset buttons ────────────────────────────────────────────────────
def _apply_avatar_config():
    """Save avatar config from GUI fields, broadcast to dashboard."""
    global avatar_config
    selected_accessories = [k for k, v in _acc_vars.items() if v.get()]
    avatar_config.update({
        "name":          av_name_var.get().strip() or "JamesBot",
        "colorScheme":   av_color_var.get(),
        "primaryColor":  av_primary_var.get(),
        "accentColor":   av_accent_var.get(),
        "bodyShape":     av_shape_var.get(),
        "faceStyle":     av_face_var.get(),
        "accessories":   selected_accessories,
        "animationStyle": av_anim_var.get(),
    })
    _save_avatar_config()
    update_avatar_canvas()
    # Broadcast to all connected dashboard clients
    import asyncio as _aio
    _state_msg = json.dumps({"type": "state", **get_state()})
    if ws_server._loop is not None:
        _aio.run_coroutine_threadsafe(ws_server._broadcast(_state_msg), ws_server._loop)


def _refresh_avatar_config_ui():
    """Update Avatar tab widgets from current avatar_config (called after WS sync)."""
    av_name_var.set(avatar_config.get("name", "JamesBot"))
    scheme = avatar_config.get("colorScheme", "shieldBlue")
    av_color_var.set(scheme)
    av_primary_var.set(avatar_config.get("primaryColor", "#2563EB"))
    av_accent_var.set(avatar_config.get("accentColor",  "#1E3A5F"))
    av_shape_var.set(avatar_config.get("bodyShape",    "compact"))
    av_face_var.set(avatar_config.get("faceStyle",     "friendly"))
    av_anim_var.set(avatar_config.get("animationStyle","reactive"))
    current_acc = avatar_config.get("accessories", [])
    for acc_id, var in _acc_vars.items():
        var.set(acc_id in current_acc)
    _prim_swatch.config(bg=av_primary_var.get())
    _acc_swatch.config(bg=av_accent_var.get())
    if scheme in _color_btns:
        _select_color_scheme(scheme)


btn_row = tk.Frame(av_scroll, bg="#0f172a")
btn_row.pack(fill="x", pady=(4, 0))

tk.Button(
    btn_row,
    text="Apply Changes",
    font=("Helvetica", 10, "bold"),
    bg="#2563eb", fg="#ffffff",
    activebackground="#1d4ed8",
    relief="flat", bd=0, padx=20, pady=8,
    cursor="hand2",
    command=_apply_avatar_config,
).pack(side="left", padx=(0, 8))

tk.Button(
    btn_row,
    text="Reset Default",
    font=("Helvetica", 9),
    bg="#334155", fg="#94a3b8",
    relief="flat", bd=0, padx=12, pady=8,
    cursor="hand2",
    command=lambda: (
        avatar_config.update(DEFAULT_AVATAR_CONFIG),
        _save_avatar_config(),
        _refresh_avatar_config_ui(),
        update_avatar_canvas(),
    ),
).pack(side="left")


# ─────────────────────────────────────────────────────────────────────────────
# DEVICE BUTTON UPDATE (simulator tab)
# ─────────────────────────────────────────────────────────────────────────────
def update_device_buttons():
    """Refresh simulator button labels and colors based on current state."""
    for i, (container, btn) in enumerate(_device_btn_refs):
        if i >= len(button_mapping):
            continue
        feature_id = button_mapping[i]
        bg_c, fg_c = _get_feature_color(feature_id)
        is_active  = daemon_state.get(feature_id, {}).get("active", False)
        state_txt  = "ON" if is_active else "OFF"
        fname      = FEATURE_NAMES.get(feature_id, feature_id)
        btn.config(
            text=f"BTN {i + 1}\n{fname}\n[{state_txt}]",
            bg=bg_c, fg=fg_c,
            activebackground=bg_c, activeforeground=fg_c,
        )


# ── Register callbacks ────────────────────────────────────────────────────────
_gui_callbacks["device_buttons"] = update_device_buttons
_gui_callbacks["avatar"]         = update_avatar_canvas
_gui_callbacks["controls_labels"] = _refresh_button_labels

# ── Initial draw ─────────────────────────────────────────────────────────────
update_device_buttons()
update_avatar_canvas()

# ─────────────────────────────────────────────────────────────────────────────
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
