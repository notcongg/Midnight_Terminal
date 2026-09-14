#include "auth.hpp"

#include "binary/hash.hpp"
#include "storage/sto.hpp"

namespace midnight::auth {

bool authenticate(const std::string& password) {
    std::string stored_hash;

    if (!storage::read_password_hash(stored_hash)) {
        return false;
    }

    return hash::verify_password(password, stored_hash);
}

}