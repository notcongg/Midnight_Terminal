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
* 🌙 Lightweight and extensible architecture
* 🐍 Built with Python

---

## 📦 Commands

| Command  | Description                                |
| -------- | ------------------------------------------ |
| `alias`  | Create or manage command aliases           |
| `cat`    | Display file contents                      |
| `cd`     | Change the current directory               |
| `cls`    | Clear the terminal                         |
| `crt`    | Create files and directories               |
| `echo`   | Print text and write content               |
| `find`   | Find files and directories                 |
| `grep`   | Search text inside files or command output |
| `help`   | Display command help                       |
| `host`   | Display the hostname                       |
| `hwinfo` | Display hardware information               |
| `ls`     | List files and directories                 |
| `mkdir`  | Create a directory                         |
| `mv`     | Move files and directories                 |
| `pwd`    | Display the current directory              |
| `rem`    | Rename files and directories               |
| `rm`     | Remove files and directories               |
| `tree`   | Display a directory as a tree              |
| `which`  | Find the path of a command                 |
| `whoami` | Display the current username               |
| `date`   | Display the current date and time          |

> Some commands and features are still under development.

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
    │   ├── cd.py
    │   ├── ls.py
    │   ├── mv.py
    │   ├── rm.py
    │   └── ...
    │
    └── utils/
        └── registry.py
```

The command registry automatically discovers command modules and makes them available to the shell.

This allows new commands to be added without manually maintaining a large command list.

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
* [ ] Quoted arguments
* [ ] Output redirection
* [x] Pipelines
* [ ] Process management

### Commands

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
* File systems
* Windows APIs
* Hardware information
* Process management
* Python internals
* Low-level programming concepts

The long-term goal is to evolve Midnight Terminal from a simple command-line project into a more complete and extensible shell environment.

---

**Built with Python. Built at midnight. 🌙**
