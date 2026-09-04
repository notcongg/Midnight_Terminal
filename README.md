# 🌙 Midnight Terminal

A lightweight, customizable terminal environment written in Python.

Midnight Terminal is a hobby terminal/shell project focused on learning, experimentation, and building a custom command-line environment from the ground up.

> **Status:** 🚧 Active Development

---

## ✨ Features

* 🖥️ Custom terminal interface
* ⚡ Automatic command discovery and registration
* 📁 File and directory management
* 🔎 File and directory searching
* 💻 Hardware information
* 🧩 Custom command system
* 🔧 Shell utilities
* 🔗 Command pipelines
* ↪️ Input and output redirection
* 🧠 Command syntax correction and suggestions
* ⌨️ Interactive command autocomplete
* 🤖 AI-powered command
* 📝 AI request/response logging
* 🌙 Lightweight and extensible architecture
* 🐍 Built with Python

---

### 🖥️ Shell & System

| Command  | Description                                |
| -------- | ------------------------------------------ |
| `alias`  | Create or manage command aliases           |
| `cd`     | Change the current directory               |
| `cls`    | Clear the terminal                         |
| `date`   | Display the current date and time          |
| `echo`   | Print or write text                        |
| `help`   | Display command help                       |
| `host`   | Display the hostname                       |
| `pwd`    | Display the current directory              |
| `trm`    | Clear and refresh the terminal             |
| `which`  | Find the path of a command                 |
| `whoami` | Display the current username               |

### 📁 File Management

| Command  | Description                                |
| -------- | ------------------------------------------ |
| `cat`    | Display file contents                      |
| `cp`     | Copy files and directories                 |
| `crt`    | Create files and directories               |
| `find`   | Find files and directories                 |
| `grep`   | Search text inside files or command output |
| `head`   | Display the first lines of input or files  |
| `ls`     | List files and directories                 |
| `mkdir`  | Create a directory                         |
| `mte`    | Open the Midnight Text Editor              |
| `mv`     | Move files and directories                 |
| `rem`    | Rename files and directories               |
| `rm`     | Remove files and directories               |
| `stat`   | Display file or directory information      |
| `tail`   | Display the last lines of input or files   |
| `tree`   | Display a directory as a tree              |

### 🤖 AI & Hardware

| Command  | Description                                |
| -------- | ------------------------------------------ |
| `ai`     | Ask an AI model a question                 |
| `hwinfo` | Display hardware information               |

> Some commands and features are still under development.

---

## 🤖 AI

Midnight Terminal includes an `ai` command with multiple AI model tiers.

### Models

| Tier     | Model                   |
| -------- | ----------------------- |
| `fast`   | NVIDIA Nemotron 3 Super |
| `medium` | NVIDIA Nemotron 3 Ultra |
| `deep`   | DeepSeek V4 Pro         |

The default model is `fast`.

### Examples

```text
ai "hello"
```

Use a specific model:

```text
ai --fast "explain this code"
ai --medium "analyze this architecture"
ai --deep "find the bug in this code"
```

Short model flag:

```text
ai -m fast "hello"
ai -m medium "analyze this"
ai -m deep "debug this"
```

Thinking mode:

```text
ai --thinking "solve this problem"
```

Streaming:

```text
ai --stream "write a short explanation"
```

AI can also receive input from a pipeline:

```text
echo "Hello world" | ai "explain this"
```

AI requests and responses are logged to:

```text
src/data/log/AI_LOG.log
```

---

## 🚀 Installation

### Requirements

* Python 3.12+
* Windows

Clone the repository:

```bash
git clone <repository-url>
cd midnight_terminal
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run Midnight Terminal:

```bash
python -m src
```

---

## 💻 Usage

After starting Midnight Terminal, enter a command:

```text
> ls
```

Change directories:

```text
> cd src
```

Display a file:

```text
> cat README.md
```

Create a file:

```text
> crt hello.txt
```

Find a file:

```text
> find README.md
```

Display hardware information:

```text
> hwinfo
```

Get help:

```text
> help
```

### Pipelines

Commands can pass their output to another command:

```text
> echo "Hello world" | grep Hello
Hello world
```

Multiple commands can be chained:

```text
> echo "Hello world" | grep world | grep Hello
Hello world
```

### Redirection

Output can be redirected to a file:

```text
> echo "Hello world" > hello.txt
```

Append output:

```text
> echo "Another line" >> hello.txt
```

Read input from a file:

```text
> cat < hello.txt
```

Pipelines and redirection can also be combined:

```text
> cat error.log | grep ERROR
```

---

## 🧠 Command Architecture

Midnight Terminal uses an automatic command registry.

Commands are stored inside:

```text
src/
└── cmd/
    └── rootfs/
