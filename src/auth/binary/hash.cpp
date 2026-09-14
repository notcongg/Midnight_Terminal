#include "hash.hpp"

#include <sodium.h>

namespace midnight::auth::hash {

bool hash_password(
    const std::string& password,
    std::string& hashed
) {
    if (password.empty()) {
        return false;
    }

    if (sodium_init() < 0) {
        return false;
    }

    char output[crypto_pwhash_STRBYTES];

    if (crypto_pwhash_str(
            output,
            password.c_str(),
            password.size(),
            crypto_pwhash_OPSLIMIT_INTERACTIVE,
            crypto_pwhash_MEMLIMIT_INTERACTIVE
        ) != 0) {
        return false;
    }

    hashed = output;

    return true;
}

bool verify_password(
    const std::string& password,
    const std::string& hashed
) {
    if (password.empty() || hashed.empty()) {
        return false;
    }

    if (sodium_init() < 0) {
        return false;
    }

    return crypto_pwhash_str_verify(
        hashed.c_str(),
        password.c_str(),
        password.size()
    ) == 0;
}

}