#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"

#if !defined(TEST_TCP_SERVER_IP)
#error TEST_TCP_SERVER_IP not defined
#endif
#if !defined(DEVICE_ID)
#error DEVICE_ID not defined
#endif

#define TCP_PORT 4242
#define SEND_INTERVAL_MS 5000
#define PAYLOAD_SIZE 256
#define DEBUG_printf printf

typedef struct TCP_CLIENT_T_ {
    struct tcp_pcb *tcp_pcb;
    ip_addr_t remote_addr;
    bool connected;
    bool complete;
} TCP_CLIENT_T;

static float random_float(float min, float max) {
    return min + ((float)rand() / (float)RAND_MAX) * (max - min);
}

static int random_bool(void) {
    return rand() % 2;
}

static const char* random_on_off(void) {
    return random_bool() ? "ON" : "OFF";
}

static const char* random_ac_state(void) {
    const char *states[] = {"OFF", "COOLING", "HEATING"};
    return states[rand() % 3];
}

static const char* random_curtain_state(void) {
    return random_bool() ? "OPEN" : "CLOSED";
}

static void build_payload(char *payload, size_t size) {
    if (strcmp(DEVICE_ID, "pico_living_room") == 0) {
        snprintf(payload, size,
            "{\"device_id\":\"%s\",\"sensors\":{\"temperature\":%.1f,\"humidity\":%.1f,\"light\":%.1f},\"actuators\":{\"light\":\"%s\",\"air_conditioner\":\"%s\",\"curtain\":\"%s\"}}\n",
            DEVICE_ID,
            random_float(20.0f, 29.0f),
            random_float(35.0f, 70.0f),
            random_float(100.0f, 700.0f),
            random_on_off(),
            random_ac_state(),
            random_curtain_state());
    } else if (strcmp(DEVICE_ID, "pico_bedroom") == 0) {
        snprintf(payload, size,
            "{\"device_id\":\"%s\",\"sensors\":{\"temperature\":%.1f,\"humidity\":%.1f},\"actuators\":{\"light\":\"%s\",\"air_conditioner\":\"%s\"}}\n",
            DEVICE_ID,
            random_float(19.0f, 27.0f),
            random_float(35.0f, 65.0f),
            random_on_off(),
            random_ac_state());
    } else {
        snprintf(payload, size,
            "{\"device_id\":\"%s\",\"sensors\":{\"temperature\":%.1f,\"motion\":%d},\"actuators\":{\"light\":\"%s\",\"fan\":\"%s\"}}\n",
            DEVICE_ID,
            random_float(21.0f, 31.0f),
            random_bool(),
            random_on_off(),
            random_on_off());
    }
}

static err_t tcp_client_close(void *arg) {
    TCP_CLIENT_T *state = (TCP_CLIENT_T*)arg;
    if (state->tcp_pcb != NULL) {
        tcp_arg(state->tcp_pcb, NULL);
        tcp_recv(state->tcp_pcb, NULL);
        tcp_err(state->tcp_pcb, NULL);
        tcp_close(state->tcp_pcb);
        state->tcp_pcb = NULL;
    }
    return ERR_OK;
}

static err_t tcp_client_recv(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err) {
    if (!p) {
        return tcp_client_close(arg);
    }
    tcp_recved(tpcb, p->tot_len);
    pbuf_free(p);
    return ERR_OK;
}

static void tcp_client_err(void *arg, err_t err) {
    DEBUG_printf("tcp error: %d\n", err);
    TCP_CLIENT_T *state = (TCP_CLIENT_T*)arg;
    state->connected = false;
    state->tcp_pcb = NULL;
}

static err_t tcp_client_connected(void *arg, struct tcp_pcb *tpcb, err_t err) {
    TCP_CLIENT_T *state = (TCP_CLIENT_T*)arg;
    if (err != ERR_OK) {
        DEBUG_printf("connect failed: %d\n", err);
        return err;
    }
    state->connected = true;
    DEBUG_printf("connected to server\n");
    return ERR_OK;
}

static bool tcp_client_open(TCP_CLIENT_T *state) {
    state->tcp_pcb = tcp_new_ip_type(IP_GET_TYPE(&state->remote_addr));
    if (!state->tcp_pcb) {
        return false;
    }
    tcp_arg(state->tcp_pcb, state);
    tcp_recv(state->tcp_pcb, tcp_client_recv);
    tcp_err(state->tcp_pcb, tcp_client_err);

    cyw43_arch_lwip_begin();
    err_t err = tcp_connect(state->tcp_pcb, &state->remote_addr, TCP_PORT, tcp_client_connected);
    cyw43_arch_lwip_end();
    return err == ERR_OK;
}

static bool send_payload(TCP_CLIENT_T *state) {
    char payload[PAYLOAD_SIZE];
    build_payload(payload, sizeof(payload));

    cyw43_arch_lwip_begin();
    err_t err = tcp_write(state->tcp_pcb, payload, strlen(payload), TCP_WRITE_FLAG_COPY);
    if (err == ERR_OK) {
        tcp_output(state->tcp_pcb);
    }
    cyw43_arch_lwip_end();

    if (err != ERR_OK) {
        DEBUG_printf("send failed: %d\n", err);
        return false;
    }

    DEBUG_printf("sent: %s", payload);
    return true;
}

int main() {
    stdio_init_all();
    sleep_ms(2000);
    srand(time_us_32());

    if (cyw43_arch_init()) {
        printf("failed to initialise\n");
        return 1;
    }
    cyw43_arch_enable_sta_mode();

    printf("connecting to Wi-Fi...\n");
    if (cyw43_arch_wifi_connect_timeout_ms(WIFI_SSID, WIFI_PASSWORD, CYW43_AUTH_WPA2_AES_PSK, 30000)) {
        printf("failed to connect Wi-Fi\n");
        return 1;
    }
    printf("Wi-Fi connected\n");

    TCP_CLIENT_T state = {0};
    ip4addr_aton(TEST_TCP_SERVER_IP, &state.remote_addr);

    if (!tcp_client_open(&state)) {
        printf("failed to start TCP connection\n");
        return 1;
    }

    while (true) {
#if PICO_CYW43_ARCH_POLL
        cyw43_arch_poll();
#endif
        if (state.connected) {
            send_payload(&state);
        }
        sleep_ms(SEND_INTERVAL_MS);
    }

    tcp_client_close(&state);
    cyw43_arch_deinit();
    return 0;
}
