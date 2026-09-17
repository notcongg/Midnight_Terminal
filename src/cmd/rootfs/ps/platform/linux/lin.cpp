#ifndef _WIN32

#include "lin.hpp"

#include <unistd.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <dirent.h>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace midnight::ps::linux {

namespace {

// ============================================================
// Helpers
// ============================================================

bool is_numeric(const char* text) {
    if (!text || !*text) {
        return false;
    }

    for (const char* p = text; *p; ++p) {
        if (*p < '0' || *p > '9') {
            return false;
        }
    }

    return true;
}

std::string read_first_line(
    const std::string& path
) {
    std::ifstream file(path);

    if (!file) {
        return {};
    }

    std::string line;

    std::getline(file, line);

    return line;
}


// ============================================================
// /proc/<pid>/stat
//
// Format:
//
// pid (comm) state ppid ... utime stime ... num_threads ...
//
// Important:
// comm may contain spaces and ')' characters, so don't simply
// use operator>> from the beginning.
// ============================================================

bool read_stat(
    std::uint32_t pid,
    Process* process,
    double* cpu_time
) {
    const std::string path =
        "/proc/" + std::to_string(pid) + "/stat";

    std::ifstream file(path);

    if (!file) {
        return false;
    }

    std::string line;

    std::getline(file, line);

    if (line.empty()) {
        return false;
    }

    /*
     * Find the opening and closing parentheses around comm.
     *
     * Linux procfs puts the process name in:
     *
     * (comm)
     *
     * and the rest begins with:
     *
     * state ppid ...
     */
    const std::size_t open =
        line.find('(');

    const std::size_t close =
        line.rfind(')');

    if (
        open == std::string::npos ||
        close == std::string::npos ||
        close <= open
    ) {
        return false;
    }

    if (process) {
        process->pid = pid;

        process->name =
            line.substr(
                open + 1,
                close - open - 1
            );
    }

    /*
     * Everything after ") " starts at field 3.
     *
     * field 3 = state
     * field 4 = ppid
     *
     * Therefore after extracting state:
     *
     * ppid = first token
     * ...
     * utime = token 11
     * stime = token 12
     * ...
     * num_threads = token 20
     */
    std::string rest =
        line.substr(close + 2);

    std::istringstream stream(rest);

    char state = '\0';

    if (!(stream >> state)) {
        return false;
    }

    std::uint64_t ppid = 0;

    if (!(stream >> ppid)) {
        return false;
    }

    /*
     * After state + ppid, we're at field 5.
     *
     * Fields:
     *
     * 5  pgrp
     * 6  session
     * 7  tty_nr
     * 8  tpgid
     * 9  flags
     * 10 minflt
     * 11 cminflt
     * 12 majflt
     * 13 cmajflt
     * 14 utime
     * 15 stime
     * ...
     * 20 num_threads
     *
     * Since we're currently at field 5, skip 8 fields to reach
     * utime (field 14).
     */

    std::uint64_t ignored = 0;

    for (int i = 0; i < 8; ++i) {
        if (!(stream >> ignored)) {
            return false;
        }
    }

    std::uint64_t utime = 0;
    std::uint64_t stime = 0;

    if (!(stream >> utime >> stime)) {
        return false;
    }

    /*
     * Fields 16-19:
     *
     * cutime
     * cstime
     * priority
     * nice
     *
     * Then field 20 = num_threads.
     */

    for (int i = 0; i < 4; ++i) {
        if (!(stream >> ignored)) {
            return false;
        }
    }

    std::uint64_t threads = 0;

    if (!(stream >> threads)) {
        return false;
    }

    if (process) {
        process->ppid =
            static_cast<std::uint32_t>(ppid);

        process->threads =
            static_cast<std::uint32_t>(threads);
    }

    if (cpu_time) {
        const long ticks =
            sysconf(_SC_CLK_TCK);

        if (ticks <= 0) {
            return false;
        }

        *cpu_time =
            static_cast<double>(
                utime + stime
            ) / static_cast<double>(ticks);
    }

    return true;
}


// ============================================================
// /proc/<pid>/status
//
// VmRSS is the resident working set equivalent we want.
// ============================================================

bool read_working_set(
    std::uint32_t pid,
    std::uint64_t* working_set
) {
    const std::string path =
        "/proc/" + std::to_string(pid) + "/status";

    std::ifstream file(path);

    if (!file) {
        return false;
    }

    std::string line;

    while (std::getline(file, line)) {
        if (line.rfind("VmRSS:", 0) != 0) {
            continue;
        }

        std::istringstream stream(
            line.substr(6)
        );

        std::uint64_t value = 0;
        std::string unit;

        if (!(stream >> value >> unit)) {
            return false;
        }

        /*
         * Linux reports VmRSS in kB.
         */
        if (unit == "kB") {
            value *= 1024ULL;
        }

        *working_set = value;

        return true;
    }

    return false;
}

} // namespace


