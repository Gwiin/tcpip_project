const state = {
    dashboard: null,
    session: {loggedIn: false, user: null, role: "guest"},
    activeRoom: "living",
    editMode: false,
    activeModal: null,
    visibleCards: new Set(JSON.parse(localStorage.getItem("home-manager-visible-cards") || "[]"))
};

const elements = {
    connectionStatus: document.querySelector("#connection-status"),
    securityStatus: document.querySelector("#security-status"),
    avgTemp: document.querySelector("#avg-temp"),
    avgHumidity: document.querySelector("#avg-humidity"),
    currentTime: document.querySelector("#current-time"),
    sensorList: document.querySelector("#sensor-list"),
    temperatureChart: document.querySelector("#temperature-chart"),
    chartAverage: document.querySelector("#chart-average"),
    actuatorList: document.querySelector("#actuator-list"),
    reservationList: document.querySelector("#reservation-list"),
    locationUser: document.querySelector("#location-user"),
    locationTime: document.querySelector("#location-time"),
    locationUpdated: document.querySelector("#location-updated"),
    locationNote: document.querySelector("#location-note"),
    locationButton: document.querySelector("#location-button"),
    logList: document.querySelector("#log-list"),
    quickRoomList: document.querySelector("#quick-room-list"),
    gatewayIp: document.querySelector("#gateway-ip"),
    firmwareVersion: document.querySelector("#firmware-version"),
    noticeCount: document.querySelector("#notice-count"),
    profileName: document.querySelector("#profile-name"),
    profileRole: document.querySelector("#profile-role"),
    modalRoot: document.querySelector("#modal-root"),
    navButtons: document.querySelectorAll(".side-link"),
    dashboardCards: document.querySelectorAll("[data-card]")
};

const dashboardCardLabels = {
    sensors: "최신 센서 값",
    temperature: "방별 평균 온도",
    actuators: "현재 동작 중인 장치",
    reservations: "예약 / 스케줄",
    location: "사용자 위치",
    logs: "최근 로그"
};

if (state.visibleCards.size === 0) {
    Object.keys(dashboardCardLabels).forEach((card) => state.visibleCards.add(card));
}

const iconClassByName = {
    thermometer: "icon-thermo",
    drop: "icon-drop",
    sun: "icon-sun",
    co2: "icon-co2",
    light: "icon-sun",
    ac: "icon-ac",
    curtain: "icon-curtain",
    fan: "icon-fan",
    plug: "icon-plug",
    temp: "temp",
    user: "icon-user"
};

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function fetchJson(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
        let message = `${url} returned ${response.status}`;
        try {
            const payload = await response.json();
            message = payload.message || message;
        } catch (_error) {
            // Keep the HTTP status message when the response is not JSON.
        }
        const error = new Error(message);
        error.status = response.status;
        throw error;
    }
    return response.json();
}

function persistVisibleCards() {
    localStorage.setItem("home-manager-visible-cards", JSON.stringify([...state.visibleCards]));
}

function renderEmpty(message) {
    return `<p class="empty-state">${escapeHtml(message)}</p>`;
}

function renderSession() {
    elements.profileName.textContent = state.session.loggedIn ? state.session.user : "Guest";
    elements.profileRole.textContent = state.session.loggedIn ? String(state.session.role || "MEMBER").toUpperCase() : "로그인 필요";
    document.body.classList.toggle("is-authenticated", state.session.loggedIn);
}

