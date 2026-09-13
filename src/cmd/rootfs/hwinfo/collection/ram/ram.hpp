#pragma once

#include <cstddef>
#include <cstdint>

#ifdef _WIN32
#define MIDNIGHT_RAM_API __declspec(dllexport)
#else
#define MIDNIGHT_RAM_API __attribute__((visibility("default")))
#endif

namespace midnight::ram {

constexpr std::size_t MAX_MEMORY_DEVICES = 64;
constexpr std::size_t MAX_STRING = 128;
constexpr std::size_t MAX_TYPE = 32;

struct MemoryDevice {
    std::uint64_t capacity_bytes = 0;
    std::uint32_t speed_mt = 0;
    std::uint32_t configured_speed_mt = 0;

    char manufacturer[MAX_STRING]{};
    char part_number[MAX_STRING]{};
    char locator[MAX_STRING]{};
    char form_factor[MAX_TYPE]{};
    char type[MAX_TYPE]{};
};

struct RamInfo {
    std::uint64_t total_bytes = 0;

    std::uint32_t slots_used = 0;
    std::uint32_t slots_total = 0;

    std::uint32_t speed_mt = 0;

    char type[MAX_TYPE]{};

    std::uint32_t device_count = 0;
    MemoryDevice devices[MAX_MEMORY_DEVICES]{};
};

} // namespace midnight::ram


extern "C" {

MIDNIGHT_RAM_API int midnight_ram_collect(
    midnight::ram::RamInfo* out
);

MIDNIGHT_RAM_API const char* midnight_ram_backend();

}
