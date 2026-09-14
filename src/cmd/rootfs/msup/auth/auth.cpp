#include "auth.hpp"

#include <string>

#include "../../../auth/binary/hash.hpp"
#include "../../../auth/passwd/passwd.hpp"
#include "../../../auth/storage/sto.hpp"

namespace midnight::msup::auth {

bool authenticate() {
    std::string password;
    std::string stored_hash;

    if (!midnight::auth::passwd::read(password)) {
        return false;
    }

    if (!midnight::auth::storage::read_password_hash(stored_hash)) {
        password.clear();
        return false;
    }

    const bool authenticated =
        midnight::auth::hash::verify_password(password, stored_hash);

    password.clear();
    stored_hash.clear();

    return authenticated;
}

}