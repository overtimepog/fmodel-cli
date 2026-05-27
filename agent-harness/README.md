# fmodel-cli

CLI for browsing and extracting Unreal Engine game assets — no GUI needed.

Parse `.pak` archives, inspect `.uasset` Blueprints, extract game content.
Built for AI agents and terminal users who work with UE4/UE5 games.

## Install

```bash
git clone https://github.com/overtimepog/fmodel-cli.git
cd fmodel-cli/agent-harness
pip install -e .
```

## Usage

```bash
# PAK operations
fmodel pak info --path game.pak
fmodel pak list --path game.pak --filter ".uasset"
fmodel pak extract --path game.pak --file "path/to/file.uasset" -o ./out

# Asset inspection
fmodel asset inspect --file Blueprint.uasset
fmodel asset strings --file Blueprint.uasset --filter "power"

# JSON output for scripting
fmodel --json pak info --path game.pak | jq .file_count
```

## Commands

| Command | Description |
|---------|-------------|
| `pak info` | PAK version, file count, index info |
| `pak list` | List files in PAK (supports `--filter`) |
| `pak extract` | Extract files by name or filter pattern |
| `asset inspect` | Show Blueprint exports and classes |
| `asset strings` | Extract readable strings from .uasset |
| `repl` | Interactive REPL mode (default) |

## Dependencies

- Python 3.10+
- click, prompt_toolkit
- FModel.exe (optional — only for GUI browsing; core parsing is pure Python)

## Test

```bash
pytest fmodel_cli/tests/ -v
```
