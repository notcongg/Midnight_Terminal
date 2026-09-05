# 🌙 Midnight Terminal

A lightweight, customizable terminal environment written in Python.

> **Wait.**
>
> It's not a terminal emulator.
>
> It's a shell.
>
> Written in Python.
>
> **For Windows.**

Midnight Terminal is a hobby terminal/shell project focused on learning, experimentation, and building a custom command-line environment from the ground up.

---

## ✨ Features

It started as a terminal.

Then things happened.

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
* 📜 Persistent command history
* 📝 Multiline command history
* ⚙️ Configurable shell environment
* 🔄 Runtime environment reloading with `source`
* 🛠️ Environment configuration editing with `enfix`
* 🤖 AI-powered command
* 📝 AI request/response logging
* 🌙 Lightweight and extensible architecture
* 🐍 Built with Python

> At some point, it stopped being just a terminal project.

---

## 🖥️ Shell & System

| Command   | Description                                |
| --------- | ------------------------------------------ |
| `alias`   | Create or manage command aliases           |
| `cd`      | Change the current directory               |
| `cls`     | Clear the terminal                         |
| `date`    | Display the current date and time          |
| `echo`    | Print or write text                        |
| `env`     | Display the shell environment              |
| `enfix`   | Edit environment configuration             |
| `help`    | Display command help                       |
| `history` | Display previously executed commands       |
| `host`    | Display the hostname                       |
| `kill`    | Terminate a running process                |
| `ps`      | Display running processes                  |
| `pwd`     | Display the current directory              |
| `set`     | Set an environment variable                |
| `source`  | Reload the shell environment configuration |
| `task`    | Manage and inspect system tasks            |
| `trm`     | Clear and refresh the terminal             |
| `unset`   | Remove an environment variable             |
| `wc`      | Count lines, words, and characters         |
| `which`   | Find the path of a command                 |
| `whoami`  | Display the current username               |

---

## 📁 File Management

| Command | Description                                |
| ------- | ------------------------------------------ |
| `cat`   | Display file contents                      |
| `cp`    | Copy files and directories                 |
| `crt`   | Create files and directories               |
| `find`  | Find files and directories                 |
| `grep`  | Search text inside files or command output |
| `head`  | Display the first lines of input or files  |
| `ls`    | List files and directories                 |
| `mkdir` | Create a directory                         |
| `mte`   | Open the Midnight Text Editor              |
| `mv`    | Move files and directories                 |
| `rem`   | Rename files and directories               |
| `rm`    | Remove files and directories               |
| `stat`  | Display file or directory information      |
| `tail`  | Display the last lines of input or files   |
| `tree`  | Display a directory as a tree              |

---

## 🤖 AI & Hardware

| Command  | Description                  |
| -------- | ---------------------------- |
| `ai`     | Ask an AI model a question   |
| `hwinfo` | Display hardware information |

> Some commands and features are still under development.

---

# 🤖 AI

Yes, the terminal has an AI command.

No, this wasn't part of the original plan.

Midnight Terminal includes an `ai` command with multiple model tiers.

### Models

| Tier     | Model                   |
| -------- | ----------------------- |
| `fast`   | NVIDIA Nemotron 3 Super |
| `medium` | NVIDIA Nemotron 3 Ultra |
| `deep`   | DeepSeek V4 Pro         |

The default model is `fast`.

### Basic usage

```text
ai "hello"
```

### Choose a model

```text
ai --fast "explain this code"
ai --medium "analyze this architecture"
ai --deep "find the bug in this code"
```

### Short model flag

```text
ai -m fast "hello"
ai -m medium "analyze this"
ai -m deep "debug this"
```

### Thinking mode

```text
ai --thinking "solve this problem"
```

### Streaming

```text
ai --stream "write a short explanation"
```

### And yes, it works with pipelines

```text
echo "Hello world" | ai "explain this"
```

AI requests and responses are logged to:

```text
src/data/log/AI_LOG.log
```

---

# ⚙️ Environment

Midnight Terminal has a custom environment configuration system.

Configuration is stored in:

```text
src/cmd/rootfs/env/envconfig.dream
```

Example:

```text
set $NAME=(cmd.whoami);
set $HOST=(cmd.hostname);
set $PWD=(cmd.pwd);

set $UP1=[
╭─[$NAME@$HOST]-[$PWD]
╰─$~space
    set $CURSOR=CURSORSHAPE.BLINKING_BEAM;
]

set $INPUT.AUTOCOMPLETE=true;
set $INPUT.HISTORY=true;
set $INPUT.HISTORY_SIZE=1000;
```

