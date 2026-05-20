-- Modern Home Manager MySQL setup
-- MySQL에 그대로 붙여넣으면 DB, 기본 테이블, Pico simulator seed 데이터가 준비됩니다.

CREATE DATABASE IF NOT EXISTS Home_Manager
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE Home_Manager;

CREATE TABLE IF NOT EXISTS ROOM(
    room_id INT PRIMARY KEY,
    room_name VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS USER_ROLE(
    role_id INT PRIMARY KEY,
    role_name VARCHAR(40) NOT NULL,
    CHECK (role_name IN ('ADMIN', 'GUEST', 'MEMBER'))
);

CREATE TABLE IF NOT EXISTS `USER`(
    user_id INT PRIMARY KEY,
    role_id INT,
    pw VARCHAR(255) NOT NULL,
    user_name VARCHAR(40) NOT NULL,
    FOREIGN KEY (role_id) REFERENCES USER_ROLE(role_id)
);

CREATE TABLE IF NOT EXISTS SENSOR_TYPE(
    sensor_type_id INT PRIMARY KEY,
    type_name VARCHAR(40) NOT NULL,
    unit VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS SENSOR(
    sensor_id INT PRIMARY KEY,
    room_id INT,
    sensor_type_id INT,
    sensor_name VARCHAR(40),
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id),
    FOREIGN KEY (sensor_type_id) REFERENCES SENSOR_TYPE(sensor_type_id)
);

CREATE TABLE IF NOT EXISTS SENSOR_READING(
    reading_id INT PRIMARY KEY AUTO_INCREMENT,
    sensor_id INT NOT NULL,
    measured_value DOUBLE NOT NULL,
    measured_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES SENSOR(sensor_id),
    INDEX idx_sensor_latest (sensor_id, measured_time, reading_id)
);

CREATE TABLE IF NOT EXISTS ACTUATOR_TYPE(
    actuator_type_id INT PRIMARY KEY,
    type_name VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS ACTUATOR(
    actuator_id INT PRIMARY KEY,
    room_id INT,
    actuator_type_id INT,
    actuator_name VARCHAR(40) NOT NULL,
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id),
    FOREIGN KEY (actuator_type_id) REFERENCES ACTUATOR_TYPE(actuator_type_id)
);

CREATE TABLE IF NOT EXISTS ACTUATOR_STATE_LOG(
    actuator_state_id INT PRIMARY KEY AUTO_INCREMENT,
    actuator_id INT NOT NULL,
    state_value VARCHAR(40) NOT NULL,
    changed_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actuator_id) REFERENCES ACTUATOR(actuator_id),
    INDEX idx_actuator_latest (actuator_id, changed_time, actuator_state_id)
);

CREATE TABLE IF NOT EXISTS ROOM_STATUS_TYPE(
    status_id INT PRIMARY KEY,
    status_name VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS ROOM_STATUS_LOG(
    room_status_log_id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    status_id INT NOT NULL,
    changed_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id),
    FOREIGN KEY (status_id) REFERENCES ROOM_STATUS_TYPE(status_id),
    INDEX idx_room_status_latest (room_id, changed_time, room_status_log_id)
);

CREATE TABLE IF NOT EXISTS USER_LOCATION(
    user_id INT PRIMARY KEY,
    room_id INT NULL,
    FOREIGN KEY (user_id) REFERENCES `USER`(user_id),
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
);

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

CREATE TABLE IF NOT EXISTS DEVICE(
    device_id VARCHAR(40) PRIMARY KEY,
    room_id INT NOT NULL,
    device_name VARCHAR(80) NOT NULL,
    FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
);

CREATE TABLE IF NOT EXISTS MODERN_BROWSER_LOCATION(
    user_id INT PRIMARY KEY,
    source VARCHAR(40) NOT NULL,
    latitude DOUBLE NULL,
    longitude DOUBLE NULL,
    accuracy DOUBLE NULL,
    note VARCHAR(255) NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES `USER`(user_id)
);

INSERT IGNORE INTO ROOM (room_id, room_name) VALUES
(1, '거실'),
(2, '침실'),
(3, '주방'),
(4, '공부방'),
(5, '화장실');

INSERT IGNORE INTO USER_ROLE (role_id, role_name) VALUES
(1, 'ADMIN'),
(2, 'MEMBER'),
(3, 'GUEST');