// ============================================================
// Process enumeration
// ============================================================

std::vector<Process> enumerate_processes() {
    std::vector<Process> processes;

    DIR* proc =
        opendir("/proc");

    if (!proc) {
        return processes;
    }

    while (true) {
        dirent* entry =
            readdir(proc);

        if (!entry) {
            break;
        }

        if (!is_numeric(entry->d_name)) {
            continue;
        }

        try {
            const auto pid =
                static_cast<std::uint32_t>(
                    std::stoul(entry->d_name)
                );

            Process process;

            if (read_stat(
                pid,
                &process,
                nullptr
            )) {
                processes.push_back(
                    std::move(process)
                );
            }

        } catch (...) {
            /*
             * Process may disappear between readdir()
             * and opening /proc/<pid>.
             *
             * Same practical behavior as the Windows
             * implementation: just skip it.
             */
        }
    }

    closedir(proc);

    return processes;
}


// ============================================================
// Window/process classification
// ============================================================

void enumerate_windows(
    std::unordered_set<std::uint32_t>& app_pids,
    std::unordered_set<std::uint32_t>& hung_pids
) {
    /*
     * There is no portable Linux equivalent of:
     *
     * EnumWindows()
     * IsWindowVisible()
     * IsHungAppWindow()
     *
     * In particular, Wayland intentionally does not expose
     * arbitrary global window ownership to applications.
     *
     * Leave both sets empty.
     *
     * ps.cpp can therefore classify Linux processes as
     * Background/System unless a Linux-specific desktop backend
     * is added later.
     */
    app_pids.clear();
    hung_pids.clear();
}


// ============================================================
// Process CPU / memory statistics
// ============================================================

ProcessStats get_process_stats(
    std::uint32_t pid
) {
    ProcessStats result;

    double cpu_time = 0.0;

    if (read_stat(
        pid,
        nullptr,
        &cpu_time
    )) {
        result.cpu_time = cpu_time;
        result.has_cpu = true;
    }

    std::uint64_t working_set = 0;

    if (read_working_set(
        pid,
        &working_set
    )) {
        result.working_set = working_set;
        result.has_memory = true;
    }

    return result;
}


// ============================================================
// Total physical RAM
// ============================================================

std::uint64_t get_total_memory() {
    std::ifstream file("/proc/meminfo");

    if (!file) {
        return 0;
    }

    std::string line;

    while (std::getline(file, line)) {
        if (line.rfind("MemTotal:", 0) != 0) {
            continue;
        }

        std::istringstream stream(
            line.substr(9)
        );

        std::uint64_t value = 0;
        std::string unit;

        if (!(stream >> value >> unit)) {
            return 0;
        }

        /*
         * /proc/meminfo normally reports kB.
         */
        if (unit == "kB") {
            value *= 1024ULL;
        }

        return value;
    }

    return 0;
}

} // namespace midnight::ps::linux

#endif