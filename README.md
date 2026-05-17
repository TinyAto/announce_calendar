# gjh_s1

SSAFY Mattermost 공지 채널 수집 → AI 요약 → 캘린더 표시 웹서비스

---

## 구성

| 폴더 | 설명 | 포트 |
|---|---|---|
| `project/` | Django 백엔드 (메시지 수집, AI 요약, API) | 8000 |
| `calendar-ui/` | Next.js 프론트엔드 (캘린더 UI) | 3000 |

---

## 백엔드 실행

```bash
cd project

# 1. 패키지 설치
pip install -r requirements.txt

# 2. .env 작성 (아래 항목 참고)
# MATTERMOST_URL, MATTERMOST_TOKEN, TARGET_CHANNEL_ID 등

# 3. DB 마이그레이션
python manage.py migrate

# 4. 웹서버 실행
python manage.py runserver

# 5. 메시지 수집 (별도 터미널)
python manage.py runlistener --no-chrome
```

---

## 프론트엔드 실행

```bash
cd calendar-ui

# 1. 패키지 설치
pnpm install

# 2. 개발 서버 실행
pnpm dev
```

---

## .env 설정 항목

| 키 | 설명 | 예시 |
|---|---|---|
| `MATTERMOST_URL` | Mattermost 서버 주소 | `https://meeting.ssafy.com` |
| `MATTERMOST_TOKEN` | API 토큰 | `token값` |
| `TARGET_CHANNEL_ID` | 수집할 채널 ID (쉼표 구분) | `abc123,def456` |
| `OPENAI_API_URL` | AI 요약 API 주소 | `your api url` |
| `OPENAI_API_KEY` | AI API 키 | `key값` |
| `OPENAI_MODEL` | 사용할 모델명 | `default` |
| `RECONNECT_DELAY` | 재연결 대기 시간(초) | `5` |
| `MAX_RECONNECT_ATTEMPTS` | 최대 재연결 횟수 (0=무제한) | `0` |

---

## 커맨드 목록

| 커맨드 | 설명 |
|---|---|
| `python manage.py runlistener --no-chrome` | 실시간 메시지 수신 (.env 토큰 사용) |
| `python manage.py fetch_history` | 과거 메시지 일괄 수집 |
| `python manage.py summarize` | 미처리 메시지 일괄 AI 요약 |
| `python manage.py runserver` | 웹서버 실행 |

---

## API 엔드포인트

| URL | 설명 |
|---|---|
| `GET /api/announcements/` | 캘린더 공지 목록 (JSON) |
| `GET /` | 메시지 목록 |
| `GET /channel/<id>/` | 채널별 메시지 |
| `GET /search/?q=키워드` | 키워드 검색 |
| `GET /channels/` | 채널 목록 조회 |
