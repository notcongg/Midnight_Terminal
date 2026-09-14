#include "msup.hpp"
#include "state/state.hpp"

extern "C" {

int midnight_msup_execute(int argc, char** argv) {
    return midnight::msup::execute(argc, argv);
}

int midnight_msup_is_active() {
    return midnight::msup::state::is_active() ? 1 : 0;
}

int midnight_msup_deactivate() {
    if (!midnight::msup::state::is_active()) {
        return 0;
    }

    midnight::msup::state::deactivate();
    return 1;
}

}