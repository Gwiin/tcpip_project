-- Home Manager 프로젝트용 데이터베이스 생성
-- utf8mb4를 사용해 한글 데이터를 안전하게 저장한다.
CREATE DATABASE IF NOT EXISTS Home_Manager
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE Home_Manager;

-- 1. ROOM
-- 집 안의 방 정보를 저장한다.
-- 예: 거실, 안방, 주방, 공부방, 화장실
CREATE TABLE IF NOT EXISTS ROOM(
    room_id INT PRIMARY KEY,
    room_name VARCHAR(40) NOT NULL
);

-- 2. USER_ROLE
-- 사용자의 권한 종류를 저장한다.
-- 예: 관리자, 가족 구성원, 손님
CREATE TABLE IF NOT EXISTS USER_ROLE(
    role_id INT PRIMARY KEY,
    role_name VARCHAR(40) NOT NULL,
    CHECK (role_name IN ('ADMIN', 'GUEST', 'MEMBER'))
);

-- 3. USER
-- 시스템 사용자를 저장한다. 패스워드를 추가 한다.
-- 각 사용자는 하나의 권한을 가진다.
CREATE TABLE IF NOT EXISTS `USER`(
    user_id INT PRIMARY KEY,
    role_id INT,
    pw VARCHAR(255) NOT NULL,
    user_name VARCHAR(40) NOT NULL,
    FOREIGN KEY (role_id) REFERENCES USER_ROLE(role_id)
);

-- 4. SENSOR_TYPE
-- 센서 종류와 단위를 저장한다.
-- 예: temperature / C, humidity / %, motion / bool
CREATE TABLE IF NOT EXISTS SENSOR_TYPE(
    sensor_type_id INT PRIMARY KEY,
    type_name VARCHAR(40) NOT NULL,
    unit VARCHAR(10) NOT NULL
);

-- 5. SENSOR
-- 실제 설치된 센서 정보를 저장한다.
-- 어떤 방에 있고, 어떤 종류의 센서인지 연결한다.
CREATE TABLE IF NOT EXISTS SENSOR(
    sensor_id INT PRIMARY KEY,
    room_id INT,
    sensor_type_id INT,
    sensor_name VARCHAR(40),
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id),
    FOREIGN KEY (sensor_type_id) REFERENCES SENSOR_TYPE(sensor_type_id)
);

-- 6. SENSOR_READING
-- 센서가 측정한 값의 기록을 시간순으로 저장한다.
-- 이 테이블은 시간이 지날수록 계속 데이터가 쌓이는 로그 테이블이다.
CREATE TABLE IF NOT EXISTS SENSOR_READING(
    reading_id INT PRIMARY KEY AUTO_INCREMENT,
    sensor_id INT NOT NULL,
    measured_value DOUBLE NOT NULL,
    measured_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES SENSOR(sensor_id)
);

-- 7. ACTUATOR_TYPE
-- 액추에이터 종류를 저장한다.
-- 예: light, air_conditioner, fan, curtain
CREATE TABLE IF NOT EXISTS ACTUATOR_TYPE(
    actuator_type_id INT PRIMARY KEY,
    type_name VARCHAR(40) NOT NULL
);

-- 8. ACTUATOR
-- 실제 설치된 제어 장치를 저장한다.
-- 어떤 방에 있고, 어떤 종류의 장치인지 연결한다.
CREATE TABLE IF NOT EXISTS ACTUATOR(
    actuator_id INT PRIMARY KEY,
    room_id INT,
    actuator_type_id INT,
    actuator_name VARCHAR(40) NOT NULL,
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id),
    FOREIGN KEY (actuator_type_id) REFERENCES ACTUATOR_TYPE(actuator_type_id)
);

-- 9. ACTUATOR_STATE_LOG
-- 액추에이터 상태 변화 기록을 시간순으로 저장한다.
-- 예: ON, OFF, COOLING, HEATING, OPEN
CREATE TABLE IF NOT EXISTS ACTUATOR_STATE_LOG(
    actuator_state_id INT PRIMARY KEY AUTO_INCREMENT,
    actuator_id INT NOT NULL,
    state_value VARCHAR(40) NOT NULL,
    changed_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actuator_id) REFERENCES ACTUATOR(actuator_id)
);

-- 10. ROOM_STATUS_TYPE
-- 방 상태의 종류를 저장한다.
-- 예: EMPTY, IN_USE, CLEANING, RESERVED
CREATE TABLE IF NOT EXISTS ROOM_STATUS_TYPE(
    status_id INT PRIMARY KEY,
    status_name VARCHAR(40) NOT NULL
);

-- 11. ROOM_STATUS_LOG
-- 방 상태가 언제 어떻게 바뀌었는지 기록한다.
-- 최신 로그를 조회하면 현재 방 상태를 알 수 있다.
CREATE TABLE IF NOT EXISTS ROOM_STATUS_LOG(
    room_status_log_id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    status_id INT NOT NULL,
    changed_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id),
    FOREIGN KEY (status_id) REFERENCES ROOM_STATUS_TYPE(status_id)
);

-- 12. USER_LOCATION
-- 사용자가 현재 어느 방에 있는지 저장한다.
-- room_id가 NULL이면 위치 정보가 없는 상태를 의미한다.
CREATE TABLE IF NOT EXISTS USER_LOCATION(
    user_id INT PRIMARY KEY,
    room_id INT NULL,
    FOREIGN KEY (user_id) REFERENCES `USER`(user_id),
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
);

-- 13. ROOM_RESERVATION
-- 사용자가 특정 시간 동안 방을 예약한 정보를 저장한다.
-- 예약 시작 시간은 종료 시간보다 빨라야 한다.
CREATE TABLE IF NOT EXISTS ROOM_RESERVATION(
    reservation_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    room_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    purpose VARCHAR(40),
    reservation_status VARCHAR(40) NOT NULL,
    CHECK (start_time < end_time),
    CHECK (reservation_status IN ('RESERVED', 'CANCELLED', 'FINISHED')),
    FOREIGN KEY (user_id) REFERENCES `USER`(user_id),
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
);

-- 14. DEVICE
-- TCP 데이터를 보내는 Pico 2 W 장치와 담당 방을 연결한다.
-- 예: pico_living_room -> 거실
CREATE TABLE IF NOT EXISTS DEVICE(
    device_id VARCHAR(40) PRIMARY KEY,
    room_id INT NOT NULL,
    device_name VARCHAR(80) NOT NULL,
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
);