function sparkline(points) {
    const safePoints = points.length > 1 ? points : [points[0] || 0, points[0] || 0];
    const max = Math.max(...safePoints);
    const min = Math.min(...safePoints);
    const spread = max - min || 1;
    const coordinates = safePoints.map((point, index) => {
        const x = (index / (safePoints.length - 1)) * 72;
        const y = 22 - ((point - min) / spread) * 18;
        return `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    });

    return `
        <svg class="sparkline" viewBox="0 0 72 28" aria-hidden="true">
            <path d="${coordinates.join(" ")}"></path>
        </svg>
    `;
}

function renderStatus(status) {
    elements.connectionStatus.textContent = status.connection;
    elements.securityStatus.textContent = status.security;
    elements.avgTemp.textContent = status.averageTemperature;
    elements.avgHumidity.textContent = status.averageHumidity;
    elements.currentTime.textContent = status.currentTime;
    elements.chartAverage.textContent = status.averageTemperature;
    elements.gatewayIp.textContent = status.gateway;
    elements.firmwareVersion.textContent = status.firmware;
    elements.noticeCount.textContent = String(buildNotifications().length);
}

function renderSensors(sensors, rooms) {
    if (!sensors.length) {
        elements.sensorList.innerHTML = renderEmpty("표시할 센서 값이 없습니다.");
        return;
    }
    const roomById = new Map(rooms.map((room) => [room.id, room]));
    elements.sensorList.innerHTML = sensors.map((sensor) => {
        const room = roomById.get(sensor.room);
        return `
            <article class="sensor-row">
                <span class="sensor-icon ${iconClassByName[sensor.icon] || ""}" aria-hidden="true"></span>
                <p class="sensor-label">${escapeHtml(sensor.label)}</p>
                <strong class="sensor-value">${escapeHtml(sensor.value)}</strong>
                ${sparkline(room?.spark || [2, 4, 3, 5, 4, 6])}
                <time class="time-text">${escapeHtml(sensor.time)}</time>
            </article>
        `;
    }).join("");
}

function renderTemperatureChart(temperatures) {
    if (!temperatures.length) {
        elements.temperatureChart.innerHTML = renderEmpty("온도 데이터가 없습니다.");
        return;
    }
    const maxValue = Math.max(...temperatures.map((item) => item.value), 1);
    elements.temperatureChart.innerHTML = temperatures.map((item) => {
        const height = Math.round((item.value / maxValue) * 150);
        return `
            <div class="bar-item">
                <span class="bar-value">${item.value.toFixed(1)}C</span>
                <span class="bar ${item.color}" style="height: ${height}px"></span>
                <span class="bar-label">${escapeHtml(item.room)}</span>
            </div>
        `;
    }).join("");
}

function renderActuators(actuators) {
    if (!actuators.length) {
        elements.actuatorList.innerHTML = renderEmpty("표시할 장치가 없습니다.");
        return;
    }
    elements.actuatorList.innerHTML = actuators.map((actuator) => `
        <article class="actuator-row">
            <span class="sensor-icon ${iconClassByName[actuator.icon] || ""}" aria-hidden="true"></span>
            <strong>${escapeHtml(actuator.name)}</strong>
            <small><span class="state-dot"></span> ${escapeHtml(actuator.detail)}</small>
            <button class="toggle ${actuator.active ? "is-on" : ""}" type="button" aria-label="${escapeHtml(actuator.name)} 전환" data-actuator-id="${escapeHtml(actuator.id)}" data-active="${actuator.active}"></button>
        </article>
    `).join("");
}

function renderReservations(reservations) {
    if (!reservations.length) {
        elements.reservationList.innerHTML = renderEmpty("등록된 예약이 없습니다.");
        return;
    }
    elements.reservationList.innerHTML = reservations.map((item) => `
        <article class="reservation-row">
            <time class="reservation-time">${escapeHtml(item.time)}</time>
            <div>
                <strong>${escapeHtml(item.title)}</strong>
                <small>${escapeHtml(item.repeat)}</small>
            </div>
            <span>${escapeHtml(item.status)}</span>
        </article>
    `).join("");
}

function renderLocation(location) {
    elements.locationUser.textContent = location.user;
    elements.locationTime.textContent = location.time;
    elements.locationUpdated.textContent = location.updated;
    if (location.source === "browser_geolocation") {
        const accuracy = location.accuracy ? `오차 약 ${location.accuracy}m` : "오차 정보 없음";
        elements.locationNote.textContent = `브라우저 위치 확인됨 · ${accuracy}`;
    } else {
        elements.locationNote.textContent = location.note;
    }
}

function renderLogs(logs) {
    if (!logs.length) {
        elements.logList.innerHTML = renderEmpty("최근 로그가 없습니다.");
        return;
    }
    elements.logList.innerHTML = logs.map((log) => `
        <article class="log-row">
            <span class="log-icon ${iconClassByName[log.icon] || ""}" aria-hidden="true"></span>
            <time>${escapeHtml(log.time)}</time>
            <p>${escapeHtml(log.message)}</p>
            <span>${escapeHtml(log.value)}</span>
        </article>
    `).join("");
}

function metricIcon(label) {
    if (label === "temperature") return "T";
    if (label === "humidity") return "%";
    return "L";
}

function renderRooms(rooms) {
    if (!rooms.length) {
        elements.quickRoomList.innerHTML = renderEmpty("등록된 방이 없습니다.");
        return;
    }
    elements.quickRoomList.innerHTML = rooms.map((room) => `
        <article class="room-card ${room.id === state.activeRoom ? "is-active" : ""}" data-room="${escapeHtml(room.id)}">
            <img src="/static/${escapeHtml(room.image)}" alt="${escapeHtml(room.name)} 이미지">
            <div class="room-card-content">
                <div>
                    <div class="room-card-top">
                        <h3>${escapeHtml(room.name)}</h3>
                        <span class="room-status">${escapeHtml(room.status)}</span>
                    </div>
                    <div class="room-metrics">
                        <span>${metricIcon("temperature")} ${room.temperature.toFixed(1)}C</span>
                        <span>${metricIcon("humidity")} ${room.humidity}%</span>
                        <span>${metricIcon("light")} ${room.light} lux</span>
                    </div>
                </div>
                <div class="room-card-bottom">
                    <span>장치 ${room.devices_on}개 켜짐</span>
                    <span>보기</span>
                </div>
            </div>
        </article>
    `).join("");
}

function applyDashboardCards() {
    elements.dashboardCards.forEach((card) => {
        const cardId = card.dataset.card;
        card.hidden = !state.visibleCards.has(cardId);
        card.classList.toggle("is-editing", state.editMode);
    });
    document.body.classList.toggle("is-dashboard-editing", state.editMode);
}

function buildNotifications() {
    if (!state.dashboard) return [];
    const notifications = [];
    const activeDevices = state.dashboard.status.activeDevices || state.dashboard.actuators.filter((item) => item.active).length;
    if (activeDevices > 0) {
        notifications.push({
            title: "동작 중인 장치",
            detail: `${activeDevices}개 장치가 켜져 있습니다.`
        });
    }
    state.dashboard.logs.slice(0, 3).forEach((log) => {
        notifications.push({
            title: log.message,
            detail: `${log.time} · ${log.value}`
        });
    });
    return notifications.slice(0, 6);
}

function modalList(items, className = "modal-list") {
    return `<div class="${className}">${items.join("")}</div>`;
}

function openModal(title, body, options = {}) {
    state.activeModal = options.action || null;
    elements.modalRoot.innerHTML = `
        <div class="modal-backdrop" data-close-modal></div>
        <section class="modal-panel liquid-panel" role="dialog" aria-modal="true" aria-labelledby="modal-title">
            <header class="modal-header">
                <h2 id="modal-title">${escapeHtml(title)}</h2>
                <button class="modal-close" type="button" aria-label="닫기" data-close-modal>×</button>
            </header>
            <div class="modal-body">${body}</div>
        </section>
    `;
    document.body.classList.add("has-modal");
    document.body.classList.remove("has-popover");
    elements.modalRoot.querySelector(".modal-close")?.focus();
}

function openPopover(anchor, title, body, options = {}) {
    const rect = anchor.getBoundingClientRect();
    const width = Math.min(360, window.innerWidth - 24);
    const left = Math.min(Math.max(12, rect.right - width), window.innerWidth - width - 12);
    const top = Math.min(rect.bottom + 12, window.innerHeight - 24);

    state.activeModal = options.action || null;
    elements.modalRoot.innerHTML = `
        <section class="notice-popover liquid-panel" role="dialog" aria-modal="false" aria-labelledby="notice-popover-title" style="--popover-left: ${left}px; --popover-top: ${top}px; --popover-width: ${width}px;">
            <header class="notice-popover-header">
                <h2 id="notice-popover-title">${escapeHtml(title)}</h2>
                <button class="modal-close" type="button" aria-label="닫기" data-close-modal>×</button>
            </header>
            <div class="notice-popover-body">${body}</div>
        </section>
    `;
    document.body.classList.add("has-popover");
    document.body.classList.remove("has-modal");
}

function closeModal() {
    if (state.activeModal === "edit-dashboard") {
        state.editMode = false;
        applyDashboardCards();
    }
    state.activeModal = null;
    elements.modalRoot.innerHTML = "";
    document.body.classList.remove("has-modal");
    document.body.classList.remove("has-popover");
}

function showSettingsModal() {
    const status = state.dashboard.status;
    openModal(
        "시스템 설정",
        `
            ${modalList([
                `<article><span>DB 연결</span><strong>${escapeHtml(status.connection)}</strong></article>`,
                `<article><span>게이트웨이</span><strong>${escapeHtml(status.gateway)}</strong></article>`,
                `<article><span>펌웨어</span><strong>${escapeHtml(status.firmware)}</strong></article>`,
                `<article><span>보안 상태</span><strong>${escapeHtml(status.security)}</strong></article>`
            ], "key-value-list")}
            <button class="primary-action" type="button" data-action="health-check">연결 상태 다시 확인</button>
            <p class="modal-note" id="health-result">현재 dashboard payload 기준 상태입니다.</p>
        `,
        {action: "settings"}
    );
}

function showNoticePopover(anchor) {
    const notifications = buildNotifications();
    openPopover(
        anchor,
        "알림",
        notifications.length
            ? modalList(notifications.map((item) => `
                <article>
                    <strong>${escapeHtml(item.title)}</strong>
                    <span>${escapeHtml(item.detail)}</span>
                </article>
            `))
            : renderEmpty("새 알림이 없습니다."),
        {action: "notice"}
    );
}

function showProfileModal() {
    const location = state.dashboard.location;
    if (!state.session.loggedIn) {
        showLoginModal();
        return;
    }
    openModal(
        "관리자 프로필",
        `
            ${modalList([
                `<article><span>사용자</span><strong>${escapeHtml(state.session.user || location.user)}</strong></article>`,
                `<article><span>현재 위치</span><strong>${escapeHtml(location.place || "집")}</strong></article>`,
                `<article><span>위치 출처</span><strong>${escapeHtml(location.source)}</strong></article>`,
                `<article><span>마지막 업데이트</span><strong>${escapeHtml(location.updated)}</strong></article>`
            ], "key-value-list")}
            <button class="danger-action" type="button" data-action="logout">로그아웃</button>
        `,
        {action: "profile"}
    );
}

function showLoginModal(message = "", mode = "login") {
    const isRegister = mode === "register";
    openModal(
        isRegister ? "회원가입" : "로그인",
        `
            <form class="login-form" id="login-form">
                <label>
                    <span>사용자명</span>
                    <input name="username" autocomplete="username" value="${isRegister ? "" : "관리자"}" required>
                </label>
                <label>
                    <span>비밀번호</span>
                    <input name="password" type="password" autocomplete="${isRegister ? "new-password" : "current-password"}" value="${isRegister ? "" : "admin123"}" required>
                </label>
                <input type="hidden" name="mode" value="${escapeHtml(mode)}">
                <button class="primary-action" type="submit">${isRegister ? "계정 만들기" : "로그인"}</button>
                <button class="link-action" type="button" data-action="${isRegister ? "show-login" : "show-register"}">${isRegister ? "로그인으로 돌아가기" : "새 계정 만들기"}</button>
                <p class="modal-note" id="login-message">${escapeHtml(message || (isRegister ? "생성한 계정은 SQL DB의 USER 테이블에 저장됩니다." : "기본 SQL 계정은 관리자 / admin123 입니다."))}</p>
            </form>
        `,
        {action: mode}
    );
    document.querySelector("#login-form input[name='username']")?.focus();
}

function showSensorsModal() {
    openModal(
        "전체 센서",
        state.dashboard.sensors.length
            ? modalList(state.dashboard.sensors.map((sensor) => `
                <article>
                    <span class="sensor-icon ${iconClassByName[sensor.icon] || ""}" aria-hidden="true"></span>
                    <strong>${escapeHtml(sensor.label)}</strong>
                    <span>${escapeHtml(sensor.value)}</span>
                    <time>${escapeHtml(sensor.time)}</time>
                </article>
            `), "detail-list")
            : renderEmpty("표시할 센서 값이 없습니다."),
        {action: "show-sensors"}
    );
}

function showActuatorsModal() {
    openModal(
        "전체 장치",
        state.dashboard.actuators.length
            ? modalList(state.dashboard.actuators.map((actuator) => `
                <article>
                    <span class="sensor-icon ${iconClassByName[actuator.icon] || ""}" aria-hidden="true"></span>
                    <strong>${escapeHtml(actuator.name)}</strong>
                    <span>${escapeHtml(actuator.detail)}</span>
                    <button class="toggle ${actuator.active ? "is-on" : ""}" type="button" aria-label="${escapeHtml(actuator.name)} 전환" data-actuator-id="${escapeHtml(actuator.id)}" data-active="${actuator.active}"></button>
                </article>
            `), "detail-list actuator-detail-list")
            : renderEmpty("표시할 장치가 없습니다."),
        {action: "show-actuators"}
    );
}

function showReservationsModal() {
    openModal(
        "예약 목록",
        state.dashboard.reservations.length
            ? modalList(state.dashboard.reservations.map((item) => `
                <article>
                    <time>${escapeHtml(item.time)}</time>
                    <strong>${escapeHtml(item.title)}</strong>
                    <span>${escapeHtml(item.repeat)}</span>
                    <em>${escapeHtml(item.status)}</em>
                </article>
            `), "detail-list")
            : renderEmpty("등록된 예약이 없습니다."),
        {action: "show-reservations"}
    );
}

function showLogsModal() {
    openModal(
        "최근 로그",
        state.dashboard.logs.length
            ? modalList(state.dashboard.logs.map((log) => `
                <article>
                    <span class="log-icon ${iconClassByName[log.icon] || ""}" aria-hidden="true"></span>
                    <time>${escapeHtml(log.time)}</time>
                    <strong>${escapeHtml(log.message)}</strong>
                    <span>${escapeHtml(log.value)}</span>
                </article>
            `), "detail-list")
            : renderEmpty("최근 로그가 없습니다."),
        {action: "show-logs"}
    );
}

function showRoomsModal() {
    openModal(
        "모든 방",
        state.dashboard.rooms.length
            ? modalList(state.dashboard.rooms.map((room) => `
                <button class="room-picker" type="button" data-room="${escapeHtml(room.id)}">
                    <img src="/static/${escapeHtml(room.image)}" alt="">
                    <span>
                        <strong>${escapeHtml(room.name)}</strong>
                        <small>${escapeHtml(room.status)} · ${room.temperature.toFixed(1)}C · ${room.humidity}%</small>
                    </span>
                    <b>${room.devices_on}개 켜짐</b>
                </button>
            `), "room-picker-list")
            : renderEmpty("등록된 방이 없습니다."),
        {action: "show-rooms"}
    );
}

function showEditModal() {
    state.editMode = true;
    applyDashboardCards();
    openModal(
        "대시보드 편집",
        `
            <div class="edit-card-list">
                ${Object.entries(dashboardCardLabels).map(([id, label]) => `
                    <label>
                        <input type="checkbox" data-card-toggle="${escapeHtml(id)}" ${state.visibleCards.has(id) ? "checked" : ""}>
                        <span>${escapeHtml(label)}</span>
                    </label>
                `).join("")}
            </div>
            <p class="modal-note">선택한 카드는 이 브라우저에 저장됩니다.</p>
        `,
        {action: "edit-dashboard"}
    );
}

function renderActiveModal() {
    if (state.activeModal === "show-actuators") showActuatorsModal();
}

async function loadSession() {
    state.session = await fetchJson("/api/session");
    renderSession();
}

function updateActiveNavigation(roomId, source = "room") {
    elements.navButtons.forEach((button) => {
        const isHome = button.dataset.home === "true";
        const isCurrentRoom = button.dataset.room === roomId && !isHome;
        button.classList.toggle("is-active", source === "home" ? isHome : isCurrentRoom);
    });
}

function renderDashboard(payload) {
    state.dashboard = payload;
    renderStatus(payload.status);
    renderSensors(payload.sensors, payload.rooms);
    renderTemperatureChart(payload.temperatures);
    renderActuators(payload.actuators);
    renderReservations(payload.reservations);
    renderLocation(payload.location);
    renderLogs(payload.logs);
    renderRooms(payload.rooms);
    applyDashboardCards();
}

async function loadDashboard() {
    const payload = await fetchJson("/api/dashboard");
    renderDashboard(payload);
}

async function selectRoom(roomId, source = "room") {
    state.activeRoom = roomId;
    updateActiveNavigation(roomId, source);
    const payload = await fetchJson(`/api/rooms/${roomId}`);
    renderActuators(payload.actuators.length ? payload.actuators : state.dashboard.actuators);
    renderSensors(payload.sensors.length ? payload.sensors : state.dashboard.sensors, state.dashboard.rooms);
    renderRooms(state.dashboard.rooms);
}

async function toggleActuator(button) {
    if (!state.session.loggedIn) {
        showLoginModal("장치를 제어하려면 먼저 로그인하세요.");
        return;
    }
    const actuatorId = button.dataset.actuatorId;
    const active = button.dataset.active !== "true";
    button.disabled = true;
    await fetchJson(`/api/actuators/${actuatorId}/toggle`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({active})
    });
    await loadDashboard();
    renderActiveModal();
}

async function runHealthCheck() {
    const result = document.querySelector("#health-result");
    if (!result) return;
    result.textContent = "연결 확인 중...";
    try {
        const payload = await fetchJson("/api/health");
        result.textContent = payload.success ? "MySQL 연결 확인 완료" : "MySQL 연결 확인 실패";
    } catch (error) {
        result.textContent = "MySQL 연결 확인에 실패했습니다.";
        console.error(error);
    }
}

async function handleAction(action, sourceElement) {
    if (!state.dashboard && action !== "health-check") return;

    if (action === "settings") showSettingsModal();
    if (action === "notice") showNoticePopover(sourceElement);
    if (action === "profile") showProfileModal();
    if (action === "edit-dashboard") showEditModal();
    if (action === "show-sensors") showSensorsModal();
    if (action === "show-actuators") showActuatorsModal();
    if (action === "show-reservations") showReservationsModal();
    if (action === "show-logs") showLogsModal();
    if (action === "show-rooms") showRoomsModal();
    if (action === "health-check") await runHealthCheck();
    if (action === "logout") await logout();
    if (action === "show-register") showLoginModal("", "register");
    if (action === "show-login") showLoginModal("", "login");
}

async function login(form) {
    const message = form.querySelector("#login-message");
    const submitButton = form.querySelector("button[type='submit']");
    submitButton.disabled = true;
    message.textContent = "로그인 중...";
    try {
        const formData = new FormData(form);
        const mode = formData.get("mode") === "register" ? "register" : "login";
        state.session = await fetchJson(`/api/session/${mode}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                username: formData.get("username"),
                password: formData.get("password")
            })
        });
        renderSession();
        closeModal();
    } catch (error) {
        if (error.status === 401) {
            message.textContent = "사용자명 또는 비밀번호가 맞지 않습니다.";
        } else if (error.status === 409) {
            message.textContent = "이미 존재하는 사용자명입니다.";
        } else {
            message.textContent = "요청 처리에 실패했습니다.";
        }
        submitButton.disabled = false;
    }
}

