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

    prompt = prompt = f"""
{message.text}
---
너는 아래 메시지가 "처리 대상 공지"인지 먼저 판단해야 한다.

[처리 대상이 아닌 경우]
아래 중 하나라도 해당하면 다른 설명 없이 반드시 빈 JSON만 반환해라.
반드시 아래 형식 그대로 반환:
{{}}

처리 대상이 아닌 경우:
1. 입퇴장 알림
   - 예: "OOO님이 채널에 참가했습니다", "OOO님이 나갔습니다"
2. 잡담, 인사, 단순 대화
3. 이전 공지의 리마인드, 재공지, 다시 알림
   - 예: "리마인드합니다", "다시 공지합니다", "위 공지 확인해주세요"
4. 날짜나 시간, 일정 정보가 전혀 없는 단순 안내
5. 시작일, 마감일, 행사일, 제출기한 등 일정으로 등록할 만한 정보가 없는 메시지

[처리 대상인 경우]
메시지가 채용공고, 새로운 일정, 행사, 제출, 신청, 마감, 시작일, 데드라인 등을 알리는 공지일 때만 JSON을 반환해라.

반환 형식은 반드시 아래 필드만 포함한 JSON이어야 한다.
다른 설명, 참고 사항, 문장은 절대 추가하지 마라.

필드:
- title: 일정 제목
- start_dt: 시작 날짜와 시간
- deadline_dt: 마감 날짜와 시간
- summary: 공지 요약

규칙:
1. 날짜 형식은 sqlite3 DATETIME 형식인 "YYYY-MM-DD HH:MM:SS"로 작성해라.
2. 시작 시간이 없으면 start_dt는 빈 문자열로 작성해라.
3. 마감 시간이 없으면 deadline_dt는 빈 문자열로 작성해라.
4. summary는 150자 내외로 간략히 작성해라.
5. JSON 외의 내용은 절대 말하지 마라.

예시:
- "OOO님이 채널에 참가했습니다" -> {{}}
- "오늘 회의 잊지 마세요. 리마인드입니다." -> {{}}
- "다들 점심 드셨나요?" -> {{}}
- "과제 제출은 5월 20일 23:59까지입니다." -> {{"title":"과제 제출","start_dt":"","deadline_dt":"YYYY-05-20 23:59:00","summary":"과제 제출 마감은 5월 20일 23시 59분까지입니다."}}
"""

    prompt += """

추가 규칙:
- 처리 대상 공지라면 JSON에 반드시 category 필드를 포함해라.
- category는 다음 다섯 값 중 정확히 하나만 사용해라: 공지사항, 과목평가, 취업지원, 행사/이벤트, 프로젝트
- 분류가 애매하면 category는 공지사항으로 작성해라.
- 반환 JSON 예시:
{"title":"과제 제출","category":"공지사항","start_dt":"","deadline_dt":"YYYY-05-20 23:59:00","summary":"과제 제출 마감은 5월 20일 23시 59분까지입니다."}
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
        timeout=180
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()

    data = response.json()

    content = data["choices"][0]["message"]["content"]

    result = parse_ai_response(content)

    if result == {}:
        return False

    category = str(result.get("category") or Announcement.Category.NOTICE).strip()
    if category not in Announcement.Category.values:
        category = Announcement.Category.NOTICE

    start_dt = result.get("start_dt")

    if not start_dt:
        start_dt = message.created_at
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
        category=category,
        start_dt=start_dt,
        deadline_dt=deadline_dt,
        summary=result.get("summary", ""),
    )

    return True
