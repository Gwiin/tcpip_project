# Home Manager Project

3대의 Raspberry Pi Pico 2 W가 각각 한 개의 방을 담당하고, 랜덤 더미 센서값과 액추에이터 상태를 TCP로 전송하면 Python 서버가 이를 MySQL에 저장하고 Flask 웹 대시보드에서 보여주는 프로젝트입니다.

## 전체 구성

```text
Pico 2 W 3대
   └─ TCP JSON 전송
        └─ Python TCP 서버
             └─ MySQL 저장
                  └─ Flask 웹 대시보드
```

| 장치 | 담당 방 | 전송 데이터 |
|---|---|---|
| Pico 1 | 거실 | 온도, 습도, 조도 / 조명, 에어컨, 커튼 |
| Pico 2 | 안방 | 온도, 습도 / 조명, 에어컨 |
| Pico 3 | 주방 | 온도, 움직임 / 조명, 선풍기 |

## 폴더 구조

```text
tcpip_project/
├─ picow_tcpip_client/   # Pico 2 W 클라이언트 코드
├─ python_server/        # TCP 서버, Flask 앱, 시뮬레이터
├─ sql/                  # DB 생성, 초기 데이터, 조회 쿼리
├─ home_manager_DB.txt   # 원본 DB 설계 참고 파일
└─ README.md
```

## 데이터 흐름

1. Pico가 5초마다 JSON 한 줄을 TCP로 전송
2. `python_server/tcp_server.py`가 데이터를 수신
3. MySQL의 `SENSOR_READING`, `ACTUATOR_STATE_LOG` 테이블에 저장
4. `python_server/app.py`가 SQL 조회 결과를 웹 화면으로 표시

예시 전송 데이터:

```json
{
  "device_id": "pico_living_room",
  "sensors": {
    "temperature": 24.3,
    "humidity": 48.2,
    "light": 410.5
  },
  "actuators": {
    "light": "ON",
    "air_conditioner": "COOLING",
    "curtain": "OPEN"
  }
}
```

## 대시보드 기능

- 최신 센서값
- 방별 평균 온도
- 현재 동작 중인 액추에이터
- 최근 센서 로그
- 최근 액추에이터 로그
- 방별 상세 페이지
- 방별 온도 그래프
- 사용자 현재 위치
- 예약 현황
- 현재 방 상태

## 1. MySQL 준비

MySQL 콘솔에서 `sql` 폴더로 이동한 뒤:

```sql
SOURCE setup.sql;
```

또는 직접 순서대로 실행:

```sql
SOURCE schema.sql;
SOURCE seed.sql;
```

`home_manager_DB.txt`는 처음 작성한 원본 설계 참고 파일이고, 실제 실행에는 `sql/` 폴더의 파일들을 사용합니다.

## 2. Python 서버 준비

```powershell
cd python_server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

환경 변수는 직접 입력하거나, 예시 파일을 참고해서 설정합니다.

```powershell
$env:HOME_MANAGER_DB_USER='root'
$env:HOME_MANAGER_DB_PORT='3306'
$env:HOME_MANAGER_DB_PASSWORD='1234'
$env:HOME_MANAGER_DB_NAME='Home_Manager'
```

또는:

```powershell
Get-Content .\set_env.example.ps1
```

를 참고해서 본인 비밀번호에 맞게 설정하면 됩니다.

## 3. DB 연결 확인

```powershell
cd python_server
python check_db.py
```

정상이라면 대략 아래처럼 나옵니다.

```text
[OK] MySQL 연결 성공
[OK] ROOM 테이블 데이터 수: 5
```

## 4. 서버 실행

터미널 1:

```powershell
cd python_server
python tcp_server.py
```

터미널 2:

```powershell
cd python_server
python app.py
```

웹 브라우저에서 아래 주소로 접속:

```text
http://127.0.0.1:5000
```

## 5. Pico 없이 먼저 테스트하기

Pico를 아직 굽지 않았더라도 PC에서 3대의 Pico처럼 더미 데이터를 보낼 수 있습니다.

터미널 3:

```powershell
cd python_server
python simulate_clients.py
```

이 상태에서 대시보드를 새로고침하면 값이 계속 추가되는 것을 확인할 수 있습니다.

## 6. 실제 Pico 사용 전 수정할 값

`picow_tcpip_client/CMakeLists.txt`

- `TEST_TCP_SERVER_IP`
- `WIFI_SSID`
- `WIFI_PASSWORD`

각 보드용 빌드 타깃:

- `pico_living_room_client`
- `pico_bedroom_client`
- `pico_kitchen_client`

## 발표할 때 설명하기 좋은 핵심

- **DB 설계**: 센서와 액추에이터를 종류별 테이블로 분리하고, 측정값과 상태 변화는 로그 테이블에 계속 쌓이도록 구성
- **서버 역할 분리**: TCP 서버는 수집과 저장, Flask 서버는 조회와 화면 표시 담당
- **확장성**: 실제 센서를 붙여도 현재 구조를 거의 그대로 유지할 수 있음
- **학습 포인트**: TCP 통신, Python 서버, MySQL, Flask, HTML/CSS를 한 프로젝트 안에서 연결
