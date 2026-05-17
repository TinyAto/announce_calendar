import json
import logging
import os
import time
from datetime import datetime, timezone

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_channels(server_url, token):
    base = server_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(f"{base}/api/v4/users/me/teams", headers=headers, timeout=10)
    resp.raise_for_status()
    teams = resp.json()
    if not teams:
        raise ValueError("No teams found")
    team_id = teams[0]["id"]

    resp = requests.get(
        f"{base}/api/v4/users/me/channels",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    channels = resp.json()

    result = []
    for ch in channels:
        result.append({
            "id": ch["id"],
            "name": ch.get("name", ""),
            "display_name": ch.get("display_name", ""),
            "team_id": ch.get("team_id", ""),
            "type": ch.get("type", ""),
        })

    return result


def find_channel(server_url, token, channel_name):
    channels = get_channels(server_url, token)
    for ch in channels:
        if ch["name"] == channel_name or ch["display_name"] == channel_name:
            return ch
    return None


def fetch_posts(server_url, token, channel_id, page=0, per_page=60):
    base = server_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(
            f"{base}/api/v4/channels/{channel_id}/posts",
            headers=headers,
            params={"page": page, "per_page": per_page},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        order = data.get("order", [])
        posts = data.get("posts", {})

        return [
            posts[post_id]
            for post_id in reversed(order)
            if post_id in posts
        ]
    except Exception as exc:
        logger.error("Failed to fetch posts for channel %s: %s", channel_id, exc)
        return []
