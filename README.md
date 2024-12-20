# AutoNut - for bilibili Notification
AutoNut은 bilibili 새로운 게시물 알림 기능을 포함한 Discord 봇입니다. 사용자가 지정한 bilibili 계정의 활동을 모니터링하며 최신 동영상, 게시물 등의 업데이트 정보를 Discord 채널에 실시간으로 전송합니다.

## 봇 초대하기
**[서버에 초대하기](https://discord.com/oauth2/authorize?client_id=1305039063081816074&permissions=415001701376&integration_type=0&scope=bot+applications.commands)**

## 주요 기능
### ✅ bilibili 계정 등록 및 관리
- 사용자가 알림을 받기 원하는 bilibili UID를 Discord 채널에 등록할 수 있습니다.
- 등록된 계정의 콘텐츠를 실시간으로 모니터링하여 새로운 콘텐츠 알림을 제공합니다.
- 등록된 계정 정보를 쉽게 수정하거나 삭제할 수 있습니다.
  
### 🔔 알림 관리
- 새로운 콘텐츠(동영상, 게시물 등)가 업로드되면 알림 메시지를 전송합니다.
- 멘션 설정: 특정 역할(또는 @everyone)을 지정하여 알림 메시지를 전송합니다.
- 번역 설정: 콘텐츠 내용을 DeepL 번역기를 통해 번역하여 알림 메시지를 전송합니다.
  
### 🚀 사전예약 게임 순위
- bilibili 사전예약 게임 순위를 페이지 형식으로 출력합니다.

### 🌐 메시지 자동 번역
- 중국어 메시지를 자동으로 감지해 번역합니다.
  
### 📌 간단한 설정
- 모든 설정은 사용자가 쉽게 접근하고 수정할 수 있도록 구성되었습니다.
- 관리자 권한이 있는 사용자만이 Discord 채널에서 알림을 활성화 및 관리할 수 있습니다.

## 명령어
- `/알림설정` - 현재 채널의 bilibili 알림 설정을 관리합니다.
  - 계정 등록/수정 - 알림을 받기 원하는 bilibili UID를 등록하여 새 콘텐츠 알림을 받을 수 있습니다.
  - 멘션 설정 - 알림 메시지에 포함될 역할을 선택하거나 비활성화할 수 있습니다.
  - 번역 설정 - 콘텐츠 내용 번역 여부를 선택할 수 있습니다.
  
- `/사전예약순위` - bilibili 사전예약 게임 순위를 확인합니다.
  
- `/카운트다운` - 스트리노바 출시일 카운트다운 명령어.

- `/자동번역설정` - 현재 채널의 자동번역 기능을 관리합니다.

## 패키지 ##
```
pip install discord.py aiofiles aiohttp python-dotenv deepl
```

## 라이선스
[MIT license](https://github.com/MayNut02/AutoNut/blob/main/LICENSE)
