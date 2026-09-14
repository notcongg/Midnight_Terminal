#include "msup.hpp"

#include <iostream>
#include <string>

#include "auth/auth.hpp"
#include "auth/setup.hpp"
#include "auth/cpswd.hpp"
#include "auth/secrules/secrules.hpp"
#include "state/state.hpp"

namespace midnight::msup {

int execute(int argc, char** argv) {
    if (argc < 2) {
        std::cerr
            << "Usage: msup -s | -cpswd | -a | -e | -status | -h | -v\n";
        return 1;
    }

    const std::string option = argv[1];

    // ========================================================
    // SETUP
    // ========================================================

    if (option == "-s") {
        return auth::setup_password() ? 0 : 1;
    }

    // ========================================================
    // CHANGE PASSWORD
    // ========================================================

    if (option == "-cpswd") {
        return auth::change_password() ? 0 : 1;
    }

    // ========================================================
    // ACTIVATE
    // ========================================================

    if (option == "-a") {
        if (!secrules::can_activate()) {
            std::cerr
                << "[!] Cannot activate Midnight superuser\n";
            return 1;
        }

        if (!auth::authenticate()) {
            std::cerr
                << "\n[!] Authentication failed\n";
            return 1;
        }

        state::activate();

        std::cout
            << "\n[✓] Midnight superuser activated\n";

        return 0;
    }

    // ========================================================
    // DEACTIVATE
    // ========================================================

    if (option == "-e") {
        if (!state::is_active()) {
            std::cerr
                << "[!] Midnight superuser is not active\n";
            return 1;
        }

        state::deactivate();

        std::cout
            << "[✓] Midnight superuser deactivated\n";

        return 0;
    }

    // ========================================================
    // STATUS
    // ========================================================

    if (option == "-status") {
        if (state::is_active()) {
            std::cout
                << "[✓] Midnight superuser active\n";
        } else {
            std::cout
                << "[ ] Midnight superuser inactive\n";
        }

        return 0;
    }

    // ========================================================
    // HELP
    // ========================================================

    if (option == "-h") {
        std::cout
            << "Midnight SUPERUserPermissions\n\n"
            << "Usage:\n"
            << "  msup -s          Setup password\n"
            << "  msup -cpswd      Change password\n"
            << "  msup -a          Activate MSUP\n"
            << "  msup -e          Deactivate MSUP\n"
            << "  msup -status     Show current status\n"
            << "  msup -h          Show help\n"
            << "  msup -v          Show version\n";

        return 0;
    }

    // ========================================================
    // VERSION
    // ========================================================

    if (option == "-v") {
        std::cout
            << "Midnight SUPERUserPermissions [Ver. 1.000.0001]\n"
            << "Copyright (C) 2026 Congg\n";

        return 0;
    }

    // ========================================================
    // UNKNOWN OPTION
    // ========================================================

    std::cerr
        << "Unknown option: "
        << option
        << '\n';

    return 1;
}

}