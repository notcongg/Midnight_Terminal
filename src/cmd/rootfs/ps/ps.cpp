#include "ps.hpp"

#ifdef _WIN32
#include "platform/windows/win.hpp"
namespace backend = midnight::ps::windows;
#else
#include "platform/linux/lin.hpp"
namespace backend = midnight::ps::linux_backend;
#endif

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace midnight::ps {

namespace {

constexpr double REFRESH_INTERVAL = 1.0;
constexpr double CPU_SAMPLE_INTERVAL = 0.25;

constexpr int NAME_WIDTH = 28;
constexpr int TYPE_WIDTH = 12;
constexpr int PERCENT_WIDTH = 7;

constexpr double CPU_HIGH_THRESHOLD = 25.0;
constexpr double MEM_WARN_THRESHOLD = 10.0;
constexpr double MEM_CRITICAL_THRESHOLD = 25.0;

constexpr int LIVE_MAX_ROWS = 25;
constexpr int LIVE_ROW_RESERVE = 5;


// ============================================================
// ANSI
// ============================================================

constexpr const char* ANSI_RESET = "\033[0m";
constexpr const char* ANSI_BOLD  = "\033[1m";
constexpr const char* ANSI_CYAN  = "\033[36m";
constexpr const char* ANSI_YELLOW = "\033[33m";
constexpr const char* ANSI_RED = "\033[31m";
constexpr const char* ANSI_GREEN = "\033[32m";
constexpr const char* ANSI_GRAY = "\033[90m";


// ============================================================
// Helpers
// ============================================================

bool stdout_is_tty() {
#ifdef _WIN32
    return _isatty(_fileno(stdout)) != 0;
#else
    return isatty(fileno(stdout)) != 0;
#endif
}

std::string paint(
    const std::string& text,
    const char* color
) {
    if (!color) {
        return text;
    }

    return std::string(color)
        + text
        + ANSI_RESET;
}

std::string lower(std::string value) {
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char c) {
            return static_cast<char>(
                std::tolower(c)
            );
        }
    );

    return value;
}

std::string format_name(
    const std::string& name
) {
    if (
        static_cast<int>(name.size())
        <= NAME_WIDTH
    ) {
        return name;
    }

    return name.substr(
        0,
        NAME_WIDTH - 3
    ) + "...";
}

std::string format_percent(
    const std::optional<double>& value,
    const char* color = nullptr
) {
    if (!value.has_value()) {
        return std::string(
            PERCENT_WIDTH - 1,
            ' '
        ) + "-";
    }

    std::ostringstream stream;

    stream << std::fixed
           << std::setprecision(1)
           << std::setw(PERCENT_WIDTH - 1)
           << *value
           << "%";

    const auto text = stream.str();

    return color
        ? paint(text, color)
        : text;
}


// ============================================================
// Option parsing
// ============================================================

std::size_t parse_count(
    const std::string& value
) {
    try {
        std::size_t position = 0;

        const unsigned long parsed =
            std::stoul(value, &position);

        if (
            position != value.size() ||
            parsed < 1
        ) {
            throw std::invalid_argument(
                "invalid count"
            );
        }

        return static_cast<std::size_t>(
            parsed
        );

    } catch (...) {
        throw std::runtime_error(
            "invalid value for '-n': '" +
            value +
            "' (expected a positive integer)"
        );
    }
}

bool parse_boolean(
    const std::string& value
) {
    const auto normalized =
        lower(value);

    if (normalized == "true") {
        return true;
    }

    if (normalized == "false") {
        return false;
    }

    throw std::runtime_error(
        "invalid value for '-rt': '" +
        value +
        "' (expected 'true' or 'false')"
    );
}

SortKey parse_sort_key(
    const std::string& value
) {
    const auto key = lower(value);

    if (key == "cpu") {
        return SortKey::Cpu;
    }

    if (key == "mem") {
        return SortKey::Mem;
    }

    if (key == "pid") {
        return SortKey::Pid;
    }

    if (key == "ppid") {
        return SortKey::Ppid;
    }

    if (key == "threads") {
        return SortKey::Threads;
    }

    if (key == "name") {
        return SortKey::Name;
    }

    throw std::runtime_error(
        "invalid value for '-sort': '" +
        value +
        "' (expected one of: "
        "cpu|mem|pid|ppid|threads|name)"
    );
}


// ============================================================
// System process classification
// ============================================================

