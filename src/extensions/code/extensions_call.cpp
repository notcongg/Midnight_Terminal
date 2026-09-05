#include "extensions_call.h"

#include <windows.h>

#include <cstring>
#include <thread>
#include <vector>

// ============================================================
// INTERNAL HELPERS
// ============================================================

static void read_pipe(
    HANDLE pipe,
    std::vector<char> &output)
{
    constexpr DWORD BUFFER_SIZE = 4096;

    char buffer[BUFFER_SIZE];
    DWORD bytes_read = 0;

    while (true)
    {
        BOOL success = ReadFile(
            pipe,
            buffer,
            BUFFER_SIZE,
            &bytes_read,
            nullptr);

        if (!success || bytes_read == 0)
        {
            break;
        }

        output.insert(
            output.end(),
            buffer,
            buffer + bytes_read);
    }
}

// ============================================================
// EXTENSIONS CALL
// ============================================================

int extensions_call(
    const wchar_t *command_line,
    const wchar_t *working_directory,
    const char *stdin_data,
    DWORD stdin_size,
    ExtensionsResult *result)
{
    if (result == nullptr)
    {
        return 0;
    }

    // --------------------------------------------------------
    // RESET RESULT
    // --------------------------------------------------------

    result->exit_code = 0;
    result->error_code = ERROR_SUCCESS;

    result->stdout_data = nullptr;
    result->stdout_size = 0;

    result->stderr_data = nullptr;
    result->stderr_size = 0;

    if (command_line == nullptr)
    {
        result->error_code = ERROR_INVALID_PARAMETER;
        return 0;
    }

    // --------------------------------------------------------
    // SECURITY ATTRIBUTES
    // --------------------------------------------------------

    SECURITY_ATTRIBUTES security_attributes{};

    security_attributes.nLength =
        sizeof(SECURITY_ATTRIBUTES);

    security_attributes.bInheritHandle = TRUE;

    security_attributes.lpSecurityDescriptor =
        nullptr;

    // --------------------------------------------------------
    // STDIN PIPE
    // --------------------------------------------------------

    HANDLE stdin_read = nullptr;
    HANDLE stdin_write = nullptr;

    if (!CreatePipe(
            &stdin_read,
            &stdin_write,
            &security_attributes,
            0))
    {
        result->error_code = GetLastError();
        return 0;
    }

    // Parent writes -> child reads.
    //
    // The child must inherit only the read side.

    if (!SetHandleInformation(
            stdin_write,
            HANDLE_FLAG_INHERIT,
            0))
    {
        result->error_code = GetLastError();

        CloseHandle(stdin_read);
        CloseHandle(stdin_write);

        return 0;
    }

    // --------------------------------------------------------
    // STDOUT PIPE
    // --------------------------------------------------------

    HANDLE stdout_read = nullptr;
    HANDLE stdout_write = nullptr;

    if (!CreatePipe(
            &stdout_read,
            &stdout_write,
            &security_attributes,
            0))
    {
        result->error_code = GetLastError();

        CloseHandle(stdin_read);
        CloseHandle(stdin_write);

        return 0;
    }

    if (!SetHandleInformation(
            stdout_read,
            HANDLE_FLAG_INHERIT,
            0))
    {
        result->error_code = GetLastError();

        CloseHandle(stdin_read);
        CloseHandle(stdin_write);

        CloseHandle(stdout_read);
        CloseHandle(stdout_write);

        return 0;
    }

    // --------------------------------------------------------
    // STDERR PIPE
    // --------------------------------------------------------

    HANDLE stderr_read = nullptr;
    HANDLE stderr_write = nullptr;

    if (!CreatePipe(
            &stderr_read,
            &stderr_write,
            &security_attributes,
            0))
    {
        result->error_code = GetLastError();

        CloseHandle(stdin_read);
        CloseHandle(stdin_write);

        CloseHandle(stdout_read);
        CloseHandle(stdout_write);

        return 0;
    }

    if (!SetHandleInformation(
            stderr_read,
            HANDLE_FLAG_INHERIT,
            0))
    {
        result->error_code = GetLastError();

        CloseHandle(stdin_read);
        CloseHandle(stdin_write);

        CloseHandle(stdout_read);
        CloseHandle(stdout_write);

        CloseHandle(stderr_read);
        CloseHandle(stderr_write);

        return 0;
    }

    // --------------------------------------------------------
    // STARTUP INFO
    // --------------------------------------------------------

    STARTUPINFOW startup_info{};

    startup_info.cb =
        sizeof(STARTUPINFOW);

    startup_info.dwFlags |=
        STARTF_USESTDHANDLES;

    startup_info.hStdInput =
        stdin_read;

    startup_info.hStdOutput =
        stdout_write;

    startup_info.hStdError =
        stderr_write;

    // --------------------------------------------------------
    // PROCESS INFO
    // --------------------------------------------------------

    PROCESS_INFORMATION process_info{};

    // CreateProcessW requires mutable command line.
    const size_t command_length =
        wcslen(command_line);

    std::vector<wchar_t> command_buffer(
        command_length + 1);

    std::memcpy(
        command_buffer.data(),
        command_line,
        (command_length + 1) * sizeof(wchar_t));

    // --------------------------------------------------------
    // CREATE PROCESS
    // --------------------------------------------------------

    BOOL created = CreateProcessW(
        nullptr,
        command_buffer.data(),
        nullptr,
        nullptr,
        TRUE,
        0,
        nullptr,
        working_directory,
        &startup_info,
        &process_info);

    // Parent does not need child-side handles.

    CloseHandle(stdin_read);
    stdin_read = nullptr;

    CloseHandle(stdout_write);
    stdout_write = nullptr;

    CloseHandle(stderr_write);
    stderr_write = nullptr;

    if (!created)
    {
        result->error_code =
            GetLastError();

        CloseHandle(stdin_write);
        CloseHandle(stdout_read);
        CloseHandle(stderr_read);

        return 0;
    }

    // --------------------------------------------------------
    // WRITE STDIN
    // --------------------------------------------------------

    std::thread stdin_thread(
        [stdin_write, stdin_data, stdin_size]()
        {
            if (
                stdin_data != nullptr &&
                stdin_size > 0)
            {
                DWORD total_written = 0;

                while (total_written < stdin_size)
                {
                    DWORD bytes_written = 0;

                    DWORD remaining =
                        stdin_size - total_written;

                    BOOL success = WriteFile(
                        stdin_write,
                        stdin_data + total_written,
                        remaining,
                        &bytes_written,
                        nullptr);

                    if (!success || bytes_written == 0)
                    {
                        break;
                    }

                    total_written += bytes_written;
                }
            }

            // VERY IMPORTANT:
            // closing the write end gives the child EOF.

            CloseHandle(stdin_write);
        });

    // --------------------------------------------------------
    // READ OUTPUT CONCURRENTLY
    // --------------------------------------------------------

    std::vector<char> stdout_buffer;
    std::vector<char> stderr_buffer;

    std::thread stdout_thread(
        read_pipe,
        stdout_read,
        std::ref(stdout_buffer));

    std::thread stderr_thread(
        read_pipe,
        stderr_read,
        std::ref(stderr_buffer));

    // --------------------------------------------------------
    // WAIT FOR PROCESS
    // --------------------------------------------------------

    WaitForSingleObject(
        process_info.hProcess,
        INFINITE);

    // --------------------------------------------------------
    // GET EXIT CODE
    // --------------------------------------------------------

    DWORD exit_code = 0;

    if (!GetExitCodeProcess(
            process_info.hProcess,
            &exit_code))
    {
        result->error_code =
            GetLastError();
    }

    result->exit_code =
        exit_code;

    // --------------------------------------------------------
    // WAIT FOR THREADS
    // --------------------------------------------------------

    stdin_thread.join();
    stdout_thread.join();
    stderr_thread.join();

    // --------------------------------------------------------
    // CLOSE HANDLES
    // --------------------------------------------------------

    CloseHandle(stdout_read);
    CloseHandle(stderr_read);

    CloseHandle(process_info.hThread);
    CloseHandle(process_info.hProcess);

    // --------------------------------------------------------
    // COPY STDOUT
    // --------------------------------------------------------

    if (!stdout_buffer.empty())
    {
        result->stdout_size =
            static_cast<DWORD>(
                stdout_buffer.size());

        result->stdout_data =
            static_cast<char *>(
                HeapAlloc(
                    GetProcessHeap(),
                    0,
                    stdout_buffer.size() + 1));

        if (result->stdout_data == nullptr)
        {
            result->error_code =
                ERROR_NOT_ENOUGH_MEMORY;

            extensions_free(result);

            return 0;
        }

        std::memcpy(
            result->stdout_data,
            stdout_buffer.data(),
            stdout_buffer.size());

        result->stdout_data[stdout_buffer.size()] = '\0';
    }

    // --------------------------------------------------------
    // COPY STDERR
    // --------------------------------------------------------

    if (!stderr_buffer.empty())
    {
        result->stderr_size =
            static_cast<DWORD>(
                stderr_buffer.size());

        result->stderr_data =
            static_cast<char *>(
                HeapAlloc(
                    GetProcessHeap(),
                    0,
                    stderr_buffer.size() + 1));

        if (result->stderr_data == nullptr)
        {
            result->error_code =
                ERROR_NOT_ENOUGH_MEMORY;

            extensions_free(result);

            return 0;
        }

        std::memcpy(
            result->stderr_data,
            stderr_buffer.data(),
            stderr_buffer.size());

        result->stderr_data[stderr_buffer.size()] = '\0';
    }

    return 1;
}

// ============================================================
// FREE RESULT
// ============================================================

void extensions_free(
    ExtensionsResult *result)
{
    if (result == nullptr)
    {
        return;
    }

    if (result->stdout_data != nullptr)
    {
        HeapFree(
            GetProcessHeap(),
            0,
            result->stdout_data);

        result->stdout_data = nullptr;
    }

    if (result->stderr_data != nullptr)
    {
        HeapFree(
            GetProcessHeap(),
            0,
            result->stderr_data);

        result->stderr_data = nullptr;
    }

    result->stdout_size = 0;
    result->stderr_size = 0;
}
