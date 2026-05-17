import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.monitor.models import Message
from apps.monitor.services.chrome_auth import ChromeAuthExtractor
from apps.monitor.services.reconnect import ReconnectManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start Mattermost WebSocket message listener"

    def add_arguments(self, parser):
        parser.add_argument("--channel-id", type=str, action="append", help="Target channel ID (can be specified multiple times)")
        parser.add_argument("--channel-name", type=str, action="append", help="Channel name to auto-resolve (can be specified multiple times)")
        parser.add_argument("--no-chrome", action="store_true", help="Skip Chrome attachment, use token from env")

    def _parse_channel_ids(self, raw_value):
        if not raw_value:
            return []
        return [cid.strip() for cid in raw_value.replace(",", " ").split() if cid.strip()]

    def handle(self, *args, **options):
        from dotenv import load_dotenv
        load_dotenv()

        server_url = os.getenv("MATTERMOST_URL")
        if not server_url:
            self.stderr.write("MATTERMOST_URL not set in .env")
            return

        channel_ids = []
        cli_ids = options.get("channel_id") or []
        for cid in cli_ids:
            channel_ids.extend(self._parse_channel_ids(cid))

        env_ids = self._parse_channel_ids(os.getenv("TARGET_CHANNEL_ID", ""))
        if not channel_ids:
            channel_ids = env_ids

        channel_names = options.get("channel_name") or []

        token = None

        if not options.get("no_chrome"):
            debug_port = int(os.getenv("CHROME_DEBUG_PORT", 9222))
            extractor = ChromeAuthExtractor(server_url, debug_port)

            try:
                extractor.attach_to_chrome()
                self.stdout.write("Waiting for login...")
                extractor.ensure_logged_in()
                token = extractor.extract_token()
                if not token:
                    self.stderr.write("Failed to extract token")
                    return
                self.stdout.write(self.style.SUCCESS("Token extracted successfully"))
            except Exception as e:
                self.stderr.write(f"Chrome auth failed: {e}")
                return
        else:
            self.stderr.write("--no-chrome requires MATTERMOST_TOKEN in .env")
            return

        if channel_names:
            from apps.monitor.services.channel_api import find_channel
            resolved_ids = []
            for name in channel_names:
                ch = find_channel(server_url, token, name)
                if ch:
                    resolved_ids.append(ch["id"])
                    self.stdout.write(self.style.SUCCESS(f"Resolved channel: {ch['display_name']} ({ch['id']})"))
                else:
                    self.stderr.write(f"Channel '{name}' not found")
            channel_ids.extend(resolved_ids)

        channel_ids = list(dict.fromkeys(channel_ids))

        if channel_ids:
            self.stdout.write(self.style.SUCCESS(f"Listening to {len(channel_ids)} channel(s): {', '.join(channel_ids)}"))
        else:
            self.stdout.write(self.style.WARNING("No channel specified. Listening to all channels."))

        reconnect_delay = int(os.getenv("RECONNECT_DELAY", 5))
        max_attempts = int(os.getenv("MAX_RECONNECT_ATTEMPTS", 0))

        def on_message(msg_data):
            try:
                created_at_ts = msg_data.get("created_at")
                if created_at_ts:
                    created_at = datetime.fromtimestamp(created_at_ts / 1000, tz=timezone.utc)
                else:
                    created_at = datetime.now(tz=timezone.utc)

                Message.objects.update_or_create(
                    message_id=msg_data["message_id"],
                    defaults={
                        "channel_id": msg_data["channel_id"],
                        "username": msg_data["username"],
                        "user_id": msg_data["user_id"],
                        "text": msg_data["text"],
                        "created_at": created_at,
                        "raw": msg_data["raw"],
                    },
                )
                self.stdout.write(f"[{msg_data['username']}] {msg_data['text'][:80]}")
            except Exception as e:
                logger.error("Error saving message: %s", e)

        manager = ReconnectManager(
            server_url=server_url,
            token=token,
            channel_ids=channel_ids if channel_ids else None,
            on_message=on_message,
            reconnect_delay=reconnect_delay,
            max_attempts=max_attempts,
        )

        def shutdown(signum, frame):
            self.stdout.write("\nShutting down...")
            manager.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        self.stdout.write(self.style.SUCCESS("Starting listener..."))
        manager.run()
