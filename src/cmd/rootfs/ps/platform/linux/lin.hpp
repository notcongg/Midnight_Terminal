#pragma once

#ifndef _WIN32

#include <cstdint>
#include <string>
#include <unordered_set>
#include <vector>

namespace midnight::ps::linux {

struct Process {
    std::uint32_t pid = 0;
    std::uint32_t ppid = 0;
    std::uint32_t threads = 0;
    std::string name;
};

struct ProcessStats {
    double cpu_time = 0.0;
    std::uint64_t working_set = 0;

    bool has_cpu = false;
    bool has_memory = false;
};

std::vector<Process> enumerate_processes();

void enumerate_windows(
    std::unordered_set<std::uint32_t>& app_pids,
    std::unordered_set<std::uint32_t>& hung_pids
);

ProcessStats get_process_stats(std::uint32_t pid);

std::uint64_t get_total_memory();

} // namespace midnight::ps::linux

#endif