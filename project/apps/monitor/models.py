import uuid

from django.db import models


class Message(models.Model):
    message_id = models.CharField(max_length=64, unique=True, db_index=True)
    channel_id = models.CharField(max_length=64, db_index=True)
    username = models.CharField(max_length=255)
    user_id = models.CharField(max_length=64, db_index=True)
    text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(db_index=True)
    raw = models.JSONField(default=dict)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"[{self.username}] {self.text[:50]}"

    @classmethod
    def get_recent(cls, limit=50):
        return cls.objects.all()[:limit]

    @classmethod
    def get_by_channels(cls, channel_ids, limit=50):
        return cls.objects.filter(channel_id__in=channel_ids).order_by("-created_at")[:limit]

    @classmethod
    def get_by_channel(cls, channel_id, limit=50):
        return cls.objects.filter(channel_id=channel_id).order_by("-created_at")[:limit]

    @classmethod
    def search(cls, keyword, channel_ids=None, limit=50):
        qs = cls.objects.filter(text__icontains=keyword).order_by("-created_at")
        if channel_ids:
            qs = qs.filter(channel_id__in=channel_ids)
        return qs[:limit]
