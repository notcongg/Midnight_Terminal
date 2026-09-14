#include "cpswd.hpp"

#include <iostream>
#include <string>

#include "../../../../auth/binary/hash.hpp"
#include "../../../../auth/passwd/passwd.hpp"
#include "../../../../auth/storage/sto.hpp"

namespace midnight::msup::auth {

bool change_password() {
    std::string stored_hash;

    if (!midnight::auth::storage::read_password_hash(stored_hash)) {
        std::cerr
            << "[!] Midnight superuser password is not configured\n";
        return false;
    }

    std::string current_password;

    std::cout << "Current password: ";
    if (!midnight::auth::passwd::read(current_password)) {
        stored_hash.clear();
        return false;
    }

    if (!midnight::auth::hash::verify_password(
            current_password,
            stored_hash
        )) {
        current_password.clear();
        stored_hash.clear();

        std::cerr << "\n[!] Authentication failed\n";
        return false;
    }

    current_password.clear();
    stored_hash.clear();

    std::string new_password;
    std::string confirmation;
    std::string hashed;

    std::cout << "New password: ";
    if (!midnight::auth::passwd::read(new_password)) {
        return false;
    }

    std::cout << "Confirm password: ";
    if (!midnight::auth::passwd::read(confirmation)) {
        new_password.clear();
        return false;
    }

    if (new_password != confirmation) {
        new_password.clear();
        confirmation.clear();

        std::cerr << "\n[!] Passwords do not match\n";
        return false;
    }

    if (new_password.empty()) {
        new_password.clear();
        confirmation.clear();

        std::cerr << "\n[!] Password cannot be empty\n";
        return false;
    }

    if (!midnight::auth::hash::hash_password(
            new_password,
            hashed
        )) {
        new_password.clear();
        confirmation.clear();

        std::cerr << "\n[!] Failed to create password hash\n";
        return false;
    }

    new_password.clear();
    confirmation.clear();

    if (!midnight::auth::storage::write_password_hash(hashed)) {
        hashed.clear();

        std::cerr << "\n[!] Failed to save password\n";
        return false;
    }

    hashed.clear();

    std::cout
        << "\n[✓] Midnight superuser password changed\n";

    return true;
}

}