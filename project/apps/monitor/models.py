import uuid

from django.db import models
from django.utils import timezone


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


class Announcement(models.Model):
    class Category(models.TextChoices):
        NOTICE = "공지사항", "공지사항"
        SUBJECT_EVALUATION = "과목평가", "과목평가"
        CAREER_SUPPORT = "취업지원", "취업지원"
        EVENT = "행사/이벤트", "행사/이벤트"
        PROJECT = "프로젝트", "프로젝트"

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.NOTICE,
    )
    start_dt = models.DateTimeField(null=True, blank=True)
    deadline_dt = models.DateTimeField(null=True, blank=True)
    summary = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_dt"]
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"

    def __str__(self):
        return self.title

    @classmethod
    def get_upcoming(cls, limit=20):
        now = timezone.now()
        return cls.objects.filter(
            models.Q(start_dt__gte=now) | models.Q(deadline_dt__gte=now),
            start_dt__isnull=False
        ).order_by("start_dt")[:limit]

    @classmethod
    def get_by_date(cls, date_obj):
        return cls.objects.filter(
            models.Q(start_dt__date=date_obj) | models.Q(deadline_dt__date=date_obj)
        ).order_by("start_dt")
