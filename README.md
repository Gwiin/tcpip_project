# Home Manager Project

Raspberry Pi Pico 2 W 3대가 각각 방을 담당하고, 센서값과 액추에이터 상태를 TCP로 전송하면 Python 서버가 MySQL에 저장하고 Flask 웹 대시보드에서 보여주는 프로젝트입니다.

## 전체 구성

```text
Pico 2 W 3대
  -> TCP JSON 전송
      -> Python TCP 서버
          -> MySQL 저장
              -> Flask 웹 대시보드
```

| 장치 | 담당 방 | 전송 데이터 |
|---|---|---|
| Pico 1 | 거실 | 온도, 습도, 조도 / 조명, 에어컨, 커튼 |
| Pico 2 | 침실 | 온도, 습도 / 조명, 에어컨 |
| Pico 3 | 주방 | 온도, 움직임 / 조명, 선풍기 |

## 폴더 구조

```text
tcpip_project/
├─ picow_tcpip_client/   # Pico 2 W 클라이언트 코드
├─ python_server/        # TCP 서버, Flask 앱, 대시보드
├─ sql/                  # DB 생성, 초기 데이터, 조회 쿼리
├─ home_manager_DB.txt   # 원본 DB 설계 참고 파일
└─ README.md
```

## 데이터 흐름

1. Pico가 5초마다 JSON 한 줄을 TCP로 전송합니다.
2. `python_server/tcp_server.py`가 데이터를 수신합니다.
3. MySQL의 `SENSOR_READING`, `ACTUATOR_STATE_LOG` 테이블에 저장합니다.
4. `python_server/app.py`가 SQL 조회 결과를 웹 화면으로 표시합니다.

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

MySQL 콘솔에서 `sql` 폴더로 이동한 뒤 실행합니다.

```sql
SOURCE setup.sql;
```

또는 파일을 직접 순서대로 실행합니다.

```sql
SOURCE schema.sql;
SOURCE seed.sql;
```

`home_manager_DB.txt`는 처음 작성한 원본 설계 참고 파일이고, 실제 실행에는 `sql/` 폴더의 SQL 파일을 사용합니다.

## 2. Python 서버 준비

이 프로젝트는 Miniconda 환경 `flask1`에서 동작하도록 구성했습니다.

현재 생성된 환경:

```text
C:\Users\KOREA_HRD_1_3\miniconda3\envs\flask1
```

현재 PC에서는 PowerShell 실행 정책 때문에 `conda activate`가 막힐 수 있습니다. 그래서 아래처럼 `conda run -n flask1` 방식으로 실행합니다.

```powershell
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python --version
```

환경을 다시 만들어야 할 때는 아래 명령을 사용합니다.

```powershell
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat create -n flask1 python=3.12 pip -y
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python -m pip install -r python_server\requirements.txt
```

설치된 주요 버전:

```text
Python 3.12.13
Flask 3.1.1
mysql-connector-python 9.3.0
```

DB와 Flask 설정은 프로젝트 루트의 `.env` 파일에 작성합니다. Python 실행 파일에서 `load_dotenv()`가 이 파일을 읽습니다.

```text
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=Home_Manager
MYSQL_PORT=3306
FLASK_SECRET_KEY=change-me
```

## 3. DB 연결 확인

```powershell
cd python_server
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python check_db.py
```

정상이라면 아래처럼 출력됩니다.

```text
[OK] MySQL 연결 성공
[OK] ROOM 테이블 데이터 수: 5
```

## 4. 서버 실행

터미널 1에서 TCP 서버를 실행합니다.

```powershell
cd python_server
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python tcp_server.py
```

터미널 2에서 Flask 웹 서버를 실행합니다.

```powershell
cd python_server
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python app.py
```

브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:5000
```

## 5. Pico 없이 먼저 테스트하기

Pico를 아직 연결하지 않았을 때는 PC에서 3대의 Pico처럼 더미 데이터를 보낼 수 있습니다.

터미널 3에서 실행합니다.

```powershell
cd python_server
C:\Users\KOREA_HRD_1_3\miniconda3\condabin\conda.bat run -n flask1 python simulate_clients.py
```

이 상태에서 대시보드를 새로고침하면 값이 계속 추가되는 것을 확인할 수 있습니다.

## 6. 실제 Pico 사용 시 수정할 값

`picow_tcpip_client/CMakeLists.txt`에서 아래 값을 보드와 네트워크 환경에 맞게 수정합니다.

- `TEST_TCP_SERVER_IP`
- `WIFI_SSID`
- `WIFI_PASSWORD`

빌드 대상:

- `pico_living_room_client`
- `pico_bedroom_client`
- `pico_kitchen_client`

## 발표 때 설명하기 좋은 포인트

- **DB 설계**: 센서와 액추에이터를 종류별 테이블로 분리하고, 측정값과 상태 변화는 로그 테이블에 계속 쌓이도록 구성했습니다.
- **서버 역할 분리**: TCP 서버는 수집과 저장, Flask 서버는 조회와 화면 표시를 담당합니다.
- **확장성**: 실제 센서를 붙여도 현재 구조를 거의 그대로 사용할 수 있습니다.
- **학습 포인트**: TCP 통신, Python 서버, MySQL, Flask, HTML/CSS를 하나의 프로젝트 안에서 연결했습니다.
