#include "is_avail.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>

#ifndef _WIN32
#include <sys/stat.h>
#endif

namespace fs = std::filesystem;

namespace midnight::auth {

static fs::path get_password_file_path() {
#ifdef _WIN32
    const char* appdata = std::getenv("APPDATA");

    if (appdata) {
        return fs::path(appdata) / "Midnight" / ".midps";
    }

    const char* userprofile = std::getenv("USERPROFILE");

    if (userprofile) {
        return fs::path(userprofile) / "AppData" / "Roaming"
             / "Midnight" / ".midps";
    }

    return {};
#else
    const char* home = std::getenv("HOME");

    if (!home) {
        return {};
    }

    return fs::path(home) / ".config" / "midnight" / ".midps";
#endif
}

bool is_password_file_available() {
    const fs::path password_file = get_password_file_path();

    if (password_file.empty()) {
        return false;
    }

    // .midps already exists.
    if (fs::exists(password_file)) {
        return fs::is_regular_file(password_file);
    }

    std::error_code ec;

    // Create ~/.config/midnight/
    fs::create_directories(password_file.parent_path(), ec);

    if (ec) {
        return false;
    }

    // Create the password file.
    std::ofstream file(password_file);

    if (!file.is_open()) {
        return false;
    }

    file.close();

#ifndef _WIN32
    // Owner: read + write
    // Group/Others: no permissions
    if (::chmod(password_file.c_str(), S_IRUSR | S_IWUSR) != 0) {
        std::error_code remove_ec;
        fs::remove(password_file, remove_ec);
        return false;
    }
#endif

    return true;
}

}