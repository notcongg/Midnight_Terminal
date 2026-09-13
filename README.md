# Midnight Terminal

> An experimental, extensible command-line shell built with Python and C++.

[![License: GPL v3+](https://img.shields.io/badge/License-GPLv3%2B-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C%2B%2B-Native%20Extensions-blue.svg)](https://isocpp.org/)

---

## Overview

Midnight Terminal started as a simple terminal project and evolved into a shell with its own command system, lexer, parser, AST, executor, environment configuration, persistent history, pipelines, redirection, process management, and native process integration.

> It was supposed to be a terminal.
> Then it got a lexer.
> Then a parser.
> Then an AST.
> Then an executor.
>
> We may have gone too far.

---

## Features

| Category       | Features                                                                  |   |                            |
| -------------- | ------------------------------------------------------------------------- | - | -------------------------- |
| **Shell**      | Custom interface, command discovery, aliases, environment configuration   |   |                            |
| **Input**      | Autocomplete, history, multiline input, syntax correction and suggestions |   |                            |
| **Parser**     | Lexer, parser, AST and command executor                                   |   |                            |
| **Execution**  | Pipelines, redirection, `&&`, `                                           |   | `, `;`, external processes |
| **System**     | File management, hardware information, process management                 |   |                            |
| **AI**         | Multiple model tiers, streaming, thinking mode, pipeline input            |   |                            |
| **Extensions** | Extensible command architecture and native C++ integration                |   |                            |
| **Editor**     | Midnight Text Editor (`mte`)                                              |   |                            |

---

## Architecture

```text
Input
  │
  ▼
Syntax Correction
  │
  ▼
Lexer
  │
  ▼
Parser
  │
  ▼
AST
  │
  ▼
Executor
  │
  ├── Built-in Commands
  │       │
  │       ▼
  │   Command Registry
  │
  └── External Commands
          │
          ▼
     Native Extensions
```

Commands are automatically discovered from the command tree, allowing new functionality to be added without maintaining a central command table.

---

## AI

Midnight Terminal includes an `ai` command with multiple model tiers, streaming, optional thinking mode, pipeline input, and request/response logging.

```text
ai "explain this code"

ai --fast "quick question"

ai --medium "analyze this architecture"

ai --deep "find the bug"
```

AI requests and responses are logged locally for debugging and development.

---

## Requirements

* Windows
* Python 3.12+
* Git

---

## Installation

```bash
git clone https://github.com/notcongg/Midnight_Terminal.git
cd Midnight_Terminal
pip install -r requirements.txt
python -m src
```

---

## Project Structure

```text
Midnight_Terminal/
├── src/
│   ├── cmd/
│   │   ├── rootfs/
│   │   └── utils/
│   ├── history/
│   └── data/
├── native/
├── tests/
├── requirements.txt
└── README.md
```

---

## Project Status

Midnight Terminal is under active development.

The core shell architecture, command system, parser, executor, history, pipelines, redirection, external process execution, and native Windows process integration are already implemented.

Advanced process control and additional native shell integration are still being developed.

---

## License

Midnight Terminal is licensed under the **GNU General Public License v3.0 or later**.

See [`LICENSE`](LICENSE) for the complete license text.

---

## About

The project explores:

* Shell architecture
* Lexing and parsing
* Abstract syntax trees
* Command execution
* Filesystem operations
* Windows APIs
* Native C++ integration
* AI integration
* Interactive terminal systems

Midnight Terminal is an ongoing experiment in building a complete and extensible command-line environment from the ground up.