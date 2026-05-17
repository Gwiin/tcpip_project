USE Home_Manager;

-- 1. 센서별 최신 측정값 조회
-- 각 센서의 가장 최근 데이터만 보여준다.
SELECT
    r.room_name,
    s.sensor_name,
    st.type_name,
    sr.measured_value,
    st.unit,
    sr.measured_time
FROM SENSOR_READING sr
JOIN SENSOR s
    ON sr.sensor_id = s.sensor_id
JOIN SENSOR_TYPE st
    ON s.sensor_type_id = st.sensor_type_id
JOIN ROOM r
    ON s.room_id = r.room_id
WHERE sr.measured_time = (
    SELECT MAX(sr2.measured_time)
    FROM SENSOR_READING sr2
    WHERE sr2.sensor_id = sr.sensor_id
)
ORDER BY r.room_id, s.sensor_id;

-- 2. 방별 평균 온도 조회
-- 각 방의 temperature 센서 데이터를 평균 내어 보여준다.
SELECT
    r.room_name,
    ROUND(AVG(sr.measured_value), 2) AS avg_temperature
FROM SENSOR_READING sr
JOIN SENSOR s
    ON sr.sensor_id = s.sensor_id
JOIN SENSOR_TYPE st
    ON s.sensor_type_id = st.sensor_type_id
JOIN ROOM r
    ON s.room_id = r.room_id
WHERE st.type_name = 'temperature'
GROUP BY r.room_id, r.room_name
ORDER BY r.room_id;

-- 3. 현재 동작 중인 액추에이터 조회
-- 각 액추에이터의 최신 상태 중 실제로 동작 중인 것만 보여준다.
SELECT
    r.room_name,
    a.actuator_name,
    at.type_name,
    asl.state_value,
    asl.changed_time
FROM ACTUATOR_STATE_LOG asl
JOIN ACTUATOR a
    ON asl.actuator_id = a.actuator_id
JOIN ACTUATOR_TYPE at
    ON a.actuator_type_id = at.actuator_type_id
JOIN ROOM r
    ON a.room_id = r.room_id
WHERE asl.changed_time = (
    SELECT MAX(asl2.changed_time)
    FROM ACTUATOR_STATE_LOG asl2
    WHERE asl2.actuator_id = asl.actuator_id
)
AND asl.state_value IN ('ON', 'COOLING', 'HEATING', 'OPEN')
ORDER BY r.room_id, a.actuator_id;

-- 4. 현재 방 상태 조회
-- 각 방의 최신 상태 로그를 기준으로 현재 상태를 보여준다.
SELECT
    r.room_name,
    rst.status_name,
    rsl.changed_time
FROM ROOM_STATUS_LOG rsl
JOIN ROOM r
    ON rsl.room_id = r.room_id
JOIN ROOM_STATUS_TYPE rst
    ON rsl.status_id = rst.status_id
WHERE rsl.changed_time = (
    SELECT MAX(rsl2.changed_time)
    FROM ROOM_STATUS_LOG rsl2
    WHERE rsl2.room_id = rsl.room_id
)
ORDER BY r.room_id;

-- 5. 사용자 현재 위치 조회
-- 사용자가 현재 어떤 방에 있는지 보여주며, 방 정보가 없으면 '위치 없음'으로 표시한다.
SELECT
    u.user_name,
    COALESCE(r.room_name, '위치 없음') AS current_location
FROM USER_LOCATION ul
JOIN `USER` u
    ON ul.user_id = u.user_id
LEFT JOIN ROOM r
    ON ul.room_id = r.room_id
ORDER BY u.user_id;

-- 6. 예약 전체 조회
-- 모든 예약 정보를 시작 시간 순서대로 보여준다.
SELECT
    rr.reservation_id,
    u.user_name,
    r.room_name,
    rr.start_time,
    rr.end_time,
    rr.purpose,
    rr.reservation_status
FROM ROOM_RESERVATION rr
JOIN `USER` u
    ON rr.user_id = u.user_id
JOIN ROOM r
    ON rr.room_id = r.room_id
ORDER BY rr.start_time;
