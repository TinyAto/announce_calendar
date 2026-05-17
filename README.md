실행 방법
1. 의존성 설치
cd project
pip install -r requirements.txt
2. 환경변수 설정 (.env 수정)
MATTERMOST_URL=https://your-mattermost-domain.com
TARGET_CHANNEL_ID=your-channel-id
CHROME_DEBUG_PORT=9222
RECONNECT_DELAY=5
MAX_RECONNECT_ATTEMPTS=0
3. Chrome Remote Debugging 모드로 실행
chrome.exe --remote-debugging-port=9222
4. Chrome에서 Mattermost 로그인
5. DB 마이그레이션
python manage.py makemigrations
python manage.py migrate
6. Listener 실행
python manage.py runlistener
python manage.py runlistener --channel-name general
python manage.py runlistener --channel-id abc123
7. Django 서버 실행
python manage.py runserver
Dashboard URL
URL
설명
/
최근 메시지 목록
/channel/<channel_id>/
채널별 메시지
/search/?q=keyword
키워드 검색
/channels/
채널 목록 조회
WebSocket 동작 흐름
1.
ChromeAuthExtractor가 Chrome 디버깅 포트에 연결
2.
localStorage.MMTOKEN 또는 쿠키에서 토큰 추출
3.
MattermostWebSocket이 /api/v4/websocket에 연결
4.
authentication_challenge로 인증
5.
posted 이벤트 수신 → channel_id 필터링 → Message 모델에 저장
6.
ReconnectManager가 연결 끊김 시 자동 재연결


runlistener 사용법
# .env에서 여러 채널 읽기
python manage.py runlistener

# CLI에서 여러 채널 지정
python manage.py runlistener --channel-id id1 --channel-id id2 --channel-id id3

# 채널 이름으로 자동 조회 (여러 개 가능)
python manage.py runlistener --channel-name general --channel-name random