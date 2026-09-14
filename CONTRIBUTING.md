<p align="center">
  <img src="logo/icon.png" alt="Midnight Terminal" width="96">
</p>

<h1 align="center">Contributing to Midnight Terminal</h1>

<p align="center">
  Help build an experimental, extensible command-line shell for the modern era.
</p>

<p align="center">
  <a href="../README.md">README</a>
  ·
  <a href="../LICENSE">License</a>
  ·
  <a href="https://github.com/notcongg/Midnight_Terminal/issues">Issues</a>
  ·
  <a href="https://github.com/notcongg/Midnight_Terminal/pulls">Pull Requests</a>
</p>

---

Thank you for your interest in contributing to **Midnight Terminal**!

Midnight Terminal is an open-source, extensible command-line shell built with Python and C++. Contributions of all kinds are welcome, including bug fixes, improvements, new commands, documentation, tests, and new ideas.

## Getting Started

### 1. Fork the repository

Create your own fork of the Midnight Terminal repository on GitHub.

### 2. Clone your fork

```bash
git clone https://github.com/<your-username>/Midnight_Terminal.git
cd Midnight_Terminal
```

### 3. Create a branch

Create a dedicated branch for your change:

```bash
git checkout -b feat/your-feature
```

### 4. Make your changes

Keep changes focused and consistent with the existing architecture.

### 5. Test your changes

Run the relevant tests before submitting your changes:

```bash
pytest
```

If your changes affect native C++ components, build and test those components as well.

### 6. Commit your changes

Use a short, descriptive commit message following the project's commit conventions.

### 7. Push your branch

```bash
git push -u origin feat/your-feature
```

### 8. Open a Pull Request

Open a Pull Request against the `main` branch and describe what you changed and why.

---

## Branch Naming

Use clear and descriptive branch names.

```text
feat/<feature>
fix/<bug>
refactor/<area>
docs/<topic>
test/<topic>
build/<topic>
chore/<topic>
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

Keep branch names short and focused on the purpose of the change.

---

## Commit Messages

Keep commit messages short, descriptive, and consistent.

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
build: update native dependencies
```

### Common commit types

| Type       | Purpose                                    |
| ---------- | ------------------------------------------ |
| `feat`     | Add a new feature                          |
| `fix`      | Fix a bug                                  |
| `refactor` | Restructure code without changing behavior |
| `docs`     | Documentation changes                      |
| `test`     | Add or update tests                        |
| `build`    | Build system or dependency changes         |
| `chore`    | Maintenance changes                        |

---

## Code Style

Please keep code:

* Readable
* Simple
* Modular
* Consistent with the existing project
* Properly documented when necessary

Avoid unnecessary abstraction and complexity.

### Python

Follow normal Python conventions:

* Use clear and descriptive names.
* Keep functions and modules focused.
* Avoid unnecessary global state.
* Prefer simple solutions over clever ones.
* Preserve existing behavior unless a change is intentional.

### C++

For native C++ components:

* Keep platform-specific code isolated where possible.
* Prefer clear ownership and resource management.
* Keep interfaces small and predictable.
* Avoid introducing unnecessary dependencies.

When modifying existing code, **preserve working behavior unless the change specifically requires otherwise.**

---

## Adding Commands

Midnight Terminal uses an extensible command system.

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

A command should contain the logic required to implement that command rather than unrelated shell functionality.

Avoid placing command-specific behavior directly inside the command registry or shell executor unless the architecture requires it.

### New command checklist

Before submitting a new command:

* [ ] Command behavior is clearly defined.
* [ ] Command-specific logic is isolated.
* [ ] Existing commands are not unnecessarily modified.
* [ ] Relevant tests are included.
* [ ] Documentation is updated when appropriate.
* [ ] Windows/Linux behavior is considered where applicable.

---

## Pull Requests

Before opening a Pull Request:

* Make sure the project still runs.
* Run the relevant tests.
* Keep the Pull Request focused.
* Explain what changed and why.
* Mention important implementation details.
* Mention known limitations or platform-specific behavior.
* Update documentation when necessary.

A Pull Request may be reviewed, requested for changes, rejected, or merged by project maintainers.

Please avoid combining unrelated features or fixes into the same Pull Request.

---

## Bug Reports

When reporting a bug, include as much relevant information as possible.

Please provide:

* What happened
* What you expected to happen
* Steps to reproduce the issue
* Relevant error messages or logs
* Operating system
* Python version
* Midnight Terminal version or commit
* A minimal reproducible example, when possible

A good bug report makes the problem reproducible.

---

## Feature Requests

Feature requests are welcome.

Please explain:

* What the feature does
* Why it would be useful
* How you expect it to work
* Any relevant examples
* Potential compatibility or architectural concerns

For new shell commands, include the intended syntax and expected behavior.

For larger architectural changes, opening a discussion before implementation may help avoid duplicated or conflicting work.

---

## Documentation

Documentation improvements are always welcome.

This includes:

* README improvements
* Installation instructions
* Command documentation
* Architecture documentation
* Examples
* Tutorials
* Typo and grammar fixes

Documentation changes should remain accurate to the current implementation.

---

## Testing

Before submitting a Pull Request, run the tests relevant to your changes.

For Python components:

```bash
pytest
```

For native C++ components, use the project's configured build and test system.

If a change introduces new behavior, add tests where practical.

---

## License

Midnight Terminal is distributed under the **GNU General Public License v3.0 or later**.

By contributing to this project, you agree that your contributions may be distributed as part of Midnight Terminal under the project's applicable license.

See [`LICENSE`](LICENSE) for the full license text.

---

## Code of Conduct

Please be respectful to other contributors.

Harassment, discrimination, personal attacks, and intentionally disruptive behavior are not welcome.

Keep discussions focused on the project and its technical goals.

---

Thank you for contributing to **Midnight Terminal**.