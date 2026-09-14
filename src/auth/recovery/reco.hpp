#pragma once

#include <string>

namespace midnight::auth::recovery {

bool is_available();

bool reset_password(
    const std::string& new_password
);

}