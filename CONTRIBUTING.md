# Contributing to Midnight Terminal

Thank you for your interest in contributing to Midnight Terminal!

Midnight Terminal is an open-source terminal project developed by Congg and contributors. Contributions, improvements, bug fixes, and new ideas are welcome.

## Getting Started

1. Fork the repository.
2. Clone your fork:

```bash
git clone <your-fork-url>
cd midnight_terminal
```

3. Create a new branch:

```bash
git checkout -b feat/your-feature
```

4. Make your changes.
5. Test your changes.
6. Commit your changes.
7. Push your branch:

```bash
git push -u origin feat/your-feature
```

8. Open a Pull Request.

## Branch Naming

Use clear branch names:

```text
feat/<feature>
fix/<bug>
refactor/<area>
docs/<topic>
test/<topic>
```

Examples:

```text
feat/parser
feat/grep-command
fix/mv-windows-path
refactor/command-registry
docs/contributing
test/parser
```

## Commit Messages

Keep commit messages short and descriptive.

Recommended format:

```text
type: description
```

Examples:

```text
feat: add grep command
fix: handle paths with spaces
refactor: improve command registry
docs: update installation guide
test: add parser tests
```

Common commit types:

* `feat` — new feature
* `fix` — bug fix
* `refactor` — code restructuring without changing behavior
* `docs` — documentation changes
* `test` — tests
* `build` — build or dependency changes
* `chore` — maintenance

## Code Style

Please keep code:

* Readable
* Simple
* Modular
* Consistent with the existing project
* Properly documented when necessary

Avoid unnecessary complexity.

For Python code, follow normal Python conventions and use clear names for functions, variables, and modules.

## Commands

When adding a new command, keep command-specific logic inside its own module.

For example:

```text
src/
└── cmd/
    └── rootfs/
        ├── cd.py
        ├── ls.py
        ├── mv.py
        └── grep.py
```

Do not put unrelated command logic into the command registry or shell executor.

## Pull Requests

Before opening a Pull Request:

* Make sure the project still runs.
* Test the affected functionality.
* Keep the PR focused on one feature or fix when possible.
* Explain what changed and why.
* Mention any known limitations.

A Pull Request may be reviewed, modified, rejected, or merged by project maintainers.

## Bug Reports

When reporting a bug, include:

* What happened
* What you expected to happen
* Steps to reproduce the issue
* Relevant error messages
* Operating system
* Python version
* Midnight Terminal version or commit

A minimal reproducible example is highly appreciated.

## Feature Requests

Feature requests are welcome.

Please explain:

* What the feature does
* Why it would be useful
* How you expect it to work
* Any relevant examples

For new shell commands, explain the intended syntax and behavior.

## License

Midnight Terminal is distributed under the **GNU General Public License v3.0 or later**.

By contributing to this project, you agree that your contributions may be distributed as part of the project under the project's applicable license.

See [`LICENSE`](LICENSE) for the full license text.

## Code of Conduct

Please be respectful to other contributors.

Harassment, discrimination, personal attacks, and intentionally disruptive behavior are not welcome.

Keep discussions focused on the project and its technical goals.

---

Thank you for contributing to Midnight Terminal. 🌙