async function logout() {
    await fetchJson("/api/session/logout", {method: "POST"});
    await loadSession();
    closeModal();
}

function requestBrowserLocation() {
    if (!state.session.loggedIn) {
        showLoginModal("현재 위치를 저장하려면 먼저 로그인하세요.");
        return;
    }
    if (!("geolocation" in navigator)) {
        elements.locationNote.textContent = "이 브라우저는 위치 API를 지원하지 않습니다.";
        return;
    }

    elements.locationButton.disabled = true;
    elements.locationButton.textContent = "위치 확인 중...";
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            try {
                const payload = await fetchJson("/api/location", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    })
                });
                renderLocation(payload);
            } catch (error) {
                elements.locationNote.textContent = "위치 저장 API 호출에 실패했습니다.";
                console.error(error);
            } finally {
                elements.locationButton.disabled = false;
                elements.locationButton.innerHTML = "현재 위치 확인 <span>→</span>";
            }
        },
        (error) => {
            elements.locationNote.textContent = error.code === error.PERMISSION_DENIED
                ? "위치 권한이 거부되었습니다."
                : "현재 위치를 확인할 수 없습니다.";
            elements.locationButton.disabled = false;
            elements.locationButton.innerHTML = "현재 위치 확인 <span>→</span>";
        },
        {enableHighAccuracy: true, timeout: 8000, maximumAge: 30000}
    );
}

