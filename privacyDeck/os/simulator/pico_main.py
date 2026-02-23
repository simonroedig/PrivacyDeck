import machine
import network
import socket
import time

 
WIFI_SSID = "Simon69"
WIFI_PASSWORD = "25062506"
DAEMON_HOST = "10.174.249.146"
DAEMON_PORT = 50555
BUTTON_PIN = 1
DEBOUNCE_MS = 250


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
	button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
	last_button_state = button.value()
	last_press_ms = 0
	sock = None

	while True:
		try:
			connect_wifi()
			if sock is None:
				sock = connect_daemon()
				print("Connected to daemon")

			current_state = button.value()
			falling_edge = last_button_state == 1 and current_state == 0
			if falling_edge:
				now = time.ticks_ms()
				if time.ticks_diff(now, last_press_ms) > DEBOUNCE_MS:
					send_line(sock, "EVENT LOCK_BUTTON pressed")
					print("EVENT LOCK_BUTTON pressed")
					response = recv_line(sock)
					print("Event response:", response)
					last_press_ms = now

			last_button_state = current_state
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

