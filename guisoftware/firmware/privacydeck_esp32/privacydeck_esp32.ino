/*
 * PrivacyDeck — ESP32 Hardware Client
 * ====================================
 * Connects to the PrivacyDeck daemon over TCP (port 50555) and maps
 * physical buttons to the EVENT protocol.
 *
 * Board: ESP32 (any ESP32-DevKitC / WROOM / WROVER)
 * IDE:   Arduino IDE 2.x  +  esp32 core by Espressif (≥ 2.0)
 *
 * ── Pin Map ──────────────────────────────────────────────────
 *   GPIO 12  →  BUTTON_1     (default: camera-control)
 *   GPIO 13  →  BUTTON_2     (default: mic-control)
 *   GPIO 14  →  BUTTON_3     (default: network isolation)
 *   GPIO 15  →  BUTTON_4     (default: GPS toggle)
 *   GPIO 16  →  LOCK_BUTTON  (locks the host OS)
 *   GPIO  2  →  Status LED   (built-in on most DevKit boards)
 *
 * All buttons: wire between GPIO pin and GND.  INPUT_PULLUP is used,
 * so the pin reads LOW when the button is pressed.
 *
 * ── Protocol ─────────────────────────────────────────────────
 *   ESP → Daemon:   HELLO PRIVACYDECK_PICO 1\n
 *   Daemon → ESP:   HELLO_ACK PRIVACYDECK_DAEMON 1\n
 *   ESP → Daemon:   PING\n               (keepalive)
 *   Daemon → ESP:   PONG\n
 *   ESP → Daemon:   EVENT BUTTON_1 pressed\n   … BUTTON_4
 *   ESP → Daemon:   EVENT LOCK_BUTTON pressed\n
 *   Daemon → ESP:   OK\n  (or ERR …\n)
 */

#include <WiFi.h>
#include <WiFiClient.h>

// ─── USER CONFIGURATION ──────────────────────────────────────
// Wi-Fi credentials
const char* WIFI_SSID     = "YOUR_SSID";
const char* WIFI_PASSWORD = "YOUR_PASSWORD";

// Daemon host / port
const char*    SERVER_HOST = "10.183.219.76";
const uint16_t SERVER_PORT = 50555;
// ─────────────────────────────────────────────────────────────

// GPIO pin assignments
static const int PIN_BUTTON_1    = 12;
static const int PIN_BUTTON_2    = 13;
static const int PIN_BUTTON_3    = 14;
static const int PIN_BUTTON_4    = 15;
static const int PIN_LOCK_BUTTON = 16;
static const int PIN_LED_STATUS  =  2;  // onboard LED (active HIGH on most boards)

// Timing
static const uint32_t DEBOUNCE_MS      =    50;   // button debounce window
static const uint32_t PING_INTERVAL_MS = 15000;   // keepalive interval
static const uint32_t READ_TIMEOUT_MS  =  3000;   // max wait for a server reply
static const uint32_t RECONNECT_BASE_MS =  2000;  // initial reconnect delay
static const uint32_t RECONNECT_MAX_MS = 30000;   // reconnect back-off ceiling

// ─── Button table ─────────────────────────────────────────────
struct ButtonDef {
    int         pin;
    const char* event;   // full line sent to the daemon (without \n)
};

static const ButtonDef BUTTONS[] = {
    { PIN_BUTTON_1,    "EVENT BUTTON_1 pressed"    },
    { PIN_BUTTON_2,    "EVENT BUTTON_2 pressed"    },
    { PIN_BUTTON_3,    "EVENT BUTTON_3 pressed"    },
    { PIN_BUTTON_4,    "EVENT BUTTON_4 pressed"    },
    { PIN_LOCK_BUTTON, "EVENT LOCK_BUTTON pressed" },
};
static const int NUM_BUTTONS = sizeof(BUTTONS) / sizeof(BUTTONS[0]);

// ─── Runtime state ────────────────────────────────────────────
WiFiClient client;
bool       handshakeDone = false;
uint32_t   lastPingMs    = 0;
uint32_t   reconnectDelayMs = RECONNECT_BASE_MS;

// Per-button debounce (edge-detection on stable state)
bool     lastRawState[NUM_BUTTONS];
bool     lastStableState[NUM_BUTTONS];
uint32_t debounceStart[NUM_BUTTONS];

// ─── Helpers ─────────────────────────────────────────────────

void setLed(bool on) {
    digitalWrite(PIN_LED_STATUS, on ? HIGH : LOW);
}

/* Send msg + '\n' over the open TCP connection */
void sendLine(const char* msg) {
    client.print(msg);
    client.print('\n');
    Serial.print(F("[TX] "));
    Serial.println(msg);
}

/*
 * Read one '\n'-terminated line from the server.
 * Returns an empty String on timeout or disconnection.
 * Strips trailing '\r' so the caller can use simple equality.
 */
