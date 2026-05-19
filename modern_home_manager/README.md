# Home Manager Modern Flask Website

새 웹사이트 전용 Flask 앱입니다. 기존 `python_server/` Flask 앱은 수정하지 않고, 이 폴더 안에서 A안 대시보드 구조와 빠른 방 정보 이미지 카드를 유지한 별도 웹사이트를 실행합니다.

## 실행

필요 패키지를 설치합니다.

```bash
python3 -m pip install -r modern_home_manager/requirements.txt
```

Flask 앱을 실행합니다.

```bash
python3 modern_home_manager/app.py
```

브라우저 주소:

```text
http://127.0.0.1:5173
```

## 구성

- `app.py`: 대시보드 화면과 JSON API를 제공하는 별도 Flask 앱
- `templates/dashboard.html`: A안 구조의 대시보드 템플릿
- `static/styles.css`: A안 레이아웃에 Apple Liquid Glass 박스 표면 적용
- `static/script.js`: Flask API fetch, 방 선택, 액추에이터 토글, 데이터 렌더링
- `static/images/`: 빠른 방 정보 카드용 로컬 실사풍 PNG 이미지

## 사용자 위치

브라우저는 보안 정책상 웹사이트에 WiFi SSID/BSSID를 직접 제공하지 않습니다. 이 앱의 `내 위치 확인` 버튼은 브라우저 위치 권한을 요청하고, 허용되면 GPS/WiFi/기지국 기반 좌표와 정확도를 `/api/location`에 저장합니다.

방 단위 위치 판단이 필요하면 공유기/AP 컨트롤러, 휴대폰 앱, BLE 비콘, 또는 여러 AP의 RSSI 데이터를 별도로 수집해서 좌표를 방 이름으로 매핑해야 합니다.
