import os
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from ...models import Message
from ...services.channel_api import fetch_posts


class Command(BaseCommand):
    help = "Fetch historical messages from Mattermost channels"

    def handle(self, *args, **options):
        load_dotenv()

        server_url = os.getenv("MATTERMOST_URL", "")
        token = os.getenv("MATTERMOST_TOKEN", "")
        target_channel_ids = [
            channel_id.strip()
            for channel_id in os.getenv("TARGET_CHANNEL_ID", "").split(",")
            if channel_id.strip()
        ]

        if not server_url or not token or not target_channel_ids:
            self.stderr.write(
                "MATTERMOST_URL, MATTERMOST_TOKEN, TARGET_CHANNEL_ID 값을 확인하세요."
            )
            return

        for channel_id in target_channel_ids:
            saved_count = 0
            skipped_count = 0
            posts = fetch_posts(server_url, token, channel_id)

            for post in posts:
                text = post.get("message", "")
                if text == "":
                    skipped_count += 1
                    continue
                if post.get("type", "").startswith("system_"):
                    skipped_count += 1
                    continue

                props = post.get("props", {})
                username = (
                    props.get("override_username")
                    or props.get("from_webhook")
                    or post["user_id"]
                )
                created_at = datetime.fromtimestamp(
                    post["create_at"] / 1000,
                    tz=timezone.utc,
                )

                Message.objects.update_or_create(
                    message_id=post["id"],
                    defaults={
                        "channel_id": post["channel_id"],
                        "user_id": post["user_id"],
                        "username": username,
                        "text": text,
                        "created_at": created_at,
                        "raw": post,
                    },
                )
                saved_count += 1

            self.stdout.write(
                f"채널 {channel_id}: {saved_count}개 저장, "
                f"{skipped_count}개 스킵(빈 메시지/시스템 메시지)"
            )
