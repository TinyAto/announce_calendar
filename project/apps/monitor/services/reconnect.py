import logging
import time

from .mattermost_ws import MattermostWebSocket

logger = logging.getLogger(__name__)


class ReconnectManager:
    def __init__(self, server_url, token, channel_ids=None, on_message=None, reconnect_delay=5, max_attempts=0):
        self.server_url = server_url
        self.token = token
        self.channel_ids = channel_ids
        self.on_message = on_message
        self.reconnect_delay = reconnect_delay
        self.max_attempts = max_attempts
        self.ws = None
        self._stop = False

    def run(self):
        attempt = 0
        while not self._stop:
            if self.max_attempts > 0 and attempt >= self.max_attempts:
                logger.info("Max reconnect attempts (%d) reached", self.max_attempts)
                break

            if attempt > 0:
                logger.info("Reconnecting in %d seconds (attempt %d)...", self.reconnect_delay, attempt)
                time.sleep(self.reconnect_delay)

            try:
                self.ws = MattermostWebSocket(
                    server_url=self.server_url,
                    token=self.token,
                    channel_ids=self.channel_ids,
                    on_message=self.on_message,
                )
                self.ws.start()

                while self.ws.running and not self._stop:
                    time.sleep(1)

            except Exception as e:
                logger.error("Connection error: %s", e)

            attempt += 1

        logger.info("Reconnect loop ended")

    def stop(self):
        self._stop = True
        if self.ws:
            self.ws.stop()
