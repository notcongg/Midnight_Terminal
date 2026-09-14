#include "reco.hpp"

namespace midnight::auth::recovery {

bool is_available() {
    // Recovery mechanism is not implemented yet.
    return false;
}

bool reset_password(
    const std::string& new_password
) {
    // Do not allow password reset until a secure
    // recovery mechanism has been implemented.
    (void)new_password;

    return false;
}

}