from django.core.management.base import BaseCommand
from apps.monitor.models import Message, Announcement
from apps.monitor.services.ai_summarizer import summarize_message


class Command(BaseCommand):
    help = "Summarize messages that do not have an Announcement yet"

    def handle(self, *args, **options):
        processed_ids = Announcement.objects.values_list("message_id", flat=True)
        messages = Message.objects.exclude(id__in=processed_ids).order_by("created_at")

        if not messages.exists():
            self.stdout.write(self.style.SUCCESS("No new messages to summarize."))
            return

        self.stdout.write(f"Processing {messages.count()} messages...")

        success_count = 0
        error_count = 0

        for msg in messages:
            try:
                if summarize_message(msg):
                    success_count += 1
                    self.stdout.write(f"[OK] {msg.text[:30]}...")
                else:
                    self.stdout.write("[OK] 공지가 아닙니다.")
            except Exception as e:
                error_count += 1
                self.stderr.write(f"[FAIL] {msg.text[:30]}... Error: {e}")

        self.stdout.write(self.style.SUCCESS(f"Done. Success: {success_count}, Errors: {error_count}"))
