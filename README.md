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

### 7. Configuring MCP Servers via JSON

Instead of passing every tool via command-line arguments, you can define all your local AI tools, scripts, and MCP servers in a single JSON configuration file. This allows `ollmcp` to automatically spin up the necessary environments (like Python or Node) and attach the tools to your local model.

#### Creating your `mcp-servers.json`

Create a file named `mcp-servers.json` in your project root (or wherever you prefer to keep your configs). The structure requires an `mcpServers` object, where each key is the name of your server, and the value defines how to execute it.

Here is an example configuration tailored for our embedded development setup:

```json
{
  "mcpServers": {
    "gdb_memory_walker": {
      "command": "python3",
      "args": [
        "/absolute/path/to/your/repo/servers/gdb_mmu_walker.py"
      ]
    },
    "aosp_log_parser": {
      "command": "uv",
      "args": [
        "run",
        "/absolute/path/to/your/repo/servers/logcat_analyzer.py"
      ],
      "env": {
        "AOSP_BUILD_ENV": "raspberrypi5-userdebug"
      }
    },
    "dts_validator": {
      "command": "uvx",
      "args": [
        "device-tree-mcp-server"
      ]
    }
  }
}
```

**Understanding the Fields:**
* **`command`**: The executable to run (e.g., `python3`, `node`, `uv`, or `uvx`).
* **`args`**: The arguments passed to the command. Always use absolute paths to your scripts to avoid directory resolution issues.
* **`env`**: (Optional) Environment variables your specific server might need, such as targeting a specific AOSP build flavor or pointing to a specific cross-compiler toolchain path.

#### Running with the Configuration File

Once your configuration file is ready, start the `ollmcp` client using the `--servers-json` (or `-j`) flag:

```bash
ollmcp --servers-json ./mcp-servers.json --model gemma4
```

When the client loads, type `/tools` in the interface. You should see all the tools exposed by your `gdb_memory_walker`, `aosp_log_parser`, and `dts_validator` successfully registered and ready for the AI to use.

#### Pro-Tip: Auto-Discovery

If you are already experimenting with MCP tools using Claude Desktop, `ollmcp` can automatically discover and use those exact same tools without needing a duplicate config file. 

Just run `ollmcp` with the `--auto-discovery` (or `-a`) flag:

```bash
ollmcp --auto-discovery --model gemma4
```
*(This tells the client to parse `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or its equivalent on Windows/Linux and load the servers defined there).*

### 8. Resources & Community MCP Servers

You don't have to build every tool from scratch! The Model Context Protocol ecosystem is growing rapidly, and there are hundreds of open-source servers you can plug directly into your local setup using the `mcp-servers.json` file. 

Explore these directories to find pre-built tools for everything from local database querying (SQLite/PostgreSQL) and filesystem management to web searching and GitHub integration:

* **[Official MCP Servers Repository](https://github.com/modelcontextprotocol/servers):** The core reference implementations maintained by the creators of the Model Context Protocol. This is the best place to find robust, production-ready servers and study high-quality source code.
* **[MCP Server Registry](https://registry.modelcontextprotocol.io/):** A comprehensive, searchable directory of community-built MCP servers. If you need a tool to parse a specific file format, interact with a REST API, or pull data from external services, check this registry first.