INSERT IGNORE INTO `USER` (user_id, role_id, pw, user_name) VALUES
(1, 1, 'pbkdf2:sha256:1000000$S5Y9spM8pbe0Tc2B$3c354bbc2376fd0875ae7ba2d279f2b405d7b71f1e582ae5ce9da1ce9c2d7bc0', '관리자'),
(2, 2, 'pbkdf2:sha256:1000000$tSRmFIRMImpNqrJE$c1b5d5a81e28763a0d0559d092d756eae066dd3b6a9169febdd1e31331759ff6', '가족'),
(3, 3, 'pbkdf2:sha256:1000000$Jw9bsbN0vDkDG1bz$5ff666237eec83342829a3ba0801d142e386a040a990e3bde93f011457177481', '손님');

UPDATE `USER`
SET pw = CASE user_name
    WHEN '관리자' THEN 'pbkdf2:sha256:1000000$S5Y9spM8pbe0Tc2B$3c354bbc2376fd0875ae7ba2d279f2b405d7b71f1e582ae5ce9da1ce9c2d7bc0'
    WHEN '가족' THEN 'pbkdf2:sha256:1000000$tSRmFIRMImpNqrJE$c1b5d5a81e28763a0d0559d092d756eae066dd3b6a9169febdd1e31331759ff6'
    WHEN '손님' THEN 'pbkdf2:sha256:1000000$Jw9bsbN0vDkDG1bz$5ff666237eec83342829a3ba0801d142e386a040a990e3bde93f011457177481'
    ELSE pw
END
WHERE (user_name = '관리자' AND pw = 'admin123')
   OR (user_name = '가족' AND pw = 'member123')
   OR (user_name = '손님' AND pw = 'guest123');

INSERT IGNORE INTO SENSOR_TYPE (sensor_type_id, type_name, unit) VALUES
(1, 'temperature', 'C'),
(2, 'humidity', '%'),
(3, 'motion', 'bool'),
(4, 'light', 'lux');

INSERT IGNORE INTO SENSOR (sensor_id, room_id, sensor_type_id, sensor_name) VALUES
(1, 1, 1, '거실 온도 센서'),
(2, 1, 2, '거실 습도 센서'),
(3, 1, 4, '거실 조도 센서'),
(4, 2, 1, '침실 온도 센서'),
(5, 2, 2, '침실 습도 센서'),
(6, 3, 1, '주방 온도 센서'),
(7, 3, 3, '주방 움직임 센서'),
(8, 4, 1, '공부방 온도 센서'),
(9, 4, 3, '공부방 움직임 센서'),
(10, 5, 2, '화장실 습도 센서');

INSERT IGNORE INTO ACTUATOR_TYPE (actuator_type_id, type_name) VALUES
(1, 'light'),
(2, 'air_conditioner'),
(3, 'fan'),
(4, 'door_lock'),
(5, 'curtain');

INSERT IGNORE INTO ACTUATOR (actuator_id, room_id, actuator_type_id, actuator_name) VALUES
(1, 1, 1, '거실 조명'),
(2, 1, 2, '거실 에어컨'),
(3, 1, 5, '거실 커튼'),
(4, 2, 1, '침실 조명'),
(5, 2, 2, '침실 에어컨'),
(6, 3, 1, '주방 조명'),
(7, 3, 3, '주방 선풍기'),
(8, 4, 1, '공부방 조명'),
(9, 4, 2, '공부방 에어컨'),
(10, 5, 1, '화장실 조명'),
(11, 5, 3, '화장실 선풍기');

INSERT IGNORE INTO ROOM_STATUS_TYPE (status_id, status_name) VALUES
(1, 'EMPTY'),
(2, 'IN_USE'),
(3, 'CLEANING'),
(4, 'RESERVED');

INSERT IGNORE INTO USER_LOCATION (user_id, room_id) VALUES
(1, 1),
(2, 3),
(3, NULL);

INSERT IGNORE INTO MODERN_BROWSER_LOCATION
(user_id, source, latitude, longitude, accuracy, note, updated_at) VALUES
(1, 'mysql_seed', NULL, NULL, NULL, '브라우저 위치 권한을 허용하면 GPS 기반 좌표를 저장합니다.', NOW());

INSERT IGNORE INTO ROOM_RESERVATION
(reservation_id, user_id, room_id, start_time, end_time, purpose, reservation_status) VALUES
(1, 1, 1, '2026-05-20 22:00:00', '2026-05-20 22:10:00', '거실 조명 끄기', 'RESERVED'),
(2, 1, 1, '2026-05-21 07:00:00', '2026-05-21 07:10:00', '거실 커튼 열기', 'RESERVED'),
(3, 2, 3, '2026-05-20 18:30:00', '2026-05-20 19:00:00', '에어컨 켜기', 'RESERVED');

