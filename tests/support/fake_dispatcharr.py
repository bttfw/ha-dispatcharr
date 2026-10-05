"""Disposable, synthetic HTTP API for full HA/browser tests. Never opens IPTV.

Run inside an isolated HA test container, bound to loopback only.
The /_test routes belong only to this fixture, not the integration.
"""

import base64
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UUID = "11111111-2222-4333-8444-555555555555"
STATE = {"mode": "active", "count": 2, "calls": [], "clients": ["client_0", "client_1"]}
KEY = "synthetic-test-key"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, value, status=200, content_type="application/json"):
        body = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.handle_api("OPTIONS")

    def do_POST(self):
        self.handle_api("POST")

    def do_GET(self):
        self.handle_api("GET")

    def handle_api(self, method):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        if path == "/_test/state":
            if method == "POST":
                STATE.update(body)
                if "count" in body:
                    STATE["clients"] = [f"client_{i}" for i in range(body["count"])]
                STATE["calls"] = []
            return self.reply(STATE)
        STATE["calls"].append([method, path, body])
        if self.headers.get("X-API-Key") != KEY or STATE["mode"] == "auth":
            return self.reply({}, 401)
        if STATE["mode"] == "outage":
            return self.reply({}, 503)
        if path == "/api/accounts/users/me/":
            return self.reply({"id": 42, "user_level": 10, "api_key": KEY})
        if path == "/api/core/version/":
            return self.reply({"version": "0.31.0"})
        if path.startswith("/proxy/ts/status"):
            row = {
                "channel_id": UUID,
                "state": "active",
                "channel_name": "Example TV",
                "client_count": len(STATE["clients"]),
                "m3u_profile_id": 17,
                "stream_profile": "ffmpeg",
                "clients": [
                    {
                        "client_id": c,
                        "user_id": 42 + int(c.removeprefix("client_")),
                        "user_agent": "Example Player",
                        "ip_address": f"192.0.2.{int(c.removeprefix('client_')) + 1}",
                        "connected_at": time.time() - 1234,
                        "output_profile_id": 7,
                    }
                    for i, c in enumerate(STATE["clients"])
                ],
            }
            if STATE["mode"] != "missing":
                row.update(
                    {
                        "resolution": "1920x1080",
                        "source_fps": 50,
                        "video_codec": "h264",
                        "audio_codec": "aac",
                        "avg_bitrate_kbps": 6500,
                    }
                )
            if STATE["mode"] == "empty" or not STATE["clients"]:
                return (
                    self.reply({"channels": [], "count": 0})
                    if path == "/proxy/ts/status"
                    else self.reply({}, 404)
                )
            if path == "/proxy/ts/status":
                row["clients"] = row["clients"][:10]
                return self.reply({"channels": [row], "count": 1})
            return self.reply(row)
        if path.startswith("/proxy/ts/stop"):
            if method == "OPTIONS":
                return self.reply({"name": "Stop"})
            if "/stop_client/" in path:
                STATE["clients"] = [c for c in STATE["clients"] if c != body.get("client_id")]
            else:
                STATE["clients"] = []
            return self.reply({"message": "processed"})
        if path == "/api/accounts/users/":
            return self.reply(
                [{"id": 42, "username": "Alex", "api_key": KEY}, {"id": 43, "username": "Sam"}]
            )
        if path == "/api/core/outputprofiles/":
            return self.reply([{"id": 7, "name": "Original quality"}])
        if path == "/api/m3u/accounts/":
            return self.reply(
                [
                    {
                        "id": 2,
                        "name": "Example provider",
                        "profiles": [{"id": 17, "name": "Standard"}],
                    }
                ]
            )
        if path == "/api/channels/channels/by-uuids/":
            return self.reply(
                [
                    {
                        "id": 92,
                        "uuid": UUID,
                        "name": "Example TV",
                        "logo_id": 3 if STATE["mode"] != "missing" else None,
                    }
                ]
                if UUID in body.get("uuids", [])
                else []
            )
        if path == "/api/epg/current-programs/":
            return self.reply(
                [
                    {
                        "channel_uuid": UUID,
                        "title": "Natur entdecken",
                        "start_time": time.time() - 900,
                        "end_time": time.time() + 1800,
                    }
                ]
                if UUID in body.get("channel_uuids", []) and STATE["mode"] != "missing"
                else []
            )
        if path == "/api/channels/logos/3/cache/":
            return self.reply(
                base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="
                ),
                content_type="image/png",
            )
        self.reply({}, 404)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8919), Handler).serve_forever()
