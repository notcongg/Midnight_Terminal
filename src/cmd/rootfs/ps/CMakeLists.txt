cmake_minimum_required(VERSION 3.20)

project(midnight_ps LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(WIN32)

    add_library(midnight_ps SHARED
        ps.cpp
        bridge.cpp
        platform/windows/win.cpp
    )

    target_include_directories(midnight_ps PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/platform/windows
    )

    target_link_libraries(midnight_ps PRIVATE
        Psapi
    )

else()

    add_library(midnight_ps SHARED
        ps.cpp
        bridge.cpp
        platform/linux/lin.cpp
    )

    target_include_directories(midnight_ps PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/platform/linux
    )

endif()