from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("username", "channel_id", "text", "created_at")
    list_filter = ("channel_id", "created_at")
    search_fields = ("username", "text")
    readonly_fields = ("message_id", "channel_id", "user_id", "created_at", "raw")
