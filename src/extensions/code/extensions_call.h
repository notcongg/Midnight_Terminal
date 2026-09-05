#pragma once

#include <windows.h>

#ifdef __cplusplus
extern "C"
{
#endif

    struct ExtensionsResult
    {
        DWORD exit_code;
        DWORD error_code;

        char *stdout_data;
        DWORD stdout_size;

        char *stderr_data;
        DWORD stderr_size;
    };

    __declspec(dllexport) int extensions_call(
        const wchar_t *command_line,
        const wchar_t *working_directory,
        const char *stdin_data,
        DWORD stdin_size,
        ExtensionsResult *result);

    __declspec(dllexport) void extensions_free(
        ExtensionsResult *result);

#ifdef __cplusplus
}
#endif