bool is_system_process(
    const ProcessInfo& process
) {
    static const std::unordered_set<std::string>
        system_names = {

#ifdef _WIN32
        "system",
        "registry",
        "secure system",
        "memory compression",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "winlogon.exe",
        "services.exe",
        "lsass.exe",
        "lsaiso.exe",
        "svchost.exe",
        "dwm.exe",
        "fontdrvhost.exe",
        "audiodg.exe",
        "wudfhost.exe",
#else
        "systemd",
        "kthreadd",
        "ksoftirqd",
        "migration",
        "rcu_sched",
        "init",
#endif

    };

    if (process.pid <= 4) {
        return true;
    }

    return system_names.contains(
        lower(process.name)
    );
}

void classify(
    ProcessInfo& process,
    const std::unordered_set<std::uint32_t>& app_pids
) {
    if (is_system_process(process)) {
        process.category = "System";
    }
    else if (
        app_pids.contains(process.pid)
    ) {
        process.category = "App";
    }
    else {
        process.category = "Background";
    }
}


// ============================================================
// CPU metrics
// ============================================================

struct PreviousCpu {
    double cpu_time = 0.0;
    double timestamp = 0.0;
};

class ProcessMetrics {
public:
    void update(
        std::vector<ProcessInfo>& processes,
        std::uint64_t total_memory
    ) {
        using clock =
            std::chrono::steady_clock;

        const auto now_tp =
            clock::now();

        const double now =
            std::chrono::duration<double>(
                now_tp.time_since_epoch()
            ).count();

        std::unordered_map<
            std::uint32_t,
            PreviousCpu
        > current;

        const unsigned cpu_count =
            std::max(
                1u,
                std::thread::hardware_concurrency()
            );

        for (auto& process : processes) {
            const auto stats =
                backend::get_process_stats(
                    process.pid
                );

            if (
                stats.has_memory &&
                total_memory > 0
            ) {
                process.mem_percent =
                    static_cast<double>(
                        stats.working_set
                    )
                    / static_cast<double>(
                        total_memory
                    )
                    * 100.0;
            }

            if (!stats.has_cpu) {
                continue;
            }

            current[process.pid] =
                PreviousCpu{
                    stats.cpu_time,
                    now
                };

            const auto previous =
                previous_.find(
                    process.pid
                );

            if (
                previous == previous_.end()
            ) {
                process.cpu_percent = 0.0;
                continue;
            }

            const double elapsed =
                now -
                previous->second.timestamp;

            if (elapsed <= 0.0) {
                process.cpu_percent = 0.0;
                continue;
            }

            const double delta =
                stats.cpu_time -
                previous->second.cpu_time;

            double percent =
                delta /
                (
                    elapsed *
                    static_cast<double>(
                        cpu_count
                    )
                )
                * 100.0;

            percent =
                std::clamp(
                    percent,
                    0.0,
                    100.0
                );

            process.cpu_percent =
                percent;
        }

        previous_ = std::move(current);
    }

private:
    std::unordered_map<
        std::uint32_t,
        PreviousCpu
    > previous_;
};


// ============================================================
// Backend -> common ProcessInfo
// ============================================================

std::vector<ProcessInfo> collect_processes(
    ProcessMetrics& metrics
) {
    const auto raw =
        backend::enumerate_processes();

    std::unordered_set<std::uint32_t>
        app_pids;

    std::unordered_set<std::uint32_t>
        hung_pids;

    backend::enumerate_windows(
        app_pids,
        hung_pids
    );

    const auto total_memory =
        backend::get_total_memory();

    std::vector<ProcessInfo> processes;

    processes.reserve(
        raw.size()
    );

    for (const auto& process : raw) {
        ProcessInfo info;

        info.pid = process.pid;
        info.ppid = process.ppid;
        info.threads = process.threads;
        info.name = process.name;

        info.hung =
            hung_pids.contains(
                process.pid
            );

        processes.push_back(
            std::move(info)
        );
    }

    metrics.update(
        processes,
        total_memory
    );

    for (auto& process : processes) {
        classify(
            process,
            app_pids
        );
    }

    return processes;
}


// ============================================================
// Sorting
// ============================================================

