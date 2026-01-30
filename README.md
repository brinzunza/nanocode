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

Install [Ollama](https://ollama.ai) and pull a compatible model:

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a recommended model (choose one):
ollama pull hermes3          # BEST: Fine-tuned for tool calling
ollama pull deepseek-r1:8b   # GOOD: Reasoning model, handles tools well
ollama pull qwen2.5-coder    # GOOD: Code-focused, supports tools
```

## Usage

```bash
ollama serve

python nanocode.py
```

### Configuration

Use environment variables to customize:

```bash
# Use a specific model from your list
export MODEL="HammerAI/hermes-3-llama-3.1"  # Best for tool calling
python nanocode.py

# Or try these from your installed models:
export MODEL="deepseek-r1:8b"        # Good reasoning
export MODEL="devstral"              # Mistral's dev model
python nanocode.py

# Connect to remote Ollama instance
export OLLAMA_HOST="http://remote-server:11434"
python nanocode.py
```

**Models from your list that should work:**
- ✅ `HammerAI/hermes-3-llama-3.1` - **BEST CHOICE** (fine-tuned for tools)
- ✅ `deepseek-r1:8b` or `deepseek-r1` - Reasoning model
- ✅ `devstral` - Mistral developer model

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
