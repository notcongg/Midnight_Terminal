#ifdef _WIN32

#include "win.hpp"

#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>

#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>
#include <cstdint>

namespace midnight::ps::windows {

namespace {

constexpr DWORD SNAPSHOT_FLAGS = TH32CS_SNAPPROCESS;

constexpr DWORD PROCESS_QUERY_LIMITED =
    PROCESS_QUERY_LIMITED_INFORMATION;

constexpr DWORD STD_OUTPUT = static_cast<DWORD>(-11);

constexpr DWORD ENABLE_VIRTUAL_TERMINAL_PROCESSING_FLAG = 0x0004;

/*
 * Convert UTF-16 Windows string -> UTF-8.
 */
std::string utf8_from_wide(const wchar_t* input) {
    if (!input || !*input) {
        return {};
    }

    int required = WideCharToMultiByte(
        CP_UTF8,
        0,
        input,
        -1,
        nullptr,
        0,
        nullptr,
        nullptr
    );

    if (required <= 0) {
        return {};
    }

    std::string result(
        static_cast<std::size_t>(required - 1),
        '\0'
    );

    WideCharToMultiByte(
        CP_UTF8,
        0,
        input,
        -1,
        result.data(),
        required,
        nullptr,
        nullptr
    );

    return result;
}

/*
 * Windows FILETIME -> seconds.
 *
 * FILETIME is a 64-bit value in units of 100 ns.
 */
double filetime_to_seconds(const FILETIME& time) {
    ULARGE_INTEGER value{};

    value.LowPart = time.dwLowDateTime;
    value.HighPart = time.dwHighDateTime;

    return static_cast<double>(value.QuadPart) /
           10'000'000.0;
}

/*
 * Context passed to EnumWindows().
 */
struct WindowContext {
    std::unordered_set<std::uint32_t>* app_pids;
    std::unordered_set<std::uint32_t>* hung_pids;
};

BOOL CALLBACK window_callback(
    HWND hwnd,
    LPARAM parameter
) {
    auto* context =
        reinterpret_cast<WindowContext*>(parameter);

    if (!context) {
        return FALSE;
    }

    /*
     * Same behavior as Python:
     *
     * if user32.IsWindowVisible(hwnd):
     */
    if (!IsWindowVisible(hwnd)) {
        return TRUE;
    }

    DWORD pid = 0;

    GetWindowThreadProcessId(
        hwnd,
        &pid
    );

    if (pid == 0) {
        return TRUE;
    }

    context->app_pids->insert(
        static_cast<std::uint32_t>(pid)
    );

    /*
     * Same behavior as:
     *
     * if user32.IsHungAppWindow(hwnd):
     */
    if (IsHungAppWindow(hwnd)) {
        context->hung_pids->insert(
            static_cast<std::uint32_t>(pid)
        );
    }

    return TRUE;
}

} // namespace


// ============================================================
// Process enumeration
// ============================================================

std::vector<Process> enumerate_processes() {
    std::vector<Process> processes;

    HANDLE snapshot =
        CreateToolhelp32Snapshot(
            SNAPSHOT_FLAGS,
            0
        );

    if (snapshot == INVALID_HANDLE_VALUE) {
        throw std::runtime_error(
            "cannot snapshot the process list"
        );
    }

    PROCESSENTRY32W entry{};
    entry.dwSize = sizeof(PROCESSENTRY32W);

    BOOL success =
        Process32FirstW(
            snapshot,
            &entry
        );

    while (success) {
        Process process;

        process.pid =
            static_cast<std::uint32_t>(
                entry.th32ProcessID
            );

        process.ppid =
            static_cast<std::uint32_t>(
                entry.th32ParentProcessID
            );

        process.threads =
            static_cast<std::uint32_t>(
                entry.cntThreads
            );

        process.name =
            utf8_from_wide(
                entry.szExeFile
            );

        processes.push_back(
            std::move(process)
        );

        success =
            Process32NextW(
                snapshot,
                &entry
            );
    }

    CloseHandle(snapshot);

    return processes;
}


// ============================================================
// Window enumeration
// ============================================================

void enumerate_windows(
    std::unordered_set<std::uint32_t>& app_pids,
    std::unordered_set<std::uint32_t>& hung_pids
) {
    WindowContext context{
        &app_pids,
        &hung_pids
    };

    EnumWindows(
        window_callback,
        reinterpret_cast<LPARAM>(&context)
    );
}


// ============================================================
// Process CPU / memory statistics
// ============================================================

ProcessStats get_process_stats(
    std::uint32_t pid
) {
    ProcessStats result;

    HANDLE process =
        OpenProcess(
            PROCESS_QUERY_LIMITED,
            FALSE,
            static_cast<DWORD>(pid)
        );

    /*
     * Access denied / process already exited.
     *
     * Python version returns:
     *
     * None, None
     */
    if (!process) {
        return result;
    }

    // --------------------------------------------------------
    // CPU
    // --------------------------------------------------------

    FILETIME creation{};
    FILETIME exit_time{};
    FILETIME kernel_time{};
    FILETIME user_time{};

    if (GetProcessTimes(
        process,
        &creation,
        &exit_time,
        &kernel_time,
        &user_time
    )) {
        result.kernel_time =
            filetime_to_seconds(kernel_time);

        result.user_time =
            filetime_to_seconds(user_time);

        result.has_cpu = true;
    }

    // --------------------------------------------------------
    // Memory
    // --------------------------------------------------------

    PROCESS_MEMORY_COUNTERS counters{};

    counters.cb =
        sizeof(PROCESS_MEMORY_COUNTERS);

    if (GetProcessMemoryInfo(
        process,
        &counters,
        sizeof(PROCESS_MEMORY_COUNTERS)
    )) {
        result.working_set =
            static_cast<std::uint64_t>(
                counters.WorkingSetSize
            );

        result.has_memory = true;
    }

    CloseHandle(process);

    return result;
}


// ============================================================
// Total physical RAM
// ============================================================

std::uint64_t get_total_memory() {
    MEMORYSTATUSEX status{};

    status.dwLength =
        sizeof(MEMORYSTATUSEX);

    if (!GlobalMemoryStatusEx(&status)) {
        return 0;
    }

    return static_cast<std::uint64_t>(
        status.ullTotalPhys
    );
}


// ============================================================
// Windows ANSI console support
// ============================================================

bool enable_ansi_console() {
    HANDLE output =
        GetStdHandle(STD_OUTPUT);

    if (
        output == nullptr ||
        output == INVALID_HANDLE_VALUE
    ) {
        return false;
    }

    DWORD mode = 0;

    if (!GetConsoleMode(output, &mode)) {
        return false;
    }

    mode |=
        ENABLE_VIRTUAL_TERMINAL_PROCESSING_FLAG;

    return SetConsoleMode(
        output,
        mode
    ) != FALSE;
}

} // namespace midnight::ps::windows

#endif