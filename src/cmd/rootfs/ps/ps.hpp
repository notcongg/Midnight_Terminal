#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <optional>

namespace midnight::ps {

enum class SortKey {
    Cpu,
    Mem,
    Pid,
    Ppid,
    Threads,
    Name
};

struct Options {
    bool show_all = false;
    bool realtime = false;

    std::optional<std::size_t> limit;
    std::optional<SortKey> sort_key;
    std::optional<std::string> filter_name;
};

struct ProcessInfo {
    std::uint32_t pid = 0;
    std::uint32_t ppid = 0;
    std::uint32_t threads = 0;

    std::string name;
    std::string category;

    std::optional<double> cpu_percent;
    std::optional<double> mem_percent;

    bool hung = false;
};

/*
 * Parse:
 *
 * -a
 * -n=20
 * -rt=true
 * -rt=false
 * -sort=cpu
 * -name=python
 */
Options parse_options(
    const std::vector<std::string>& args
);

/*
 * Execute ps and return the rendered table.
 *
 * This is the main entry point used by bridge.cpp.
 */
std::string execute(
    const std::vector<std::string>& args
);

/*
 * Manual.
 */
std::string manual();

} // namespace midnight::ps