function bindEvents() {
    document.addEventListener("click", async (event) => {
        const navButton = event.target.closest(".side-link");
        const roomCard = event.target.closest(".room-card");
        const roomPicker = event.target.closest(".room-picker");
        const toggleButton = event.target.closest(".toggle");
        const actionButton = event.target.closest("[data-action]");
        const closeModalButton = event.target.closest("[data-close-modal]");

        try {
            if (closeModalButton) {
                closeModal();
            } else if (actionButton) {
                await handleAction(actionButton.dataset.action, actionButton);
            } else if (navButton) {
                await selectRoom(navButton.dataset.room, navButton.dataset.home === "true" ? "home" : "room");
            } else if (roomCard) {
                await selectRoom(roomCard.dataset.room);
            } else if (roomPicker) {
                await selectRoom(roomPicker.dataset.room);
                closeModal();
            } else if (toggleButton) {
                await toggleActuator(toggleButton);
            } else if (event.target.closest("#location-button")) {
                requestBrowserLocation();
            }
        } catch (error) {
            document.body.dataset.error = "true";
            console.error(error);
        }
    });

    document.addEventListener("click", (event) => {
        if (!document.body.classList.contains("has-popover")) return;
        if (elements.modalRoot.contains(event.target) || event.target.closest("[data-action='notice']")) return;
        closeModal();
    });

    document.addEventListener("submit", async (event) => {
        const form = event.target.closest("#login-form");
        if (!form) return;
        event.preventDefault();
        await login(form);
    });

    document.addEventListener("change", (event) => {
        const input = event.target.closest("[data-card-toggle]");
        if (!input) return;

        if (input.checked) {
            state.visibleCards.add(input.dataset.cardToggle);
        } else {
            state.visibleCards.delete(input.dataset.cardToggle);
        }
        if (state.visibleCards.size === 0) {
            state.visibleCards.add(input.dataset.cardToggle);
            input.checked = true;
        }
        persistVisibleCards();
        applyDashboardCards();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && (document.body.classList.contains("has-modal") || document.body.classList.contains("has-popover"))) {
            closeModal();
        }
    });
}

async function start() {
    bindEvents();
    try {
        await loadSession();
        await loadDashboard();
    } catch (error) {
        document.body.dataset.error = "true";
        console.error(error);
    }
}

start();
