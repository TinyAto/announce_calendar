import os
import json
import re
import requests
from datetime import datetime
from django.utils import timezone
from apps.monitor.models import Message, Announcement


def parse_ai_response(text):
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)

    if match:
        text = match.group(1)

    return json.loads(text)


def summarize_message(message: Message):
    api_url = os.getenv("OPENAI_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
    api_key = os.getenv("OPENAI_API_KEY", "")
    api_key = 'Bearer ' + api_key
    model = os.getenv("OPENAI_MODEL", "default")
    if not api_key: raise ValueError("OPENAI_API_KEY not set in .env")

    prompt = f"""
    
{message.text}
---
이 공지사항을 보고 날짜와 시간을 추출하고, 일정에 대한 공지인지 판단하고, 시작 혹은 데드라인이 있는 일정일 경우, 공지 내용을 간략하게 요약해줘.
만약 이전 공지 사항의 리마인드 성격의 공지이거나, 입퇴장 알림, 잡담인 경우, 빈 json파일을 보내줘.
날짜 정보가 없을 경우, 시간 부분은 빈 칸으로 보내줘.
(title, start_dt, deadline_dt, summary,)의 칼럼명을 다른 내용 없이 json 파일 형식으로 답변할 수 있도록.
요약 정보는 150자 내외로 요약해서 한개의 칼럼에 대답해.
날짜는 sqlite3의 DATETIME형식에 맞출 수 있도록.
참고 사항은 절대 말하지 않기.
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key,
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=30
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()

    data = response.json()

    content = data["choices"][0]["message"]["content"]

    result = parse_ai_response(content)

    if result == {}:
        return False

    start_dt = result.get("start_dt")

    if not start_dt:
        start_dt = timezone.now()
    else:
        start_dt = datetime.strptime(
            start_dt,
            "%Y-%m-%d %H:%M:%S"
        )

    deadline_dt = result.get("deadline_dt")

    if deadline_dt:
        deadline_dt = datetime.strptime(
            deadline_dt,
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        deadline_dt = None
    print(f'---------------------------------\n{{message}}---------------------------------\n')
    Announcement.objects.create(
        message=message,
        title=result.get("title", "제목 없음"),
        start_dt=start_dt,
        deadline_dt=deadline_dt,
        summary=result.get("summary", ""),
    )

    return True