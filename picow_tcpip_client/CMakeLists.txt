cmake_minimum_required(VERSION 3.13)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.2.0)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.2.0-a4)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()

set(PICO_BOARD pico2_w CACHE STRING "Board type")
include(pico_sdk_import.cmake)
project(picow_tcpip_client C CXX ASM)

set(TEST_TCP_SERVER_IP "192.168.1.100")
set(WIFI_SSID "Your Wi-Fi SSID")
set(WIFI_PASSWORD "Your Wi-Fi Password")

pico_sdk_init()

function(add_home_manager_client target_name device_id)
    add_executable(${target_name} picow_tcp_client.c)
    target_compile_definitions(${target_name} PRIVATE
        WIFI_SSID=\"${WIFI_SSID}\"
        WIFI_PASSWORD=\"${WIFI_PASSWORD}\"
        TEST_TCP_SERVER_IP=\"${TEST_TCP_SERVER_IP}\"
        DEVICE_ID=\"${device_id}\"
    )
    target_include_directories(${target_name} PRIVATE
        ${CMAKE_CURRENT_LIST_DIR}
        ${CMAKE_CURRENT_LIST_DIR}/..
    )
    target_link_libraries(${target_name}
        pico_cyw43_arch_lwip_threadsafe_background
        pico_stdlib
    )
    pico_add_extra_outputs(${target_name})
endfunction()

add_home_manager_client(pico_living_room_client pico_living_room)
add_home_manager_client(pico_bedroom_client pico_bedroom)
add_home_manager_client(pico_kitchen_client pico_kitchen)
