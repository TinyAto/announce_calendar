import json
import logging
import ssl
import threading
import time
from urllib.parse import urlencode, urlparse

import websocket

logger = logging.getLogger(__name__)


class MattermostWebSocket:
    def __init__(self, server_url, token, channel_ids=None, on_message=None, auth_on_open=False):
        self.server_url = server_url.rstrip("/")
        self.token = token
        self.channel_ids = set(channel_ids) if channel_ids else None
        self.on_message_callback = on_message
        self.auth_on_open = auth_on_open
        self.ws = None
        self.seq = 1
        self.running = False
        self.thread = None

    def _build_ws_url(self):
        parsed = urlparse(self.server_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        query = urlencode({"token": self.token})
        return f"{scheme}://{parsed.netloc}/api/v4/websocket?{query}"

    def _on_open(self, ws):
        logger.info("WebSocket connected")
        if self.auth_on_open:
            self._send_auth()
        else:
            logger.info("Authentication challenge skipped because token is included in WebSocket URL")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            event = data.get("event")
            if event == "hello":
                logger.info("Hello received from server")
                self._subscribe_to_events()
            elif event == "posted":
                self._handle_posted(data)
        except Exception as e:
            logger.error("Error processing message: %s", e)

    def _on_error(self, ws, error):
        logger.error(
            "WebSocket error: type=%s, status_code=%s, error=%s",
            type(error).__name__,
            getattr(error, "status_code", None),
            error,
            exc_info=True,
        )

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(
            "WebSocket closed: status_code=%s, message=%s",
            close_status_code,
            close_msg,
        )
        self.running = False

    def _send_auth(self):
        auth_msg = {
            "action": "authentication_challenge",
            "params": {"token": self.token},
            "seq": self._next_seq(),
        }
        self.ws.send(json.dumps(auth_msg))
        logger.info("Authentication challenge sent")

    def _subscribe_to_events(self):
        if self.channel_ids:
            sub_msg = {
                "action": "user_added",
                "seq": self._next_seq(),
            }
            self.ws.send(json.dumps(sub_msg))
        logger.info("Subscribed to events (filtering %d channels)", len(self.channel_ids) if self.channel_ids else 0)

    def _handle_posted(self, data):
        post_data = data.get("data", {})
        post = json.loads(post_data.get("post", "{}")) if isinstance(post_data.get("post"), str) else post_data.get("post", {})

        msg_channel_id = post.get("channel_id")
        if self.channel_ids and msg_channel_id not in self.channel_ids:
            return
        if post.get("type", "").startswith("system_"):
            return
        text = post.get("message", "")
        if not text:
            return

        message_data = {
            "message_id": post.get("id"),
            "channel_id": msg_channel_id,
            "user_id": post.get("user_id"),
            "username": post_data.get("sender_name") or post.get("user_id", "unknown"),
            "text": text,
            "created_at": post.get("create_at"),
            "raw": data,
        }

        if self.on_message_callback:
            try:
                self.on_message_callback(message_data)
            except Exception as e:
                logger.error("Error in on_message_callback: %s", e)

    def _next_seq(self):
        seq = self.seq
        self.seq += 1
        return seq

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        ws_url = self._build_ws_url()
        logger.info("Connecting to %s", ws_url)

        self.ws = websocket.WebSocketApp(
            ws_url,
            header={"Authorization": f"Bearer {self.token}"},
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self.ws.run_forever(
            sslopt={"cert_reqs": ssl.CERT_NONE},
            ping_interval=30,
            ping_timeout=10,
        )

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join(timeout=5)
