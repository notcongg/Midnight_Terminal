# 🌙 Midnight Terminal

> **Wait.**
>
> It's not a terminal emulator.
>
> It's a shell.
>
> Written in Python.
>
> With native Windows process execution.
>
> For Windows.

Midnight Terminal is a lightweight, customizable **shell environment for Windows**, written primarily in Python.

It started as a small terminal project.

Then it grew a lexer.

Then a parser.

Then an AST.

Then an executor.

Then a native C++ process bridge.

At some point, it stopped being "just a terminal project."

---

## ✨ Features

* 🖥️ Custom terminal interface and prompt
* ⚡ Automatic command discovery and registration
* 📁 File and directory management
* 🔎 File and directory searching
* 💻 Hardware information
* 🧩 Extensible command system
* 🔧 Shell utilities
* 🔗 Command pipelines
* ↪️ Input and output redirection
* ➕ Append redirection
* 🧠 Command syntax correction and suggestions
* ⌨️ Interactive command autocomplete
* 📜 Persistent command history
* 📝 Multiline input and history
* ⚙️ Configurable shell environment
* 🔄 Runtime environment reloading with `source`
* 🛠️ Interactive environment configuration with `enfix`
* 🤖 AI-powered shell command
* 📝 AI request/response logging
* ⚡ Native external process execution
* 🔌 Python ↔ C++ Windows process bridge
* 🌙 Lightweight and extensible architecture

> At some point, it stopped being just a terminal project.

---

# 🖥️ Shell & System

| Command   | Description                                |
| --------- | ------------------------------------------ |
| `alias`   | Create or manage command aliases           |
| `cd`      | Change the current directory               |
| `cls`     | Clear the terminal                         |
| `date`    | Display the current date and time          |
| `echo`    | Print text                                 |
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
| `time`    | Measure the execution time of a command    |

---

# 📁 File Management

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

# 🤖 AI & Hardware

| Command  | Description                  |
| -------- | ---------------------------- |
| `ai`     | Ask an AI model a question   |
| `hwinfo` | Display hardware information |

> Some commands and features are still under development.

---

# 🤖 AI

Yes, Midnight Terminal has an AI command.

No, this wasn't part of the original plan.

The `ai` command supports multiple model tiers and can consume pipeline input.

## Models

| Tier     | Model                   |
| -------- | ----------------------- |
| `fast`   | NVIDIA Nemotron 3 Super |
| `medium` | NVIDIA Nemotron 3 Ultra |
| `deep`   | DeepSeek V4 Pro         |

The default model is `fast`.

## Basic usage

```text
ai "hello"
```

## Choose a model

```text
ai --fast "explain this code"

ai --medium "analyze this architecture"

ai --deep "find the bug in this code"
```

## Short model flag

```text
ai -m fast "hello"

ai -m medium "analyze this"

ai -m deep "debug this"
```

## Thinking mode

```text
ai --thinking "solve this problem"
```

## Streaming

```text
ai --stream "write a short explanation"
```

## Pipeline input

```text
echo "Hello world" | ai "explain this"
```

AI requests and responses are logged to:

```text
src/data/log/AI_LOG.log
```

---

# ⚙️ Environment

Midnight Terminal has its own environment configuration system.

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

╰─$\~space

    set $CURSOR=CURSORSHAPE.BLINKING_BEAM;

]

set $INPUT.AUTOCOMPLETE=true;

set $INPUT.HISTORY=true;