void sort_processes(
    std::vector<ProcessInfo>& processes,
    std::optional<SortKey> key
) {
    if (!key.has_value()) {
        return;
    }

    switch (*key) {

    case SortKey::Cpu:
        std::sort(
            processes.begin(),
            processes.end(),
            [](const auto& a, const auto& b) {
                return
                    a.cpu_percent.value_or(0.0) >
                    b.cpu_percent.value_or(0.0);
            }
        );
        break;

    case SortKey::Mem:
        std::sort(
            processes.begin(),
            processes.end(),
            [](const auto& a, const auto& b) {
                return
                    a.mem_percent.value_or(0.0) >
                    b.mem_percent.value_or(0.0);
            }
        );
        break;

    case SortKey::Pid:
        std::sort(
            processes.begin(),
            processes.end(),
            [](const auto& a, const auto& b) {
                return a.pid < b.pid;
            }
        );
        break;

    case SortKey::Ppid:
        std::sort(
            processes.begin(),
            processes.end(),
            [](const auto& a, const auto& b) {
                return a.ppid < b.ppid;
            }
        );
        break;

    case SortKey::Threads:
        std::sort(
            processes.begin(),
            processes.end(),
            [](const auto& a, const auto& b) {
                return a.threads < b.threads;
            }
        );
        break;

    case SortKey::Name:
        std::sort(
            processes.begin(),
            processes.end(),
            [](const auto& a, const auto& b) {
                return lower(a.name) <
                       lower(b.name);
            }
        );
        break;
    }
}


// ============================================================
// Table formatting
// ============================================================

std::string build_row(
    const ProcessInfo& process,
    bool colors
) {
    std::ostringstream row;

    std::string pid =
        std::to_string(process.pid);

    pid.resize(8, ' ');

    if (colors) {
        pid = paint(
            pid,
            ANSI_CYAN
        );
    }

    const char* cpu_color = nullptr;

    if (
        colors &&
        process.cpu_percent.has_value() &&
        *process.cpu_percent >=
            CPU_HIGH_THRESHOLD
    ) {
        cpu_color = ANSI_YELLOW;
    }

    const char* mem_color = nullptr;

    if (
        colors &&
        process.mem_percent.has_value()
    ) {
        if (
            *process.mem_percent >=
            MEM_CRITICAL_THRESHOLD
        ) {
            mem_color = ANSI_RED;
        }
        else if (
            *process.mem_percent >=
            MEM_WARN_THRESHOLD
        ) {
            mem_color = ANSI_YELLOW;
        }
    }

    std::string type =
        process.category;

    if (
        static_cast<int>(type.size())
        < TYPE_WIDTH
    ) {
        type.resize(
            TYPE_WIDTH,
            ' '
        );
    }

    if (colors) {
        const char* type_color =
            ANSI_GRAY;

        if (
            process.category == "App"
        ) {
            type_color = ANSI_GREEN;
        }

        type =
            paint(
                type,
                type_color
            );
    }

    row << pid
        << ' '
        << std::left
        << std::setw(8)
        << process.ppid
        << ' '
        << std::setw(8)
        << process.threads
        << ' '
        << format_percent(
            process.cpu_percent,
            cpu_color
        )
        << ' '
        << format_percent(
            process.mem_percent,
            mem_color
        )
        << ' '
        << type
        << ' '
        << format_name(
            process.name
        );

    return row.str();
}


std::string format_table(
    const std::vector<ProcessInfo>& processes,
    bool colors
) {
    std::ostringstream output;

    std::ostringstream header;

    header << std::left
           << std::setw(8)
           << "PID"
           << ' '
           << std::setw(8)
           << "PPID"
           << ' '
           << std::setw(8)
           << "THREADS"
           << ' '
           << std::right
           << std::setw(PERCENT_WIDTH)
           << "CPU%"
           << ' '
           << std::setw(PERCENT_WIDTH)
           << "MEM%"
           << ' '
           << std::left
           << std::setw(TYPE_WIDTH)
           << "TYPE"
           << ' '
           << "NAME";

    std::string header_text =
        header.str();

    if (colors) {
        header_text =
            paint(
                header_text,
                ANSI_BOLD
            );
    }

    output << header_text
           << '\n';

    const int separator_length =
        8 + 1 +
        8 + 1 +
        8 + 1 +
        PERCENT_WIDTH + 1 +
        PERCENT_WIDTH + 1 +
        TYPE_WIDTH + 1 +
        NAME_WIDTH;

    output << std::string(
        separator_length,
        '-'
    );

    for (const auto& process : processes) {
        output << '\n';

        const auto row =
            build_row(
                process,
                colors
            );

        if (
            colors &&
            process.hung
        ) {
            output
                << paint(
                    row,
                    ANSI_RED
                );
        }
        else {
            output << row;
        }
    }

    return output.str();
}