Environment variables can be inspected with:

```text
env
```

Individual variables can be modified with:

```text
set $NAME=Congg;
```

Variables can be removed with:

```text
unset $NAME
```

Changes can be reloaded without restarting the shell:

```text
source
```

The `enfix` command can modify environment configuration interactively:

```text
enfix UP1=[
> ╭─[$NAME@$HOST]-[$PWD]
> ╰─$~space
> ]
```

Multiline environment values are supported.

---

# 📜 History

Midnight Terminal maintains persistent command history.

History is stored in:

```text
src/history/.midnight_history
```

History behavior can be configured through `envconfig.dream`:

```text
set $INPUT.HISTORY=true;
set $INPUT.HISTORY_SIZE=1000;
set $INPUT.HISTORY_IGNORE_CONSECUTIVE_DUPLICATES=true;
```

Supported history features include:

* Persistent history
* Configurable history size
* Consecutive duplicate filtering
* Multiline command history
* Automatic history file creation
* History file rotation

For example, a multiline command is stored as a single history entry:

```text
# 2026-09-05 ...

+enfix test=[
+hello
+world
+]
```

---

# 🚀 Installation

## Requirements

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

# 💻 Usage

After starting Midnight Terminal:

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

---

## 🔗 Pipelines

Commands can pass their output to another command.

```text
> echo "Hello world" | grep Hello

Hello world
```

And yes, you can chain them:

```text
> echo "Hello world" | grep world | grep Hello

Hello world
```

---

## ↪️ Redirection

Output:

```text
> echo "Hello world" > hello.txt
```

Append:

```text
> echo "Another line" >> hello.txt
```

Input:

```text
> cat < hello.txt
```

Combine everything:

```text
> cat error.log | grep ERROR
```

---

# 🧠 Command Architecture

Here's where this gets slightly less normal.

Midnight Terminal doesn't keep a giant list of commands somewhere and manually register every command.

Commands live inside:

```text
src/
└── cmd/
    └── rootfs/
```

For example:

```text
src/
├── cmd/
│   ├── rootfs/
│   │   ├── cd/
│   │   ├── ls/
│   │   ├── mv/
│   │   ├── rm/
│   │   ├── grep/
│   │   ├── ai/
│   │   └── ...
│   │
│   └── utils/
│       └── registry.py
```

The command registry automatically discovers command modules and makes them available to the shell.

So adding a command does not require editing some central command list.

Drop the command in.

The registry finds it.

That's it.

---

# ⌨️ Input System

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
* [x] Multiline input
* [x] Persistent history

For example:

```text
> Grep
```

can become:

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

# 🧩 Shell Architecture

Now the questionable part.

You type:

```text
echo "Hello world" | grep world > output.txt
```

Midnight Terminal does not simply split the string and hope for the best.

The command goes through multiple stages:

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

> Yes, this is still a Python terminal.

---

# 🗺️ Roadmap

## Shell

* [x] Command registry
* [x] Command aliases
* [x] File system commands
* [x] Hardware information
* [x] Command history
* [x] Environment variables
* [x] Command parser
* [x] Quoted arguments
* [x] Output redirection
* [x] Input redirection
* [x] Pipelines
* [x] Process management

## Input

* [x] Custom PATH input
* [x] AutoComplete
* [x] Syntax Corrector
* [x] Matcher
* [x] Suggestions
* [x] Validator
* [x] Multiline input
* [x] Persistent history

## Commands

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
* [x] `env`
* [x] `enfix`
* [x] `history`
* [x] `ps`
* [x] `task`
* [x] `kill`
* [x] `wc`
* [x] `set`
* [x] `unset`
* [x] `source`

## AI

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

# 🤝 Contributing

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

# 📜 License

Midnight Terminal is free software licensed under the:

**GNU General Public License v3.0 or later**

See [`LICENSE`](LICENSE) for the complete license text.

---

# 🌙 About

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

> **Built with Python.**
>
> **Built at midnight. 🌙**
>
> *It was supposed to be a terminal.*
>
> Yes, it's a shell.
>
> Yes, it's written in Python.
>
> Yes, it has an AST.
>
> **We may have gone too far.**
