const state = {
    dashboard: null,
    activeRoom: "living"
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
    navButtons: document.querySelectorAll(".side-link")
};

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
        throw new Error(`${url} returned ${response.status}`);
    }
    return response.json();
}

function sparkline(points) {
    const max = Math.max(...points);
    const min = Math.min(...points);
    const spread = max - min || 1;
    const coordinates = points.map((point, index) => {
        const x = (index / (points.length - 1)) * 72;
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
}

function renderSensors(sensors, rooms) {
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
    const maxValue = Math.max(...temperatures.map((item) => item.value));
    elements.temperatureChart.innerHTML = temperatures.map((item) => {
        const height = Math.round((item.value / maxValue) * 150);
        return `
            <div class="bar-item">
                <span class="bar-value">${item.value.toFixed(1)}°C</span>
                <span class="bar ${item.color}" style="height: ${height}px"></span>
                <span class="bar-label">${escapeHtml(item.room)}</span>
            </div>
        `;
    }).join("");
}

function renderActuators(actuators) {
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
    if (label === "temperature") return "♨";
    if (label === "humidity") return "◌";
    return "☼";
}

function renderRooms(rooms) {
    elements.quickRoomList.innerHTML = rooms.map((room) => `
        <article class="room-card ${room.id === state.activeRoom ? "is-active" : ""}" data-room="${escapeHtml(room.id)}">
            <img src="/static/${escapeHtml(room.image)}" alt="${escapeHtml(room.name)} 이미지">
            <div class="room-card-content">
                <div>
                    <div class="room-card-top">
                        <h3>${escapeHtml(room.name)}</h3>
                        <span class="room-status">● ${escapeHtml(room.status)}</span>
                    </div>
                    <div class="room-metrics">
                        <span>${metricIcon("temperature")} ${room.temperature.toFixed(1)}°C</span>
                        <span>${metricIcon("humidity")} ${room.humidity}%</span>
                        <span>${metricIcon("light")} ${room.light} lux</span>
                    </div>
                </div>
                <div class="room-card-bottom">
                    <span>장치 ${room.devices_on}개 켜짐</span>
                    <span>›</span>
                </div>
            </div>
        </article>
    `).join("");
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
    const actuatorId = button.dataset.actuatorId;
    const active = button.dataset.active !== "true";
    await fetchJson(`/api/actuators/${actuatorId}/toggle`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({active})
    });
    await loadDashboard();
}

function requestBrowserLocation() {
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
                elements.locationButton.innerHTML = "내 위치 확인 <span>→</span>";
            }
        },
        (error) => {
            elements.locationNote.textContent = error.code === error.PERMISSION_DENIED
                ? "위치 권한이 거부되었습니다."
                : "현재 위치를 확인할 수 없습니다.";
            elements.locationButton.disabled = false;
            elements.locationButton.innerHTML = "내 위치 확인 <span>→</span>";
        },
        {enableHighAccuracy: true, timeout: 8000, maximumAge: 30000}
    );
}

function bindEvents() {
    document.addEventListener("click", async (event) => {
        const navButton = event.target.closest(".side-link");
        const roomCard = event.target.closest(".room-card");
        const toggleButton = event.target.closest(".toggle");

        try {
            if (navButton) {
                await selectRoom(navButton.dataset.room, navButton.dataset.home === "true" ? "home" : "room");
            } else if (roomCard) {
                await selectRoom(roomCard.dataset.room);
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
}

async function start() {
    bindEvents();
    try {
        await loadDashboard();
    } catch (error) {
        document.body.dataset.error = "true";
        console.error(error);
    }
}

start();
