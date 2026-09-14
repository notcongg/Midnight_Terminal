#include "passwd.hpp"

#include <iostream>

#ifdef _WIN32

#include <conio.h>

#else

#include <termios.h>
#include <unistd.h>

#endif

namespace midnight::auth::passwd {

bool read(std::string& password) {
    password.clear();

#ifdef _WIN32

    while (true) {
        const int ch = _getch();

        if (ch == '\r' || ch == '\n') {
            std::cout << '\n';
            break;
        }

        // Backspace
        if (ch == '\b') {
            if (!password.empty()) {
                password.pop_back();
            }

            continue;
        }

        // Printable ASCII
        if (ch >= 32 && ch <= 126) {
            password.push_back(static_cast<char>(ch));
        }
    }

#else

    termios old_term{};
    termios new_term{};

    if (tcgetattr(STDIN_FILENO, &old_term) != 0) {
        return false;
    }

    new_term = old_term;

    // Disable terminal echo.
    new_term.c_lflag &= ~ECHO;

    if (tcsetattr(
            STDIN_FILENO,
            TCSAFLUSH,
            &new_term
        ) != 0) {
        return false;
    }

    const bool success =
        static_cast<bool>(std::getline(std::cin, password));

    // Always restore terminal state.
    tcsetattr(
        STDIN_FILENO,
        TCSAFLUSH,
        &old_term
    );

    std::cout << '\n';

    if (!success) {
        password.clear();
        return false;
    }

#endif

    return !password.empty();
}

}