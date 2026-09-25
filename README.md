<p align="center">
  <img src="logo/banner.png" alt="Midnight Terminal">
</p>

<p align="center">
  An experimental, extensible command-line shell built with Python and C++.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-GPLv3%2B-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/C%2B%2B-Native%20Extensions-blue.svg" alt="C++">
  <img src="https://img.shields.io/badge/ChatGPT-412991?logo=openai&logoColor=white" alt="ChatGPT">
</p>

## Overview
> [BEFORE READ ANYTHING, PLEASE KNOW THIS IS A HOBBY PROJECT TO TEST CAN ME AND CHATGPT MAKE A SHELL.]
> [THIS IS WROTE BY CHATGPT TOO.]

Midnight Terminal started as a simple terminal project and evolved into a full command-line shell with its own command system, parser, executor, environment, history, pipelines, redirection, process management, AI integration, and native C++ extensions.

> It was supposed to be a terminal.
> Then it got a lexer.
> Then a parser.
> Then an AST.
> Then an executor.
>
> We may have gone too far.

## Features

* **Shell** — Command discovery, aliases, environment configuration, history, and interactive input
* **Parser** — Lexer, parser, AST, and executor
* **Execution** — Pipelines, redirection, `&&`, `||`, `;`, and external commands
* **System** — File management, processes, and hardware information
* **AI** — Multiple model tiers, streaming, thinking mode, and pipeline input
* **Extensions** — Extensible command system and native C++ integration
* **Editor** — Midnight Text Editor (`mte`)

## Architecture

```text
Input
  ↓
Syntax Correction
  ↓
Lexer
  ↓
Parser
  ↓
AST
  ↓
Executor
  ├── Built-in Commands
  │      ↓
  │   Command Registry
  │
  └── External Commands
         ↓
      Native Extensions
```

Commands are discovered automatically from the command tree, so new commands can be added without maintaining a central command table.

## AI

Midnight Terminal includes an `ai` command with multiple model tiers, streaming, optional thinking mode, pipeline input, and local request/response logging.

```text
ai "explain this code"
ai --fast "quick question"
ai --medium "analyze this architecture"
ai --deep "find the bug"
```

## Requirements

* Windows or Linux
* Python 3.12+
* Git

macOS support is planned for later.

## Installation

```bash
git clone https://github.com/notcongg/Midnight_Terminal.git
cd Midnight_Terminal

pip install .
python -m src
```

## Development

```bash
git clone https://github.com/notcongg/Midnight_Terminal.git
cd Midnight_Terminal

python -m venv .venv
source .venv/bin/activate

pip install -e .
pytest
```

On Windows:

```powershell
.venv\Scripts\activate
pip install -e .
pytest
```

## Project Status

Midnight Terminal is under active development.

The core shell architecture, command system, parser, executor, history, pipelines, redirection, external process execution, hardware information, and native extensions are implemented.

Windows and Linux are currently supported. macOS support is planned for later.

## License

Midnight Terminal is licensed under the **GNU General Public License v3.0 or later**.

See [`LICENSE`](LICENSE) for the full license text.
