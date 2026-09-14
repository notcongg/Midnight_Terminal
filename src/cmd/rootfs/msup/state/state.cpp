#include "state.hpp"

namespace midnight::msup::state {

namespace {
    bool active = false;
}

bool is_active() {
    return active;
}

void activate() {
    active = true;
}

void deactivate() {
    active = false;
}

}