USE Home_Manager;

-- 1. 방 기본 데이터
-- 프로젝트에서 사용하는 전체 방 목록을 미리 등록한다.
INSERT IGNORE INTO ROOM (room_id, room_name) VALUES
(1, '거실'),
(2, '안방'),
(3, '주방'),
(4, '공부방'),
(5, '화장실');

-- 2. 사용자 권한 종류
-- 사용자에게 부여할 수 있는 권한 레벨을 등록한다.
INSERT IGNORE INTO USER_ROLE (role_id, role_name) VALUES
(1, 'ADMIN'),
(2, 'MEMBER'),
(3, 'GUEST');

-- 3. 사용자 기본 데이터
-- 사용자와 권한의 관계를 예시로 보여주기 위한 초기 데이터다.
-- INSERT IGNORE INTO `USER` (user_id, role_id, pw, user_name) VALUES
-- (1, 1, 'father123', '아버지'),
-- (2, 2, 'mother123', '어머니'),
-- (3, 2, 'me123', '나'),
-- (4, 3, 'guest123', '손님');

-- 4. 센서 종류
-- 실제 센서 데이터가 어떤 단위를 가지는지 정의한다.
INSERT IGNORE INTO SENSOR_TYPE (sensor_type_id, type_name, unit) VALUES
(1, 'temperature', 'C'),
(2, 'humidity', '%'),
(3, 'motion', 'bool'),
(4, 'light', 'lux');

-- 5. 센서 배치
-- 각 방에 어떤 센서가 설치되어 있는지 정의한다.
INSERT IGNORE INTO SENSOR (sensor_id, room_id, sensor_type_id, sensor_name) VALUES
(1, 1, 1, '거실 온도 센서'),
(2, 1, 2, '거실 습도 센서'),
(3, 1, 4, '거실 조도 센서'),
(4, 2, 1, '안방 온도 센서'),
(5, 2, 2, '안방 습도 센서'),
(6, 3, 1, '주방 온도 센서'),
(7, 3, 3, '주방 움직임 센서'),
(8, 4, 1, '공부방 온도 센서'),
(9, 4, 3, '공부방 움직임 센서'),
(10, 5, 2, '화장실 습도 센서');

-- 6. 액추에이터 종류
-- 제어할 수 있는 장치의 종류를 정의한다.
INSERT IGNORE INTO ACTUATOR_TYPE (actuator_type_id, type_name) VALUES
(1, 'light'),
(2, 'air_conditioner'),
(3, 'fan'),
(4, 'door_lock'),
(5, 'curtain');

-- 7. 액추에이터 배치
-- 각 방에 어떤 제어 장치가 설치되어 있는지 정의한다.
INSERT IGNORE INTO ACTUATOR (actuator_id, room_id, actuator_type_id, actuator_name) VALUES
(1, 1, 1, '거실 조명'),
(2, 1, 2, '거실 에어컨'),
(3, 1, 5, '거실 커튼'),
(4, 2, 1, '안방 조명'),
(5, 2, 2, '안방 에어컨'),
(6, 3, 1, '주방 조명'),
(7, 3, 3, '주방 선풍기'),
(8, 4, 1, '공부방 조명'),
(9, 4, 2, '공부방 에어컨'),
(10, 5, 1, '화장실 조명'),
(11, 5, 3, '화장실 선풍기');

-- 8. 방 상태 종류
-- 방이 가질 수 있는 상태를 정의한다.
INSERT IGNORE INTO ROOM_STATUS_TYPE (status_id, status_name) VALUES
(1, 'EMPTY'),
(2, 'IN_USE'),
(3, 'CLEANING'),
(4, 'RESERVED');

-- 9. 사용자 현재 위치
-- 사용자 위치 조회 화면을 위한 초기 예시 데이터다.
INSERT IGNORE INTO USER_LOCATION (user_id, room_id) VALUES
(1, 1),
(2, 3),
(3, 4),
(4, NULL);

-- 10. 방 예약 예시 데이터
-- 예약 조회 화면을 테스트하기 위한 샘플 데이터다.
INSERT IGNORE INTO ROOM_RESERVATION
(reservation_id, user_id, room_id, start_time, end_time, purpose, reservation_status) VALUES
(1, 3, 4, '2026-05-18 14:00:00', '2026-05-18 16:00:00', '공부', 'RESERVED'),
(2, 2, 3, '2026-05-18 18:00:00', '2026-05-18 19:00:00', '요리', 'RESERVED'),
(3, 1, 1, '2026-05-17 09:00:00', '2026-05-17 10:00:00', '가족회의', 'FINISHED'),
(4, 4, 2, '2026-05-17 13:00:00', '2026-05-17 14:00:00', '휴식', 'CANCELLED');

-- 11. Pico 장치와 방의 연결
-- 각 Pico 2 W가 어느 방을 담당하는지 등록한다.
INSERT IGNORE INTO DEVICE (device_id, room_id, device_name) VALUES
('pico_living_room', 1, 'Pico 1 - 거실'),
('pico_bedroom', 2, 'Pico 2 - 안방'),
('pico_kitchen', 3, 'Pico 3 - 주방');

-- 12. 초기 센서 로그
-- 대시보드를 처음 열었을 때 빈 화면이 되지 않도록 샘플 값을 넣는다.
INSERT INTO SENSOR_READING (sensor_id, measured_value, measured_time) VALUES
(1, 23.5, '2026-05-17 09:00:00'),
(2, 45.0, '2026-05-17 09:00:00'),
(3, 320.0, '2026-05-17 09:00:00'),
(4, 22.1, '2026-05-17 09:00:00'),
(5, 50.0, '2026-05-17 09:00:00'),
(6, 25.0, '2026-05-17 09:00:00'),
(7, 0, '2026-05-17 09:00:00');

-- 13. 초기 액추에이터 상태 로그
-- 최신 상태 조회 화면을 테스트하기 위한 시작값이다.
INSERT INTO ACTUATOR_STATE_LOG (actuator_id, state_value, changed_time) VALUES
(1, 'OFF', '2026-05-17 09:00:00'),
(2, 'OFF', '2026-05-17 09:00:00'),
(3, 'OPEN', '2026-05-17 09:00:00'),
(4, 'OFF', '2026-05-17 09:00:00'),
(5, 'OFF', '2026-05-17 09:00:00'),
(6, 'ON', '2026-05-17 09:00:00'),
(7, 'OFF', '2026-05-17 09:00:00');

-- 14. 초기 방 상태 로그
-- 각 방의 현재 상태 화면을 테스트하기 위한 시작값이다.
INSERT INTO ROOM_STATUS_LOG (room_id, status_id, changed_time) VALUES
(1, 2, '2026-05-17 09:00:00'),
(2, 1, '2026-05-17 09:00:00'),
(3, 2, '2026-05-17 09:00:00'),
(4, 3, '2026-05-17 09:00:00'),
(5, 1, '2026-05-17 09:00:00');
