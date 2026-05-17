from django.contrib import admin
from .models import Message, Announcement


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("username", "channel_id", "text", "created_at")
    list_filter = ("channel_id", "created_at")
    search_fields = ("username", "text")
    readonly_fields = ("message_id", "channel_id", "user_id", "created_at", "raw")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "start_dt", "deadline_dt", "message")
    list_filter = ("category", "start_dt", "deadline_dt")
    search_fields = ("title", "summary")
    readonly_fields = ("message", "created_at")
