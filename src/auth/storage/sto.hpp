#pragma once

#include <string>

namespace midnight::auth::storage {

bool read_password_hash(std::string& hash);

bool write_password_hash(const std::string& hash);

}