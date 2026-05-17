import os

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Message
from .services.channel_api import get_channels


@require_GET
def message_list(request):
    limit = int(request.GET.get("limit", 50))
    channel_ids_raw = request.GET.get("channel_id", "")
    channel_ids = [cid.strip() for cid in channel_ids_raw.split(",") if cid.strip()] if channel_ids_raw else []
    if channel_ids:
        messages = Message.get_by_channels(channel_ids, limit)
    else:
        messages = Message.get_recent(limit)
    return render(request, "monitor/message_list.html", {
        "messages": messages,
        "channel_ids": channel_ids,
    })


@require_GET
def channel_messages(request, channel_id):
    limit = int(request.GET.get("limit", 50))
    messages = Message.get_by_channel(channel_id, limit)
    return render(request, "monitor/channel_messages.html", {
        "messages": messages,
        "channel_id": channel_id,
    })


@require_GET
def message_search(request):
    keyword = request.GET.get("q", "")
    channel_ids_raw = request.GET.get("channel_id", "")
    channel_ids = [cid.strip() for cid in channel_ids_raw.split(",") if cid.strip()] if channel_ids_raw else []
    limit = int(request.GET.get("limit", 50))

    messages = Message.search(keyword, channel_ids if channel_ids else None, limit)
    return render(request, "monitor/search.html", {
        "messages": messages,
        "keyword": keyword,
        "channel_ids": channel_ids,
    })


@require_GET
def channel_list(request):
    server_url = os.getenv("MATTERMOST_URL")
    token = request.GET.get("token", "")
    channels = []
    error = None

    if server_url and token:
        try:
            channels = get_channels(server_url, token)
        except Exception as e:
            error = str(e)

    return render(request, "monitor/channel_list.html", {
        "channels": channels,
        "error": error,
        "server_url": server_url,
    })
