cmake_minimum_required(VERSION 3.20)

project(MidnightAuth LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SODIUM REQUIRED libsodium)

add_library(midnight_auth SHARED
    auth.cpp
    is_avail.cpp

    binary/hash.cpp
    passwd/passwd.cpp
    recovery/reco.cpp
    storage/sto.cpp
    verify/veri.cpp
)

target_include_directories(midnight_auth
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}

    PRIVATE
        ${SODIUM_INCLUDE_DIRS}
)

target_link_directories(midnight_auth PRIVATE
    ${SODIUM_LIBRARY_DIRS}
)

target_link_libraries(midnight_auth PRIVATE
    ${SODIUM_LIBRARIES}
)