```

Each command can be implemented as its own Python module.

For example:

```text
src/
└── cmd/
    ├── rootfs/
    │   ├── cd/
    │   ├── ls/
    │   ├── mv/
    │   ├── rm/
    │   ├── grep/
    │   ├── ai/
    │   └── ...
    │
    └── utils/
        └── registry.py
```

The command registry automatically discovers command modules and makes them available to the shell.

Commands do not need to be manually registered in a central command list.

This makes Midnight Terminal easier to extend as new commands are added.

---

## ⌨️ Input System

Midnight Terminal uses `prompt_toolkit` for interactive input.

Current input features include:

* [x] Custom prompt
* [x] Command history
* [x] Command autocomplete
* [x] Interactive completion menu
* [x] Syntax correction
* [x] Case-insensitive command normalization
* [x] Command matcher
* [x] Command suggestions
* [x] Syntax validator

Example:

```text
> Grep
```

can be normalized to:

```text
grep
```

Unknown commands can also produce suggestions:

```text
> gerp
gerp: command not found
Did you mean: grep?
```

---

## 🧩 Shell Architecture

Midnight Terminal separates command processing into multiple stages:

```text
Input
  │
  ▼
Syntax Corrector
  │
  ▼
Syntax Validator
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
  ▼
Command Registry
  │
  ▼
Command
```

The shell currently supports:

* Command tokenization
* Quoted arguments
* Command parsing
* AST generation
* Pipelines
* Input redirection
* Output redirection
* Append redirection
* Command execution
* Command suggestions
* Command aliases

---

## 🗺️ Roadmap

### Shell

* [x] Command registry
* [x] Command aliases
* [x] File system commands
* [x] Hardware information
* [x] Command history
* [ ] Environment variables
* [x] Command parser
* [x] Quoted arguments
* [x] Output redirection
* [x] Input redirection
* [x] Pipelines
* [ ] Process management

### Input

* [x] Custom PATH input
* [x] AutoComplete
* [x] Syntax Corrector
* [x] Matcher
* [x] Suggestions
* [x] Validator

### Commands

* [x] `alias`
* [x] `ls`
* [x] `cd`
* [x] `cat`
* [x] `echo`
* [x] `mkdir`
* [x] `rm`
* [x] `mv`
* [x] `crt`
* [x] `find`
* [x] `which`
* [x] `tree`
* [x] `hwinfo`
* [x] `cp`
* [x] `head`
* [x] `tail`
* [x] `stat`
* [x] `grep`
* [x] `ai`
* [x] `trm`
* [x] `host`
* [x] `whoami`
* [x] `date`
* [x] `mte`

### AI

* [x] AI command
* [x] Fast model
* [x] Medium model
* [x] Deep model
* [x] Model selection flags
* [x] Thinking mode
* [x] Streaming
* [x] Pipeline input
* [x] AI request/response logging
* [ ] More AI providers
* [ ] Improved terminal UI

---

## 🤝 Contributing

Contributions are welcome!

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting changes.

You can contribute by:

* Adding new commands
* Fixing bugs
* Improving the shell
* Improving documentation
* Adding tests
* Improving the terminal UI
* Suggesting new features

---

## 📜 License

Midnight Terminal is free software licensed under the:

**GNU General Public License v3.0 or later**

See [`LICENSE`](LICENSE) for the complete license text.

---

## 🌙 About

Midnight Terminal is an experimental project created to explore:

* Shell architecture
* Command parsing
* Lexing and parsing
* Abstract syntax trees
* File systems
* Windows APIs
* Hardware information
* Process management
* Python internals
* AI integration
* Low-level programming concepts

The long-term goal is to evolve Midnight Terminal from a simple command-line project into a more complete and extensible shell environment.

---

**Built with Python. Built at midnight. 🌙**
