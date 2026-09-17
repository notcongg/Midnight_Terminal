#include "ps.hpp"

#include <string>
#include <vector>

#ifdef _WIN32
#define MIDNIGHT_EXPORT __declspec(dllexport)
#else
#define MIDNIGHT_EXPORT __attribute__((visibility("default")))
#endif

extern "C" {

MIDNIGHT_EXPORT int midnight_ps_run(
    int argc,
    const char** argv
) {
    try {
        std::vector<std::string> args;

        if (argc > 0 && argv) {
            args.reserve(static_cast<std::size_t>(argc));

            for (int i = 0; i < argc; ++i) {
                if (argv[i]) {
                    args.emplace_back(argv[i]);
                }
            }
        }

        midnight::ps::execute(args);

        return 0;
    }
    catch (...) {
        return 1;
    }
}

MIDNIGHT_EXPORT int midnight_ps_man() {
    try {
        midnight::ps::manual();
        return 0;
    }
    catch (...) {
        return 1;
    }
}

}