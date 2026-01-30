# nanocode

Minimal agentic coding assistant. Single Python file, zero dependencies, ~250 lines.

Now powered by **Ollama** for local, privacy-friendly AI. No API keys required!

![screenshot](screenshot.png)

## Features

- Full agentic loop with tool use
- Tools: `read`, `write`, `edit`, `glob`, `grep`, `bash`
- Conversation history
- Colored terminal output

## Prerequisites

Install [Ollama](https://ollama.ai) and pull the llama3.2 model:

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull llama3.2:7b
```

## Usage

Just run it - no API keys needed!

```bash
python nanocode.py
```

### Configuration

Use environment variables to customize:

```bash
# Use a different Ollama model
export MODEL="mistral:7b"
python nanocode.py

# Connect to remote Ollama instance
export OLLAMA_HOST="http://remote-server:11434"
python nanocode.py
```

**Available models:**
- `llama3.2:7b` (default) - Fast, good for coding
- `llama3.2:3b` - Even faster, lower resource usage
- `codellama:13b` - Specialized for code
- `mistral:7b` - Alternative general model
- Any model from [ollama.ai/library](https://ollama.ai/library)

## Commands

- `/c` - Clear conversation
- `/q` or `exit` - Quit

## Tools

| Tool | Description |
|------|-------------|
| `read` | Read file with line numbers, offset/limit |
| `write` | Write content to file |
| `edit` | Replace string in file (must be unique) |
| `glob` | Find files by pattern, sorted by mtime |
| `grep` | Search files for regex |
| `bash` | Run shell command |

## Example

```
────────────────────────────────────────
❯ what files are here?
────────────────────────────────────────

⏺ Glob(**/*.py)
  ⎿  nanocode.py

⏺ There's one Python file: nanocode.py
```

## License

MIT
