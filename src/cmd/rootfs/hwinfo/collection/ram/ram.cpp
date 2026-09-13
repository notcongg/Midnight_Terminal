#include "ram.hpp"

#include <algorithm>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif


namespace {

using midnight::ram::MemoryDevice;
using midnight::ram::RamInfo;

constexpr std::uint8_t SMBIOS_END_OF_TABLE = 127;


// ============================================================================
// Safe string helpers
// ============================================================================

template <std::size_t N>
void copy_string(
    char (&destination)[N],
    const std::string& source
) {
    if constexpr (N == 0) {
        return;
    }

    std::memset(destination, 0, N);

    const std::size_t count =
        std::min<std::size_t>(
            source.size(),
            N - 1
        );

    std::memcpy(
        destination,
        source.data(),
        count
    );
}


std::string read_smbios_string(
    const std::uint8_t* strings,
    std::size_t strings_length,
    std::uint8_t index
) {
    if (
        index == 0 ||
        strings == nullptr ||
        strings_length == 0
    ) {
        return {};
    }

    std::size_t current_index = 1;
    std::size_t offset = 0;

    while (offset < strings_length) {
        const char* current =
            reinterpret_cast<const char*>(
                strings + offset
            );

        const std::size_t remaining =
            strings_length - offset;

        const std::size_t length =
            strnlen(
                current,
                remaining
            );

        if (length == remaining) {
            return {};
        }

        if (current_index == index) {
            return std::string(
                current,
                length
            );
        }

        offset += length + 1;
        ++current_index;
    }

    return {};
}


// ============================================================================
// SMBIOS standard mappings
// ============================================================================

std::string memory_type_name(
    std::uint8_t type
) {
    switch (type) {
        case 1:
            return "Other";
        case 2:
            return "Unknown";
        case 3:
            return "DRAM";
        case 4:
            return "EDRAM";
        case 5:
            return "VRAM";
        case 6:
            return "SRAM";
        case 7:
            return "RAM";
        case 8:
            return "ROM";
        case 9:
            return "PROM";
        case 10:
            return "EPROM";
        case 11:
            return "EEPROM";
        case 12:
            return "Flash";
        case 13:
            return "NVRAM";
        case 14:
            return "Cache DRAM";
        case 15:
            return "CDRAM";
        case 16:
            return "3DRAM";
        case 17:
            return "SDRAM";
        case 18:
            return "SGRAM";
        case 19:
            return "RDRAM";
        case 20:
            return "DDR";
        case 21:
            return "DDR2";
        case 22:
            return "DDR2 FB-DIMM";
        case 24:
            return "DDR3";
        case 25:
            return "FBD2";
        case 26:
            return "DDR4";
        case 27:
            return "LPDDR";
        case 28:
            return "LPDDR2";
        case 29:
            return "LPDDR3";
        case 30:
            return "LPDDR4";
        case 31:
            return "Logical non-volatile device";
        case 32:
            return "HBM";
        case 33:
            return "HBM2";
        case 34:
            return "DDR5";
        case 35:
            return "LPDDR5";
        case 36:
            return "LPDDR6";
        default:
            return "Unknown";
    }
}


std::string form_factor_name(
    std::uint8_t value
) {
    switch (value) {
        case 1:
            return "Other";
        case 2:
            return "Unknown";
        case 3:
            return "SIMM";
        case 4:
            return "SIP";
        case 5:
            return "Chip";
        case 6:
            return "DIP";
        case 7:
            return "ZIP";
        case 8:
            return "DIMM";
        case 9:
            return "TSOP";
        case 10:
            return "Row of chips";
        case 11:
            return "RIMM";
        case 12:
            return "SO-DIMM";
        case 13:
            return "SRIMM";
        case 14:
            return "FB-DIMM";
        default:
            return "Unknown";
    }
}


// ============================================================================
// SMBIOS raw parser
// ============================================================================

bool parse_smbios(
    const std::uint8_t* data,
    std::size_t size,
    RamInfo& output
) {
    if (
        data == nullptr ||
        size < 4
    ) {
        return false;
    }

    std::size_t offset = 0;

    while (offset + 4 <= size) {
        const auto* structure =
            data + offset;

        const std::uint8_t type =
            structure[0];

        const std::uint8_t length =
            structure[1];

        if (length < 4) {
            return false;
        }

        if (offset + length > size) {
            return false;
        }

        // --------------------------------------------------------------------
        // Find the string-set terminator.
        //
        // SMBIOS structure:
        //
        //   formatted area
        //   string 1
        //   string 2
        //   ...
        //   \0\0
        // --------------------------------------------------------------------

        std::size_t string_end =
            offset + length;

        bool found_terminator = false;

        while (string_end + 1 < size) {
            if (
                data[string_end] == 0 &&
                data[string_end + 1] == 0
            ) {
                found_terminator = true;
                break;
            }

            ++string_end;
        }

        if (!found_terminator) {
            return false;
        }

        const std::size_t strings_begin =
            offset + length;

        const std::size_t strings_length =
            string_end - strings_begin;

        const auto* strings =
            data + strings_begin;

        // ====================================================================
        // Type 16: Physical Memory Array
        // ====================================================================

        if (
            type == 16 &&
            length >= 0x0F
        ) {
            // Offset 0x0D in SMBIOS Type 16:
            // Number Of Memory Devices
            const std::uint8_t devices =
                structure[0x0D];

            output.slots_total =
                devices;
        }

        // ====================================================================
        // Type 17: Memory Device
        // ====================================================================

        if (
            type == 17 &&
            length >= 0x1B
        ) {
            // SMBIOS Type 17:
            //
            // 0x0C = Size
            // 0x0E = Form Factor
            // 0x10 = Device Locator string
            // 0x11 = Bank Locator string
            // 0x12 = Memory Type
            // 0x15 = Speed
            // 0x17 = Manufacturer string
            // 0x18 = Serial Number string
            // 0x19 = Asset Tag string
            // 0x1A = Part Number string
            //

            const std::uint16_t size_field =
                static_cast<std::uint16_t>(
                    structure[0x0C]
                    | (
                        static_cast<std::uint16_t>(
                            structure[0x0D]
                        )
                        << 8
                    )
                );

            // 0 = no module / unknown
            // 0xFFFF = unknown
            if (
                size_field != 0 &&
                size_field != 0xFFFF
            ) {
                std::uint64_t capacity_bytes = 0;

                if (
                    size_field & 0x8000
                ) {
                    // SMBIOS:
                    // bit 15 = units are KiB
                    const std::uint64_t kib =
                        size_field & 0x7FFF;

                    capacity_bytes =
                        kib * 1024ULL;
                } else {
                    // Units are MiB.
                    const std::uint64_t mib =
                        size_field;

                    capacity_bytes =
                        mib * 1024ULL * 1024ULL;
                }

                if (
                    output.device_count
                    < midnight::ram::MAX_MEMORY_DEVICES
                ) {
                    MemoryDevice& device =
                        output.devices[
                            output.device_count
                        ];

                    device.capacity_bytes =
                        capacity_bytes;

                    const std::uint8_t form_factor =
                        structure[0x0E];

                    const std::uint8_t device_locator =
                        structure[0x10];

                    const std::uint8_t memory_type =
                        structure[0x12];

                    const std::uint16_t speed =
                        static_cast<std::uint16_t>(
                            structure[0x15]
                            | (
                                static_cast<std::uint16_t>(
                                    structure[0x16]
                                )
                                << 8
                            )
                        );

                    const std::uint8_t manufacturer =
                        structure[0x17];

                    const std::uint8_t part_number =
                        structure[0x1A];

                    copy_string(
                        device.form_factor,
                        form_factor_name(
                            form_factor
                        )
                    );

                    copy_string(
                        device.locator,
                        read_smbios_string(
                            strings,
                            strings_length,
                            device_locator
                        )
                    );

                    copy_string(
                        device.type,
                        memory_type_name(
                            memory_type
                        )
                    );

                    device.speed_mt = speed;

                    copy_string(
                        device.manufacturer,
                        read_smbios_string(
                            strings,
                            strings_length,
                            manufacturer
                        )
                    );

                    copy_string(
                        device.part_number,
                        read_smbios_string(
                            strings,
                            strings_length,
                            part_number
                        )
                    );

                    // SMBIOS 2.7+
                    //
                    // Extended size at 0x1C can describe modules
                    // larger than the 16-bit Size field.
                    if (length >= 0x20) {
                        const std::uint32_t extended_size =
                            static_cast<std::uint32_t>(
                                structure[0x1C]
                                | (
                                    static_cast<std::uint32_t>(
                                        structure[0x1D]
                                    )
                                    << 8
                                )
                                | (
                                    static_cast<std::uint32_t>(
                                        structure[0x1E]
                                    )
                                    << 16
                                )
                                | (
                                    static_cast<std::uint32_t>(
                                        structure[0x1F]
                                    )
                                    << 24
                                )
                            );

                        if (
                            extended_size != 0
                        ) {
                            device.capacity_bytes =
                                static_cast<
                                    std::uint64_t
                                >(extended_size)
                                * 1024ULL
                                * 1024ULL;
                        }
                    }

                    // Configured Memory Speed:
                    // SMBIOS Type 17 offset 0x20.
                    if (length >= 0x22) {
                        const std::uint16_t configured_speed =
                            static_cast<std::uint16_t>(
                                structure[0x20]
                                | (
                                    static_cast<std::uint16_t>(
                                        structure[0x21]
                                    )
                                    << 8
                                )
                            );

                        device.configured_speed_mt =
                            configured_speed;
                    }

                    // Use configured speed when available.
                    const std::uint32_t effective_speed =
                        device.configured_speed_mt > 0
                            ? device.configured_speed_mt
                            : device.speed_mt;

                    output.speed_mt =
                        std::max(
                            output.speed_mt,
                            effective_speed
                        );

                    output.total_bytes +=
                        device.capacity_bytes;

                    ++output.device_count;
                }
            }
        }

        if (type == SMBIOS_END_OF_TABLE) {
            break;
        }

        offset =
            string_end + 2;
    }

    output.slots_used =
        output.device_count;

    // Use the first detected module's type as the
    // top-level RAM type for normal hwinfo output.
    if (
        output.device_count > 0
    ) {
        copy_string(
            output.type,
            output.devices[0].type
        );
    }

    return output.device_count > 0;
}


// ============================================================================
// Linux: raw SMBIOS table
// ============================================================================

#ifdef __linux__

bool read_linux_smbios(
    std::vector<std::uint8_t>& table
) {
    std::ifstream file(
        "/sys/firmware/dmi/tables/DMI",
        std::ios::binary
    );

    if (!file) {
        return false;
    }

    file.seekg(
        0,
        std::ios::end
    );

    const std::streamoff size =
        file.tellg();

    if (
        size <= 0 ||
        size > static_cast<std::streamoff>(
            16 * 1024 * 1024
        )
    ) {
        return false;
    }

    file.seekg(
        0,
        std::ios::beg
    );

    table.resize(
        static_cast<std::size_t>(size)
    );

    file.read(
        reinterpret_cast<char*>(
            table.data()
        ),
        size
    );

    return file.good() || file.eof();
}

#endif


// ============================================================================
// Windows: raw SMBIOS table
// ============================================================================

#ifdef _WIN32

bool read_windows_smbios(
    std::vector<std::uint8_t>& table
) {
    constexpr DWORD provider =
        'RSMB';

    const UINT required =
        GetSystemFirmwareTable(
            provider,
            0,
            nullptr,
            0
        );

    if (required == 0) {
        return false;
    }

    std::vector<std::uint8_t> raw(
        required
    );

    const UINT received =
        GetSystemFirmwareTable(
            provider,
            0,
            raw.data(),
            required
        );

    if (
        received < 8 ||
        received > raw.size()
    ) {
        return false;
    }

    // Windows RSMB provider layout:
    //
    // BYTE  Used20CallingMethod
    // BYTE  MajorVersion
    // BYTE  MinorVersion
    // BYTE  DmiRevision
    // DWORD Length
    // BYTE  SMBIOSTableData[]
    //
    const std::uint32_t table_length =
        static_cast<std::uint32_t>(
            raw[4]
            | (
                static_cast<std::uint32_t>(
                    raw[5]
                )
                << 8
            )
            | (
                static_cast<std::uint32_t>(
                    raw[6]
                )
                << 16
            )
            | (
                static_cast<std::uint32_t>(
                    raw[7]
                )
                << 24
            )
        );

    if (
        table_length == 0 ||
        8ULL + table_length > received
    ) {
        return false;
    }

    table.assign(
        raw.begin() + 8,
        raw.begin() + 8 + table_length
    );

    return true;
}

#endif


} // namespace


// ============================================================================
// Public C ABI
// ============================================================================

extern "C"
MIDNIGHT_RAM_API int midnight_ram_collect(
    midnight::ram::RamInfo* out
) {
    if (out == nullptr) {
        return 0;
    }

    // Always initialize output.
    *out = {};

    std::vector<std::uint8_t> table;

#ifdef __linux__

    if (
        !read_linux_smbios(table)
    ) {
        return 0;
    }

#elif defined(_WIN32)

    if (
        !read_windows_smbios(table)
    ) {
        return 0;
    }

#else

    return 0;

#endif

    if (
        table.empty()
    ) {
        return 0;
    }

    return parse_smbios(
        table.data(),
        table.size(),
        *out
    ) ? 1 : 0;
}


extern "C"
MIDNIGHT_RAM_API const char* midnight_ram_backend() {

#ifdef __linux__
    return "raw-smbios-linux";

#elif defined(_WIN32)
    return "raw-smbios-windows";

#else
    return "unsupported";

#endif
}
