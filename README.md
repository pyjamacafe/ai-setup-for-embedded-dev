## Setup and Installation

This guide walks you through setting up the local AI environment, installing the required fast-execution tools, and connecting your first Model Context Protocol (MCP) servers.

### 1. Install Ollama

Ollama is the engine that runs the large language models locally on your machine.

* **macOS & Linux:**
    Run the following command in your terminal:
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
* **Windows:**
    Open PowerShell and run:
    ```powershell
    irm https://ollama.com/install.ps1 | iex
    ```
    *(Alternatively, download the executable directly from [ollama.com](https://ollama.com/))*

### 2. Download the Gemma 4 Model

We use Google's **Gemma 4** as our primary local reasoning model. It provides excellent agentic capabilities and native tool-calling support.

To pull the model and start the Ollama service, open your terminal and run:
```bash
ollama run gemma4
```
*(Note: This will download the default model. If you are running on lower-VRAM edge devices like a Raspberry Pi, use `ollama run gemma4:e4b` for the "effective 4B" parameter version).*

### 3. Install `uv` (Fast Python Package Manager)

To manage our Python-based MCP servers and the TUI client efficiently, we use `uv` from Astral. It is remarkably faster than standard `pip` and includes the `uvx` command for ephemeral tool execution.

* **macOS & Linux:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
* **Windows:**
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
*Verify the installation by running `uv --version`.*

### 4. Install the MCP Client for Ollama

We use the [mcp-client-for-ollama](https://github.com/jonigl/mcp-client-for-ollama) text-based user interface (TUI) to interact with our local models and MCP tools seamlessly.

Use `uv` to install the client globally:
```bash
uv tool install mcp-client-for-ollama
```

**Important: Make `ollmcp` executable from anywhere**
If this is your first time installing global tools with `uv`, you need to ensure its binary directory is added to your system's PATH. You can do this by sourcing the `uv` environment file in your shell configuration.

* **For Zsh (macOS default & many Linux distros):**
    ```bash
    echo 'source $HOME/.local/bin/env' >> ~/.zshrc
    source ~/.zshrc
    ```
* **For Bash (Standard Linux default):**
    ```bash
    echo 'source $HOME/.local/bin/env' >> ~/.bashrc
    source ~/.bashrc
    ```
*(Note: If the `env` file doesn't exist on your system, you can achieve the same result by appending `export PATH="$HOME/.local/bin:$PATH"` to your respective `.zshrc` or `.bashrc` file).*

Once your shell is reloaded, verify the installation by typing `ollmcp --help`.

***

### 5. Adding and Running MCP Servers

An MCP server acts as a bridge between the AI model and your local environment (like reading your AOSP source tree or parsing `dmesg` logs). You launch the client by passing the paths to the MCP servers you want the AI to have access to.

**Run a local python MCP server:**
```bash
ollmcp --mcp-server ./path/to/your/custom_server.py
```

**Run multiple servers simultaneously:**
```bash
ollmcp --mcp-server ./servers/gdb_parser.py --mcp-server ./servers/dts_validator.py
```

**Run a server via standard input/output with `uvx`:**
If your MCP server is packaged as a standard Python tool (like standard SQLite or filesystem MCP servers), you can execute it on the fly:
```bash
ollmcp --mcp-server "uvx some-mcp-server-package"
```

### 6. Useful TUI Commands

Once the `ollmcp` client is running, you are in an interactive chat session. Use these internal commands (prefixed with `/`) to manage your environment:

* `/help` : Display the full list of available commands and settings.
* `/model` : Switch between locally downloaded Ollama models on the fly (e.g., from `gemma4` to `llama3.2`).
* `/tools` : View all tools currently exposed by your connected MCP servers.
* `/prompts` : Browse and invoke specific prompt templates provided by your MCP servers.
* `/server:<prompt_name>` : Quickly invoke an MCP prompt and automatically collect required arguments.
* `im` : Toggle the **Input Mode**. Switch from single-line to multiline input (essential when pasting block configs or C++ snippets). Press `Esc` then `Enter` to submit in multiline mode.