set $INPUT.HISTORY_SIZE=1000;
```

Inspect the current environment:

```text
env
```

Set a variable:

```text
set $NAME=Congg;
```

Remove a variable:

```text
unset $NAME
```

Reload the environment without restarting Midnight:

```text
source
```

The `enfix` command can modify environment configuration interactively:

```text
enfix UP1=[

> ╭─[$NAME@$HOST]-[$PWD]

> ╰─$\~space

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

A multiline command is stored as a single history entry:

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

* Windows
* Python 3.12+
* Git

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
ls
```

Change directories:

```text
cd src
```

Display a file:

```text
cat README.md
```

Create a file:

```text
crt hello.txt
```

Find a file:

```text
find README.md
```

Display hardware information:

```text
hwinfo
```

Get command help:

```text
help
```

---

# 🔗 Pipelines

Midnight Terminal supports command pipelines.

```text
echo "Hello world" | grep Hello

Hello world
```

Pipelines can contain multiple commands:

```text
echo "Hello world" | grep world | grep Hello

Hello world
```

Pipelines can also connect built-in commands with external programs.

For example:

```text
echo hello | python -c "import sys; print(sys.stdin.read().strip())"

hello
```

External processes receive pipeline input through the native Midnight Extensions bridge.

---

# ↪️ Redirection

## Output

```text
echo "Hello world" > hello.txt
```

## Append

```text
echo "Another line" >> hello.txt
```

## Input

```text
cat < hello.txt
```

## Pipeline + redirection

```text
cat error.log | grep ERROR
```

Redirection is handled by the shell executor rather than being delegated entirely to the Windows command shell.

---

# 🔌 Native External Processes

One of Midnight Terminal's more unusual parts is its external process architecture.

Built-in commands are handled directly by the Python command registry.

Unknown commands are passed to the **Midnight Extensions** native process bridge.

The architecture looks roughly like this:

```text
Shell
  │
  ▼
Lexer / Parser
  │
  ▼
AST
  │
  ▼
Executor
  │
  ├── Built-in command
  │      │
  │      └── Command Registry
  │
  └── External command
         │
         ▼
   Python Extensions Wrapper
         │
         ▼
   Native C++ DLL
         │
         ▼
     CreateProcessW
         │
         ├── stdin
         ├── stdout
         └── stderr
```

The native bridge is responsible for Windows process creation and stream handling.

This allows Midnight Terminal to execute programs such as:

```text
python --version
```

```text
node --version
```

and use them inside pipelines:

```text
echo hello | python -c "import sys; print(sys.stdin.read())"
```

The native layer is implemented in C++ and exposed to Python through `ctypes`.

---

# 🧩 Command Architecture

Midnight Terminal does not keep one giant manually maintained command list.

Commands live under:

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

Adding a command therefore does not require editing a huge central command table.

Drop the command into the command tree.

The registry discovers it.

That's it.

---

# ⌨️ Input System

Midnight Terminal uses `prompt_toolkit` for interactive input.

Current input features include:

* Custom prompt
* Command history
* Command autocomplete
* Interactive completion menu
* Syntax correction
* Case-insensitive command normalization
* Command matching
* Command suggestions
* Syntax validation
* Multiline input
* Persistent history
* Configurable cursor style

Example:

```text
Grep
```

can be normalized to:

```text
grep
```

Unknown commands can produce suggestions:

```text
gerp: command not found
Did you mean: grep?
```

---

# 🧠 Shell Architecture

Midnight Terminal does not simply split command strings and hope for the best.

A command such as:

```text
echo "Hello world" | grep world > output.txt
```

passes through several stages:

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
  ├── Built-in
  │      │
  │      ▼
  │   Command Registry
  │
  └── External
         │
         ▼
      Extensions
         │
         ▼
      Native DLL
```

The executor is responsible for:

* Command execution
* Pipeline execution
* Exit status propagation
* `&&`
* `||`
* `;`
* Input redirection
* Output redirection
* Append redirection
* Built-in command dispatch
* External command dispatch
* Pipeline stdin/stdout flow
* Command timing through `time`

So yes.

This is still a Python shell.

It just happens to have an AST and a native Windows process bridge.

---

# 🔄 Command Status & Operators

Midnight Terminal supports command chaining through:

```text
&&
||
;
```

Examples:

```text
python -c "print('ok')" && echo success
```

```text
python -c "import sys; sys.exit(1)" || echo fallback
```

Commands propagate their exit status through the executor.

This allows shell logic to behave more like a traditional command-line environment.

---

# 🛠️ Process Execution

External programs are executed through the Midnight Extensions bridge rather than directly through Python's standard subprocess interface.

The native layer handles:

* Process creation
* Working directory
* stdin pipe
* stdout pipe
* stderr pipe
* Exit code
* Native memory management

This currently enables Midnight Terminal to execute normal Windows programs and integrate them with shell pipelines.

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
* [x] Append redirection
* [x] Pipelines
* [x] `&&`
* [x] `||`
* [x] `;`
* [x] External command execution
* [x] Native Windows process bridge
* [x] Process management
* [ ] More advanced process control

## Input

* [x] Custom prompt
* [x] AutoComplete
* [x] Syntax Corrector
* [x] Matcher
* [x] Suggestions
* [x] Validator
* [x] Multiline input
* [x] Persistent history
* [x] Configurable history
* [ ] More terminal control features

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
* [x] `time`

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

## Native Extensions

* [x] Windows process creation
* [x] stdout capture
* [x] stderr capture
* [x] stdin pipe support
* [x] Working directory support
* [x] Exit code reporting
* [x] Python `ctypes` bridge
* [ ] More advanced process signaling
* [ ] More native shell integration

---

# 🤝 Contributing

Contributions are welcome.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting changes.

You can contribute by:

* Adding new commands
* Fixing bugs
* Improving the shell
* Improving the parser or executor
* Improving documentation
* Adding tests
* Improving the terminal UI
* Improving native Windows integration
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
* Lexing and parsing
* Abstract syntax trees
* Command execution
* File systems
* Windows APIs
* Native process execution
* Hardware information
* Process management
* Python internals
* C/C++ integration
* AI integration
* Shell environments
* Terminal input systems

The long-term goal is to evolve Midnight Terminal from a simple command-line project into a more complete and extensible Windows shell environment.

---

> **Built with Python.**
>
> **Powered by C++ where Windows gets serious.**
>
> **Built at midnight. 🌙**
>
> *It was supposed to be a terminal.*
>
> *Then it got a lexer.*
>
> *Then a parser.*
>
> *Then an AST.*
>
> *Then an executor.*
>
> **We may have gone too far.**
