from __future__ import annotations

import ctypes
import os
from pathlib import Path


# ============================================================
# EXTENSIONS RESULT
# ============================================================

class ExtensionsResult(ctypes.Structure):
    _fields_ = [
        ("exit_code", ctypes.c_uint32),
        ("error_code", ctypes.c_uint32),

        ("stdout_data", ctypes.POINTER(ctypes.c_char)),
        ("stdout_size", ctypes.c_uint32),

        ("stderr_data", ctypes.POINTER(ctypes.c_char)),
        ("stderr_size", ctypes.c_uint32),
    ]


# ============================================================
# EXTENSIONS
# ============================================================

class Extensions:
    """
    Python wrapper around Midnight Terminal's
    native process execution DLL.
    """

    def __init__(self) -> None:
        # ----------------------------------------------------
        # DLL DIRECTORY
        # ----------------------------------------------------

        self.dll_dir = (
            Path(__file__).resolve().parent / "dll"
        )

        self.dll_path = (
            self.dll_dir / "midnight_extensions_call.dll"
        )

        if not self.dll_path.exists():
            raise FileNotFoundError(
                "Midnight Extensions DLL not found: "
                f"{self.dll_path}"
            )

        # ----------------------------------------------------
        # WINDOWS DLL SEARCH PATH
        # ----------------------------------------------------

        self._dll_directory_handle = (
            os.add_dll_directory(
                str(self.dll_dir)
            )
        )

        # ----------------------------------------------------
        # LOAD DLL
        # ----------------------------------------------------

        self.dll = ctypes.CDLL(
            str(self.dll_path)
        )

        # ----------------------------------------------------
        # extensions_call
        #
        # C signature:
        #
        # int extensions_call(
        #     const wchar_t* command_line,
        #     const wchar_t* working_directory,
        #     const char* stdin_data,
        #     DWORD stdin_size,
        #     ExtensionsResult* result
        # );
        # ----------------------------------------------------

        self.dll.extensions_call.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.POINTER(ctypes.c_char),
            ctypes.c_uint32,
            ctypes.POINTER(ExtensionsResult),
        ]

        self.dll.extensions_call.restype = ctypes.c_int

        # ----------------------------------------------------
        # extensions_free
        # ----------------------------------------------------

        self.dll.extensions_free.argtypes = [
            ctypes.POINTER(ExtensionsResult),
        ]

        self.dll.extensions_free.restype = None

    # ========================================================
    # CALL
    # ========================================================

    def call(
        self,
        command_line: str,
        working_directory: str | None = None,
        stdin_data: bytes | None = None,
    ) -> dict:
        """
        Execute an external process.

        Returns:
            {
                "success": bool,
                "exit_code": int,
                "error_code": int,
                "stdout": bytes,
                "stderr": bytes,
            }

        stdin_data:
            Bytes written to the child process stdin.
        """

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not isinstance(command_line, str):
            raise TypeError(
                "command_line must be a string"
            )

        if not command_line:
            raise ValueError(
                "command_line cannot be empty"
            )

        if stdin_data is None:
            stdin_data = b""

        if not isinstance(stdin_data, bytes):
            raise TypeError(
                "stdin_data must be bytes or None"
            )

        # ----------------------------------------------------
        # KEEP BUFFER ALIVE
        # ----------------------------------------------------

        stdin_buffer = (
            ctypes.create_string_buffer(
                stdin_data
            )
            if stdin_data
            else None
        )

        stdin_pointer = (
            ctypes.cast(
                stdin_buffer,
                ctypes.POINTER(ctypes.c_char),
            )
            if stdin_buffer is not None
            else None
        )

        stdin_size = len(stdin_data)

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        result = ExtensionsResult()

        # ----------------------------------------------------
        # CALL NATIVE DLL
        # ----------------------------------------------------

        success = self.dll.extensions_call(
            command_line,
            working_directory,
            stdin_pointer,
            ctypes.c_uint32(stdin_size),
            ctypes.byref(result),
        )

        # ----------------------------------------------------
        # READ OUTPUT
        # ----------------------------------------------------

        stdout = b""
        stderr = b""

        try:
            if (
                result.stdout_data
                and result.stdout_size > 0
            ):
                stdout = ctypes.string_at(
                    result.stdout_data,
                    result.stdout_size,
                )

            if (
                result.stderr_data
                and result.stderr_size > 0
            ):
                stderr = ctypes.string_at(
                    result.stderr_data,
                    result.stderr_size,
                )

            return {
                "success": bool(success),
                "exit_code": int(
                    result.exit_code
                ),
                "error_code": int(
                    result.error_code
                ),
                "stdout": stdout,
                "stderr": stderr,
            }

        finally:
            # ------------------------------------------------
            # FREE NATIVE MEMORY
            # ------------------------------------------------

            self.dll.extensions_free(
                ctypes.byref(result)
            )

    # ========================================================
    # CALL TEXT
    # ========================================================

    def call_text(
        self,
        command_line: str,
        working_directory: str | None = None,
        stdin_data: str | None = None,
        encoding: str = "utf-8",
    ) -> dict:
        """
        Execute a process and decode stdout/stderr to text.
        """

        stdin_bytes = (
            (stdin_data or "").encode(
                encoding,
                errors="replace",
            )
        )

        result = self.call(
            command_line,
            working_directory,
            stdin_bytes,
        )

        result["stdout"] = result["stdout"].decode(
            encoding,
            errors="replace",
        )

        result["stderr"] = result["stderr"].decode(
            encoding,
            errors="replace",
        )

        return result

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self) -> None:
        """
        Release the DLL directory handle.
        """

        if self._dll_directory_handle is not None:
            self._dll_directory_handle.close()
            self._dll_directory_handle = None

    # ========================================================
    # CONTEXT MANAGER
    # ========================================================

    def __enter__(self) -> Extensions:
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
