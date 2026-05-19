# Home Manager Project

Raspberry Pi Pico W 클라이언트가 방별 센서값과 장치 상태를 TCP로 전송하면, Python TCP 서버가 MySQL에 저장하고 Flask 대시보드가 데이터를 조회해서 보여주는 프로젝트입니다.

## 프로젝트 구성

```text
tcpip_project/
├─ main.py                # Flask 앱 진입점
├─ templates/             # Flask 화면 템플릿
├─ static/                # CSS 정적 파일
├─ requirements.txt       # Flask 앱 실행 의존성
├─ python_server/
│  ├─ tcp_server.py       # Pico TCP 수신 서버
│  ├─ db.py               # TCP 서버용 DB 헬퍼
│  └─ config.py           # TCP 서버용 설정
├─ picow_tcpip_client/    # Pico W 클라이언트 코드
├─ sql/                   # DB 생성, 초기 데이터, 조회 SQL
└─ home_manager_DB.txt    # 원본 DB 설계 참고 파일
```

Flask 웹앱은 학습 프로젝트처럼 루트의 `main.py`, `templates/`, `static/`을 기준으로 구성했습니다. `python_server` 폴더는 실제 TCP 수신 서버 실행에 필요한 파일만 남겨두었습니다.

## 실행 준비

프로젝트 루트의 `.env` 파일에 DB 접속 정보를 둡니다.

```text
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=Home_Manager
MYSQL_PORT=3306
FLASK_SECRET_KEY=change-me
```

필요하면 의존성을 설치합니다.

```powershell
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python -m pip install -r requirements.txt
```

## Flask 웹 서버 실행

```powershell
cd C:\Users\KOREA_HRD_1_3\Desktop\tcpip_project
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python main.py
```

브라우저에서 접속합니다.

```text
http://127.0.0.1:5000
```

## TCP 서버 실행

별도 터미널에서 실행합니다.

```powershell
cd C:\Users\KOREA_HRD_1_3\Desktop\tcpip_project\python_server
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python tcp_server.py
```

## 주요 화면

- `/` 로그인
- `/register_page` 회원가입
- `/dashboard` 전체 대시보드
- `/room/<room_id>` 방 상세 화면
- `/api/room/<room_id>/temperature-history` 방별 온도 그래프 데이터
