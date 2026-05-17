from db import fetch_all


def main():
    rows = fetch_all("SELECT COUNT(*) AS room_count FROM ROOM")
    print("[OK] MySQL 연결 성공")
    print(f"[OK] ROOM 테이블 데이터 수: {rows[0]['room_count']}")


if __name__ == "__main__":
    main()
