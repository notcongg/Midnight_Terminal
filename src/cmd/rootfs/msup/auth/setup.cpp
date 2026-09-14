#include "setup.hpp"

#include <iostream>
#include <string>

#include "../../../../auth/binary/hash.hpp"
#include "../../../../auth/passwd/passwd.hpp"
#include "../../../../auth/storage/sto.hpp"
namespace midnight::msup::auth {

bool setup_password() {
    std::string existing_hash;

    if (midnight::auth::storage::read_password_hash(existing_hash)) {
        existing_hash.clear();

        std::cerr
            << "[!] Midnight superuser password is already configured\n";

        return false;
    }

    existing_hash.clear();

    std::string password;
    std::string confirmation;
    std::string hashed;

    std::cout << "Midnight SUPERUserPermissions setup\n\n";

    std::cout << "Create password: ";
    if (!midnight::auth::passwd::read(password)) {
        return false;
    }

    std::cout << "Confirm password: ";
    if (!midnight::auth::passwd::read(confirmation)) {
        password.clear();
        return false;
    }

    if (password != confirmation) {
        password.clear();
        confirmation.clear();

        std::cerr << "\n[!] Passwords do not match\n";
        return false;
    }

    if (password.empty()) {
        password.clear();
        confirmation.clear();

        std::cerr << "\n[!] Password cannot be empty\n";
        return false;
    }

    if (!midnight::auth::hash::hash_password(
            password,
            hashed
        )) {
        password.clear();
        confirmation.clear();

        std::cerr << "\n[!] Failed to create password hash\n";
        return false;
    }

    password.clear();
    confirmation.clear();

    if (!midnight::auth::storage::write_password_hash(hashed)) {
        hashed.clear();

        std::cerr
            << "\n[!] Failed to save password\n";

        return false;
    }

    hashed.clear();

    std::cout
        << "\n[✓] Midnight superuser password configured\n";

    return true;
}

}