INSERT IGNORE INTO DEVICE (device_id, room_id, device_name) VALUES
('pico_living_room', 1, 'Pico 1 - 거실'),
('pico_bedroom', 2, 'Pico 2 - 침실'),
('pico_kitchen', 3, 'Pico 3 - 주방');

INSERT INTO SENSOR_READING (sensor_id, measured_value, measured_time)
SELECT 1, 23.5, NOW() WHERE NOT EXISTS (SELECT 1 FROM SENSOR_READING WHERE sensor_id = 1)
UNION ALL SELECT 2, 45.0, NOW() WHERE NOT EXISTS (SELECT 1 FROM SENSOR_READING WHERE sensor_id = 2)
UNION ALL SELECT 3, 320.0, NOW() WHERE NOT EXISTS (SELECT 1 FROM SENSOR_READING WHERE sensor_id = 3)
UNION ALL SELECT 4, 22.1, NOW() WHERE NOT EXISTS (SELECT 1 FROM SENSOR_READING WHERE sensor_id = 4)
UNION ALL SELECT 5, 50.0, NOW() WHERE NOT EXISTS (SELECT 1 FROM SENSOR_READING WHERE sensor_id = 5)
UNION ALL SELECT 6, 25.0, NOW() WHERE NOT EXISTS (SELECT 1 FROM SENSOR_READING WHERE sensor_id = 6)
UNION ALL SELECT 7, 0, NOW() WHERE NOT EXISTS (SELECT 1 FROM SENSOR_READING WHERE sensor_id = 7);

INSERT INTO ACTUATOR_STATE_LOG (actuator_id, state_value, changed_time)
SELECT 1, 'OFF', NOW() WHERE NOT EXISTS (SELECT 1 FROM ACTUATOR_STATE_LOG WHERE actuator_id = 1)
UNION ALL SELECT 2, 'OFF', NOW() WHERE NOT EXISTS (SELECT 1 FROM ACTUATOR_STATE_LOG WHERE actuator_id = 2)
UNION ALL SELECT 3, 'OPEN', NOW() WHERE NOT EXISTS (SELECT 1 FROM ACTUATOR_STATE_LOG WHERE actuator_id = 3)
UNION ALL SELECT 4, 'OFF', NOW() WHERE NOT EXISTS (SELECT 1 FROM ACTUATOR_STATE_LOG WHERE actuator_id = 4)
UNION ALL SELECT 5, 'OFF', NOW() WHERE NOT EXISTS (SELECT 1 FROM ACTUATOR_STATE_LOG WHERE actuator_id = 5)
UNION ALL SELECT 6, 'ON', NOW() WHERE NOT EXISTS (SELECT 1 FROM ACTUATOR_STATE_LOG WHERE actuator_id = 6)
UNION ALL SELECT 7, 'OFF', NOW() WHERE NOT EXISTS (SELECT 1 FROM ACTUATOR_STATE_LOG WHERE actuator_id = 7);

INSERT INTO ROOM_STATUS_LOG (room_id, status_id, changed_time)
SELECT 1, 2, NOW() WHERE NOT EXISTS (SELECT 1 FROM ROOM_STATUS_LOG WHERE room_id = 1)
UNION ALL SELECT 2, 1, NOW() WHERE NOT EXISTS (SELECT 1 FROM ROOM_STATUS_LOG WHERE room_id = 2)
UNION ALL SELECT 3, 2, NOW() WHERE NOT EXISTS (SELECT 1 FROM ROOM_STATUS_LOG WHERE room_id = 3)
UNION ALL SELECT 4, 3, NOW() WHERE NOT EXISTS (SELECT 1 FROM ROOM_STATUS_LOG WHERE room_id = 4)
UNION ALL SELECT 5, 1, NOW() WHERE NOT EXISTS (SELECT 1 FROM ROOM_STATUS_LOG WHERE room_id = 5);

-- 대시보드 확인용 최신 센서 조회
SELECT
    r.room_name,
    s.sensor_name,
    st.type_name,
    sr.measured_value,
    st.unit,
    sr.measured_time
FROM SENSOR_READING sr
JOIN SENSOR s ON sr.sensor_id = s.sensor_id
JOIN SENSOR_TYPE st ON s.sensor_type_id = st.sensor_type_id
JOIN ROOM r ON s.room_id = r.room_id
WHERE sr.reading_id = (
    SELECT sr2.reading_id
    FROM SENSOR_READING sr2
    WHERE sr2.sensor_id = sr.sensor_id
    ORDER BY sr2.measured_time DESC, sr2.reading_id DESC
    LIMIT 1
)
ORDER BY r.room_id, s.sensor_id;
