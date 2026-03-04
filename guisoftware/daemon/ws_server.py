import asyncio
import json
import threading
import websockets


class DashboardWebSocketServer:
    """Async WebSocket server bridging the React dashboard to the daemon."""

    def __init__(self, port, get_state, handle_command, status_callback):
        self.port = port
        self.get_state = get_state
        self.handle_command = handle_command
        self.status_callback = status_callback
        self._clients = set()
        self._loop = None
        self._thread = None

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        async with websockets.serve(self._handler, "0.0.0.0", self.port):
            self.status_callback(f"WebSocket: listening on 0.0.0.0:{self.port}")
            await asyncio.Future()  # run forever

    async def _handler(self, websocket):
        self._clients.add(websocket)
        self.status_callback(
            f"WebSocket: client connected ({len(self._clients)} total)"
        )
        try:
            state = self.get_state()
            await websocket.send(json.dumps({"type": "state", **state}))

            async for raw_message in websocket:
                try:
                    msg = json.loads(raw_message)
                    response = self.handle_command(msg)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(
                        json.dumps({"type": "error", "message": "Invalid JSON"})
                    )
                except Exception as e:
                    await websocket.send(
                        json.dumps({"type": "error", "message": str(e)})
                    )
        except websockets.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            self.status_callback(
                f"WebSocket: client disconnected ({len(self._clients)} total)"
            )

    def broadcast_update(self, feature_id, active):
        """Push a feature change to all WebSocket clients (thread-safe)."""
        if self._loop is None:
            return
        msg = json.dumps(
            {"type": "feature_update", "featureId": feature_id, "active": active}
        )
        asyncio.run_coroutine_threadsafe(self._broadcast(msg), self._loop)

    async def _broadcast(self, message):
        if self._clients:
            await asyncio.gather(
                *[client.send(message) for client in self._clients],
                return_exceptions=True,
            )

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
