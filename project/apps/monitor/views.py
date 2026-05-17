import os

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Message, Announcement
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


@require_GET
def announcements_api(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    mattermost_url = os.getenv("MATTERMOST_URL", "").rstrip("/")
    category = ('공지사항', '취업지원', '과목평가', '행사/이벤트')

    announcements = Announcement.objects.all()
    if start and end:
        announcements = announcements.filter(
            start_dt__date__gte=start,
            start_dt__date__lte=end,
        ) | announcements.filter(
            deadline_dt__date__gte=start,
            deadline_dt__date__lte=end,
        )

    data = [
        {
            "id": announcement.id,
            "title": announcement.title,
            "startDateTime": announcement.start_dt.strftime("%Y-%m-%dT%H:%M:%S") if announcement.start_dt else None,
            "deadlineDateTime": announcement.deadline_dt.strftime("%Y-%m-%dT%H:%M:%S") if announcement.deadline_dt else None,
            "summary": announcement.summary,
            # 모델에 해당 필드 없음
            "originalUrl": f"{mattermost_url}/s15public/pl/{announcement.message.message_id}" if mattermost_url else "",
            "channelName": announcement.message.channel_id,
            "category": announcement.category if announcement.category in category else "공지사항",
            "createdAt": announcement.message.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        for announcement in announcements
    ]
    return JsonResponse(data, safe=False)