// ============================================================
// Filtering
// ============================================================

void apply_filters(
    std::vector<ProcessInfo>& processes,
    const Options& options
) {
    if (!options.show_all) {
        processes.erase(
            std::remove_if(
                processes.begin(),
                processes.end(),
                [](const auto& p) {
                    return p.category ==
                           "System";
                }
            ),
            processes.end()
        );
    }

    if (
        options.filter_name.has_value()
    ) {
        const auto pattern =
            lower(
                *options.filter_name
            );

        processes.erase(
            std::remove_if(
                processes.begin(),
                processes.end(),
                [&](const auto& p) {
                    return
                        lower(p.name)
                        .find(pattern)
                        == std::string::npos;
                }
            ),
            processes.end()
        );
    }
}


// ============================================================
// Default grouped ordering
// ============================================================

int category_order(
    const std::string& category
) {
    if (category == "App") {
        return 0;
    }

    if (category == "Background") {
        return 1;
    }

    if (category == "System") {
        return 2;
    }

    return 9;
}

void default_sort(
    std::vector<ProcessInfo>& processes
) {
    std::sort(
        processes.begin(),
        processes.end(),
        [](const auto& a, const auto& b) {
            const int ca =
                category_order(
                    a.category
                );

            const int cb =
                category_order(
                    b.category
                );

            if (ca != cb) {
                return ca < cb;
            }

            return a.pid < b.pid;
        }
    );
}


// ============================================================
// Live sorting
// ============================================================

void live_sort(
    std::vector<ProcessInfo>& processes
) {
    std::sort(
        processes.begin(),
        processes.end(),
        [](const auto& a, const auto& b) {
            const double ac =
                a.cpu_percent.value_or(0.0);

            const double bc =
                b.cpu_percent.value_or(0.0);

            if (ac != bc) {
                return ac > bc;
            }

            const double am =
                a.mem_percent.value_or(0.0);

            const double bm =
                b.mem_percent.value_or(0.0);

            if (am != bm) {
                return am > bm;
            }

            return a.pid < b.pid;
        }
    );
}


// ============================================================
// Terminal rows
// ============================================================

int terminal_lines() {
#ifdef _WIN32
    CONSOLE_SCREEN_BUFFER_INFO info{};

    HANDLE handle =
        GetStdHandle(
            static_cast<DWORD>(-11)
        );

    if (
        handle != INVALID_HANDLE_VALUE &&
        GetConsoleScreenBufferInfo(
            handle,
            &info
        )
    ) {
        return
            info.srWindow.Bottom -
            info.srWindow.Top +
            1;
    }
#endif

    return 24;
}

int live_max_rows(
    const Options& options
) {
    int rows =
        terminal_lines();

    int max_rows =
        std::max(
            1,
            std::min(
                LIVE_MAX_ROWS,
                rows - LIVE_ROW_RESERVE
            )
        );

    if (
        options.limit.has_value()
    ) {
        max_rows =
            std::min(
                max_rows,
                static_cast<int>(
                    *options.limit
                )
            );
    }

    return max_rows;
}


// ============================================================
// Realtime
// ============================================================

std::string run_realtime(
    const Options& options,
    ProcessMetrics& metrics,
    bool colors
) {
    /*
     * If stdout isn't a terminal, don't enter an infinite
     * dashboard. Render one snapshot instead.
     */
    if (!stdout_is_tty()) {
        auto processes =
            collect_processes(
                metrics
            );

        apply_filters(
            processes,
            options
        );

        if (options.sort_key) {
            sort_processes(
                processes,
                options.sort_key
            );
        }
        else {
            live_sort(processes);
        }

        return format_table(
            processes,
            false
        );
    }

#ifdef _WIN32
    backend::enable_ansi_console();
#endif

    const int max_rows =
        live_max_rows(options);

    std::string previous_table;

    while (true) {
        auto processes =
            collect_processes(
                metrics
            );

        apply_filters(
            processes,
            options
        );

        if (options.sort_key) {
            sort_processes(
                processes,
                options.sort_key
            );
        }
        else {
            live_sort(processes);
        }

        if (
            static_cast<int>(
                processes.size()
            ) > max_rows
        ) {
            processes.resize(
                static_cast<std::size_t>(
                    max_rows
                )
            );
        }

        const auto table =
            format_table(
                processes,
                colors
            );

        if (!previous_table.empty()) {
            const auto lines =
                static_cast<int>(
                    std::count(
                        previous_table.begin(),
                        previous_table.end(),
                        '\n'
                    )
                ) + 1;

            std::cout
                << "\033["
                << lines
                << "F"
                << "\033[J";
        }

        std::cout
            << table
            << std::flush;

        previous_table = table;

        std::this_thread::sleep_for(
            std::chrono::duration<double>(
                REFRESH_INTERVAL
            )
        );
    }
}


