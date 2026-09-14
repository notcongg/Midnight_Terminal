#include "secrules.hpp"
#include "../../state/state.hpp"

namespace midnight::msup::secrules {

bool can_activate() {
    return !midnight::msup::state::is_active();
}

}