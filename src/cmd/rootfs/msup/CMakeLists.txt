cmake_minimum_required(VERSION 3.20)

project(MidnightMSUP LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SODIUM REQUIRED libsodium)

# ============================================================
# Midnight SUPERUserPermissions
# ============================================================

add_library(midnight_msup SHARED
    msup.cpp
    bridge.cpp

    auth/auth.cpp
    auth/setup.cpp
    auth/cpswd.cpp
    auth/secrules/secrules.cpp

    state/state.cpp

    ../../../auth/binary/hash.cpp
    ../../../auth/passwd/passwd.cpp
    ../../../auth/storage/sto.cpp
)

target_include_directories(midnight_msup
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/../../../auth
        ${SODIUM_INCLUDE_DIRS}
)

target_link_directories(midnight_msup
    PRIVATE
        ${SODIUM_LIBRARY_DIRS}
)

target_link_libraries(midnight_msup
    PRIVATE
        ${SODIUM_LIBRARIES}
)

target_compile_options(midnight_msup
    PRIVATE
        ${SODIUM_CFLAGS_OTHER}
)