<p align="center">
  <img src="logo/banner.png" alt="Midnight Terminal Banner" width="100%">
</p>

<h1 align="center">Midnight Terminal</h1>

<p align="center">
  An experimental, extensible command-line shell built with Python, C++, and AI collaboration.
</p>

<p align="center">
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/GPLv3-FFFFFF?logo=gnu&logoColor=black&style=for-the-badge" alt="GPLv3">
  </a>
  <a href="https://github.com/notcongg/Midnight_Terminal">
    <img src="https://img.shields.io/github/stars/notcongg/Midnight_Terminal?style=for-the-badge&logo=github" alt="GitHub Stars">
  </a>
  <a href="https://github.com/notcongg/Midnight_Terminal/issues">
    <img src="https://img.shields.io/github/issues/notcongg/Midnight_Terminal?style=for-the-badge&logo=github" alt="GitHub Issues">
  </a>
  <a href="https://github.com/notcongg/Midnight_Terminal/releases">
    <img src="https://img.shields.io/github/v/release/notcongg/Midnight_Terminal?style=for-the-badge&logo=github" alt="Release">
  </a>
</p>

---

## Overview

> [NOTE]
> This is an experimental hobby project exploring human-AI pair programming to build a custom shell environment from scratch.

Midnight Terminal started as a basic command-line interface and rapidly evolved into a full-featured shell environment. It features a complete pipeline execution model, custom AST parser, environment state management, AI assistance integrated into the CLI lifecycle, and native C++ binding support for high-performance extensions.

### Project Specs
**AI Integration:**
<p align="left">
  <a href="#">
    <img src="https://custom-icon-badges.demolab.com/badge/ChatGPT-74aa9c?logo=openai&logoColor=white&style=for-the-badge" alt="ChatGPT">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Deepseek-4D6BFF?logo=deepseek&logoColor=fff&style=for-the-badge" alt="DeepSeek">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Google%20Gemini-886FBF?logo=googlegemini&logoColor=fff&style=for-the-badge" alt="Google Gemini">
  </a>
</p>

**Programming Language:**
<p align="left">
  <a href="#">
    <img src="https://img.shields.io/badge/C%2B%2B-Native%20Extensions-%2300599C.svg?logo=c%2B%2B&logoColor=white&style=for-the-badge" alt="C++ Native Extensions">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Python 3.12+-Core%20Language-3776AB?logo=python&logoColor=fff&style=for-the-badge" alt="Python Core Language">
  </a>
</p>

**Supported OS:**
<p align="left">
  <a href="#"><img src="https://custom-icon-badges.demolab.com/badge/Windows-0078D6?logo=windows11&logoColor=white&style=for-the-badge" alt="Windows"></a>
  <a href="#"><img src="https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black&style=for-the-badge" alt="Linux"></a>
</p>

**License:**
<p align="left">
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/GPLv3-FFFFFF?logo=gnu&logoColor=black&style=for-the-badge" alt="GPLv3">
  </a>
</p>

> *"It was supposed to be a simple terminal wrapper.*  
> *Then it got a lexer.*  
> *Then a parser.*  
> *Then an AST.*  
> *Then an executor.*  
>  
> *We may have gone too far."*

---

## Key Features

* **Shell Core:** Interactive input processing, dynamic command discovery, persistent history, alias resolution, and full environment variable management.
* **Custom Engine:** Built-in lexer, recursive-descent parser, abstract syntax tree (AST) construction, and custom execution runtime.
* **Process Control:** Robust support for process redirection (`<`, `>`), piping (`|`), logic chains (`&&`, `||`), sequential execution (`;`), and external system commands.
* **Native Extensions:** Extensible architecture allowing core functionality to be extended using C++ modules for speed and low-level system access.
* **Integrated AI Engine:** Built-in AI interface supporting streaming outputs, dynamic model tiers, reasoning/thinking modes, and pipe integration.
* **Embedded Editor:** Includes `mte` (Midnight Text Editor) for quick file edits directly within the session.
* **System Metrics:** Native tools for file management, process handling, and real-time hardware diagnostics.

---

## Architecture

```text
               +-----------------------+
               |      User Input       |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |   Syntax Correction   |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |     Lexical Analysis  |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |         Parser        |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |  Abstract Syntax Tree |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |        Executor       |
               +---+---------------+---+
                   |               |
                   v               v
         +-----------------+  +--------------------+
         | Built-in Engine |  | External Processes |
         +--------+--------+  +---------+----------+
                  |                     |
                  v                     v
         +-----------------+  +--------------------+
         |  Command Tree   |  | Native C++ Modules |
         +-----------------+  +--------------------+
```

Commands are automatically discovered at runtime using dynamic tree indexing, removing the need to register new commands manually in a centralized table.

---

## AI Assistant Integration

Midnight Terminal features a native `ai` interface equipped with context-aware streaming, local request logging, and execution pipeline support.

```bash
# Standard Query
ai "Explain this directory structure"

# Fast Utility Tier
ai --fast "How do I untar a .tar.gz file?"

# Architecture & Design Tier
ai --medium "Compare memory footprints between subprocess execution models"

# Deep Analysis / Debugging Tier
ai --deep "Analyze the current call stack for deadlock risks"

# Pipeline Integration
cat error.log | ai "Extract the main exception and suggest a fix"
```

---

## Requirements

* **Operating System:** Windows 10+ or Linux *(macOS support planned)*
* **Runtime:** Python 3.12+
* **Version Control:** Git
* **Compiler (Optional):** C++17 compatible compiler (GCC/Clang/MSVC) for building native extensions locally.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/notcongg/Midnight_Terminal.git
cd Midnight_Terminal

# Install dependencies and package
pip install .

# Launch Midnight Terminal
python -m src
```

---

## Development Setup

```bash
# Clone repository
git clone https://github.com/notcongg/Midnight_Terminal.git
cd Midnight_Terminal

# Create virtual environment
python -m venv .venv

# Activate environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install in editable mode & run test suite
pip install -e .
pytest
```

---

## Project Status

Midnight Terminal is under **active experimental development**. 

The current release includes:
- [x] Full AST parser & custom execution pipeline
- [x] Stream redirection (`<`, `>`), piping (`|`), and conditional execution (`&&`, `||`, `;`)
- [x] Native AI integration with tiering support
- [x] C++ extension loader
- [x] Windows and Linux OS compatibility