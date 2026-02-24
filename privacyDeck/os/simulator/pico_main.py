import machine
import network
import socket
import time

 
WIFI_SSID = "Simon69"
WIFI_PASSWORD = "25062506"
DAEMON_HOST = "10.174.249.146"
DAEMON_PORT = 50555
BUTTON_PIN = 1
TOGGLE_USB_PIN = 5
TOGGLE_AIRPLANE_PIN = 6
TOGGLE_BLACKOUT_PIN = 7
TOGGLE_MIC_PIN = 8
DEBOUNCE_MS = 250

# Controls are wired to 3V3, so inputs use PULL_DOWN and read 1 when active.
EVENTS = [
	{"name": "LOCK_BUTTON", "pin_num": BUTTON_PIN, "event": "EVENT LOCK_BUTTON pressed"},
	{"name": "TOGGLE_USB", "pin_num": TOGGLE_USB_PIN, "event": "EVENT TOGGLE_USB changed"},
	{"name": "TOGGLE_AIRPLANE", "pin_num": TOGGLE_AIRPLANE_PIN, "event": "EVENT TOGGLE_AIRPLANE changed"},
	{"name": "TOGGLE_BLACKOUT", "pin_num": TOGGLE_BLACKOUT_PIN, "event": "EVENT TOGGLE_BLACKOUT changed"},
	{"name": "TOGGLE_MIC", "pin_num": TOGGLE_MIC_PIN, "event": "EVENT TOGGLE_MIC changed"},
]


def connect_wifi():
	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	if wlan.isconnected():
		return wlan

	wlan.connect(WIFI_SSID, WIFI_PASSWORD)
	started = time.ticks_ms()
	while not wlan.isconnected():
		if time.ticks_diff(time.ticks_ms(), started) > 20000:
			raise OSError("wifi_timeout")
		time.sleep_ms(200)
	return wlan


def send_line(sock, text):
	sock.send((text + "\n").encode())


def recv_line(sock):
	data = bytearray()
	while True:
		chunk = sock.recv(1)
		if not chunk:
			raise OSError("socket_closed")
		if chunk == b"\n":
			break
		data.extend(chunk)
	return data.decode().strip()


def connect_daemon():
	addr = socket.getaddrinfo(DAEMON_HOST, DAEMON_PORT)[0][-1]
	sock = socket.socket()
	sock.settimeout(10)
	sock.connect(addr)
	send_line(sock, "HELLO PRIVACYDECK_PICO 1")
	ack = recv_line(sock)
	if ack != "HELLO_ACK PRIVACYDECK_DAEMON 1":
		sock.close()
		raise OSError("bad_handshake")
	sock.settimeout(2)
	return sock


def run():
	controls = []
	for item in EVENTS:
		pin = machine.Pin(item["pin_num"], machine.Pin.IN, machine.Pin.PULL_DOWN)
		controls.append(
			{
				"name": item["name"],
				"pin": pin,
				"event": item["event"],
				"last_state": pin.value(),
				"last_change_ms": 0,
			}
		)

	sock = None

	while True:
		try:
			connect_wifi()
			if sock is None:
				sock = connect_daemon()
				print("Connected to daemon")

			for control in controls:
				current_state = control["pin"].value()
				if current_state != control["last_state"]:
					now = time.ticks_ms()
					if time.ticks_diff(now, control["last_change_ms"]) > DEBOUNCE_MS:
						if control["name"] != "LOCK_BUTTON":
							state_text = "ON" if current_state == 1 else "OFF"
							print(control["name"], "switched:", state_text)
						send_line(sock, control["event"])
						print(control["event"])
						response = recv_line(sock)
						print("Event response:", response)
						control["last_change_ms"] = now
					control["last_state"] = current_state

			time.sleep_ms(25)
		except OSError as exc:
			print("Connection issue:", exc)
			if sock is not None:
				try:
					sock.close()
				except OSError:
					pass
			sock = None
			time.sleep(2)


run()

