cmake_minimum_required(VERSION 3.20)

project(midnight_ram LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(midnight_ram SHARED
    ram.cpp
)

target_include_directories(
    midnight_ram
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
)

if (WIN32)
    set_target_properties(
        midnight_ram
        PROPERTIES
            OUTPUT_NAME "midnight_ram_windows"
            PREFIX ""
    )
else()
    set_target_properties(
        midnight_ram
        PROPERTIES
            OUTPUT_NAME "midnight_ram_linux"
    )
endif()
