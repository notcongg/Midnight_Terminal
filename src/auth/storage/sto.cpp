#include "sto.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>

#ifndef _WIN32
#include <sys/stat.h>
#endif

namespace fs = std::filesystem;

namespace midnight::auth::storage {

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

bool read_password_hash(std::string& hash) {
    const fs::path password_file = get_password_file_path();

    if (password_file.empty() ||
        !fs::exists(password_file) ||
        !fs::is_regular_file(password_file)) {
        return false;
    }

    std::ifstream file(password_file);

    if (!file.is_open()) {
        return false;
    }

    std::getline(file, hash);

    return !hash.empty();
}

bool write_password_hash(const std::string& hash) {
    if (hash.empty()) {
        return false;
    }

    const fs::path password_file = get_password_file_path();

    if (password_file.empty()) {
        return false;
    }

    std::ofstream file(
        password_file,
        std::ios::trunc
    );

    if (!file.is_open()) {
        return false;
    }

    file << hash;
    file.flush();

    if (!file.good()) {
        return false;
    }

    file.close();

#ifndef _WIN32
    // Keep .midps owner-readable and owner-writable only.
    if (::chmod(password_file.c_str(), S_IRUSR | S_IWUSR) != 0) {
        return false;
    }
#endif

    return true;
}

}