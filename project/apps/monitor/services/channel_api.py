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