// ============================================================
// One-shot
// ============================================================

std::string run_once(
    const Options& options,
    ProcessMetrics& metrics,
    bool colors
) {
    /*
     * Baseline.
     */
    collect_processes(
        metrics
    );

    std::this_thread::sleep_for(
        std::chrono::duration<double>(
            CPU_SAMPLE_INTERVAL
        )
    );

    /*
     * Actual measurement.
     */
    auto processes =
        collect_processes(
            metrics
        );

    apply_filters(
        processes,
        options
    );

    if (options.sort_key) {
        sort_processes(
            processes,
            options.sort_key
        );
    }
    else {
        default_sort(processes);
    }

    if (options.limit.has_value()) {
        const auto limit =
            *options.limit;

        if (
            processes.size() > limit
        ) {
            processes.resize(limit);
        }
    }

    return format_table(
        processes,
        colors
    );
}

} // namespace


// ============================================================
// Public API
// ============================================================

Options parse_options(
    const std::vector<std::string>& args
) {
    Options options;

    for (const auto& arg : args) {
        if (arg.empty()) {
            continue;
        }

        if (arg == "-a") {
            options.show_all = true;
            continue;
        }

        if (arg[0] != '-') {
            throw std::runtime_error(
                "unexpected argument '" +
                arg +
                "'"
            );
        }

        const auto equal =
            arg.find('=');

        const std::string key =
            equal == std::string::npos
                ? arg
                : arg.substr(0, equal);

        const std::string value =
            equal == std::string::npos
                ? ""
                : arg.substr(equal + 1);

        if (key == "-n") {
            if (value.empty()) {
                throw std::runtime_error(
                    "option '-n' requires a value "
                    "(use -n=<count>)"
                );
            }

            options.limit =
                parse_count(value);
        }

        else if (key == "-rt") {
            if (value.empty()) {
                throw std::runtime_error(
                    "option '-rt' requires a value "
                    "(use -rt=<true|false>)"
                );
            }

            options.realtime =
                parse_boolean(value);
        }

        else if (key == "-sort") {
            if (value.empty()) {
                throw std::runtime_error(
                    "option '-sort' requires a value "
                    "(use -sort=<key>)"
                );
            }

            options.sort_key =
                parse_sort_key(value);
        }

        else if (key == "-name") {
            if (value.empty()) {
                throw std::runtime_error(
                    "option '-name' requires a value "
                    "(use -name=<pattern>)"
                );
            }

            options.filter_name =
                value;
        }

        else {
            throw std::runtime_error(
                "unknown option '" +
                arg +
                "'"
            );
        }
    }

    return options;
}


std::string execute(
    const std::vector<std::string>& args
) {
    const auto options =
        parse_options(args);

    ProcessMetrics metrics;

    const bool colors =
        stdout_is_tty();

    if (options.realtime) {
        return run_realtime(
            options,
            metrics,
            colors
        );
    }

    return run_once(
        options,
        metrics,
        colors
    );
}


std::string manual() {
    return R"(PS(1)                    Midnight Terminal Manual                   PS(1)

NAME

    ps - list the running processes

SYNOPSIS

    ps
    ps -a
    ps -n=<count>
    ps -rt=true
    ps -rt=false
    ps -sort=<key>
    ps -name=<pattern>

DESCRIPTION

    Lists the running processes as a table, grouped into
    apps, background processes and system processes.

OPTIONS

    -a           include system processes as well

    -n=<count>   limit the table to <count> rows

    -rt=true     realtime mode

    -rt=false    one-shot mode (default)

    -sort=<key>  sort rows by cpu|mem|pid|ppid|threads|name

    -name=<pat>  only show processes whose name contains <pat>

)";
}

} // namespace midnight::ps