String readLine(uint32_t timeoutMs = READ_TIMEOUT_MS) {
    String   line;
    uint32_t deadline = millis() + timeoutMs;

    while (millis() < deadline) {
        if (!client.connected()) break;
        while (client.available()) {
            char c = static_cast<char>(client.read());
            if (c == '\n') {
                line.trim();
                Serial.print(F("[RX] "));
                Serial.println(line);
                return line;
            }
            if (c != '\r') line += c;
        }
        delay(5);
    }
    return "";  // timeout or disconnected
}

// ─── Wi-Fi ───────────────────────────────────────────────────

void connectWiFi() {
    Serial.print(F("[WiFi] Connecting to "));
    Serial.print(WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print('.');
    }
    Serial.print(F("\n[WiFi] Connected — IP: "));
    Serial.println(WiFi.localIP());
}

// ─── TCP + Handshake ─────────────────────────────────────────

bool doHandshake() {
    sendLine("HELLO PRIVACYDECK_PICO 1");
    String ack = readLine(5000);   // give the daemon 5 s to respond
    if (ack == "HELLO_ACK PRIVACYDECK_DAEMON 1") {
        Serial.println(F("[TCP] Handshake OK"));
        return true;
    }
    Serial.print(F("[TCP] Handshake failed — got: "));
    Serial.println(ack);
    return false;
}

bool connectToServer() {
    Serial.print(F("[TCP] Connecting to "));
    Serial.print(SERVER_HOST);
    Serial.print(':');
    Serial.println(SERVER_PORT);

    if (!client.connect(SERVER_HOST, SERVER_PORT)) {
        Serial.println(F("[TCP] Connection refused"));
        return false;
    }
    client.setNoDelay(true);

    if (!doHandshake()) {
        client.stop();
        return false;
    }

    handshakeDone     = true;
    lastPingMs        = millis();
    reconnectDelayMs  = RECONNECT_BASE_MS;   // reset back-off on success
    setLed(true);
    Serial.println(F("[TCP] Ready — waiting for button presses"));
    return true;
}

void handleDisconnect() {
    handshakeDone = false;
    client.stop();
    setLed(false);
    Serial.print(F("[TCP] Disconnected — retry in "));
    Serial.print(reconnectDelayMs);
    Serial.println(F(" ms"));
}

// ─── Arduino entry points ────────────────────────────────────

void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.println(F("\n=== PrivacyDeck ESP32 ==="));

    pinMode(PIN_LED_STATUS, OUTPUT);
    setLed(false);

    // Initialise all button pins and debounce state.
    // raw = (digitalRead(pin) == LOW): false = not pressed, true = pressed.
    for (int i = 0; i < NUM_BUTTONS; i++) {
        pinMode(BUTTONS[i].pin, INPUT_PULLUP);
        lastRawState[i]    = false;  // not pressed
        lastStableState[i] = false;
        debounceStart[i]   = 0;
    }

    connectWiFi();
    connectToServer();
}

void loop() {
    // ── 1. Re-connect if the link dropped ──────────────────────
    if (!client.connected() || !handshakeDone) {
        if (handshakeDone) handleDisconnect();

        delay(reconnectDelayMs);
        reconnectDelayMs = min(reconnectDelayMs * 2, RECONNECT_MAX_MS);

        if (WiFi.status() != WL_CONNECTED) connectWiFi();
        connectToServer();
        return;
    }

    // ── 2. Drain any unsolicited server data ───────────────────
    while (client.available()) {
        readLine(100);   // consume; nothing to act on here
    }

    // ── 3. Periodic PING keepalive ─────────────────────────────
    uint32_t now = millis();
    if (now - lastPingMs >= PING_INTERVAL_MS) {
        lastPingMs = now;
        sendLine("PING");
        String pong = readLine();
        if (pong != "PONG") {
            Serial.print(F("[TCP] Expected PONG, got: "));
            Serial.print(pong);
            Serial.println(F(" — reconnecting"));
            handleDisconnect();
            return;
        }
    }

    // ── 4. Poll buttons with debounce ─────────────────────────
    now = millis();
    for (int i = 0; i < NUM_BUTTONS; i++) {
        bool raw = (digitalRead(BUTTONS[i].pin) == LOW);   // LOW = pressed

        // Restart debounce timer whenever the raw reading changes
        if (raw != lastRawState[i]) {
            lastRawState[i]  = raw;
            debounceStart[i] = now;
        }

        // Only act once the reading has been stable for DEBOUNCE_MS
        if ((now - debounceStart[i]) >= DEBOUNCE_MS) {
            bool stable = raw;
            if (stable != lastStableState[i]) {
                lastStableState[i] = stable;

                if (stable) {
                    // Falling edge → button pressed → send event
                    sendLine(BUTTONS[i].event);

                    String resp = readLine();
                    if (resp == "OK") {
                        Serial.print(F("[OK] "));
                        Serial.println(BUTTONS[i].event);
                    } else {
                        Serial.print(F("[ERR] Response for '"));
                        Serial.print(BUTTONS[i].event);
                        Serial.print(F("': "));
                        Serial.println(resp);
                    }
                }
                // Rising edge (button released) — nothing to send
            }
        }
    }

    delay(5);   // ~200 Hz poll rate — keeps buttons responsive
}
