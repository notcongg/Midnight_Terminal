#pragma once

#include <string>

namespace midnight::auth::hash {

bool hash_password(
    const std::string& password,
    std::string& hashed
);

bool verify_password(
    const std::string& password,
    const std::string& hashed
);

}