# SKILL.md — fmodel-cli

Parse, list, and extract Unreal Engine .pak archives. Inspect .uasset Blueprints.
Pure Python — no FModel GUI dependency for core operations.

## Install

```bash
git clone https://github.com/overtimepog/fmodel-cli
cd fmodel-cli/agent-harness && pip install -e .
```

## Command Reference

### `fmodel pak info --path <pak>`
Get PAK metadata: version, file count, index offset/size.
```bash
fmodel --json pak info --path game.pak
# → {"version": 8, "file_count": 2484, "index_offset": 275409266, ...}
```

### `fmodel pak list --path <pak> [--filter <pattern>] [--limit N]`
List files inside a PAK archive.
```bash
fmodel pak list --path game.pak --filter ".ini"
fmodel --json pak list --path game.pak --filter "Blueprint" --limit 10
```

### `fmodel pak extract --path <pak> --file <name> [-o <dir>]`
Extract a single file by its PAK-internal path.
```bash
fmodel pak extract --path game.pak --file "Game/Config/DefaultEngine.ini" -o ./configs
```

### `fmodel asset inspect --file <.uasset>`
Inspect a .uasset Blueprint: exports, Blueprint classes, readable strings.
```bash
fmodel --json asset inspect --file MotionControllerPawn.uasset
# → {"export_count": 54, "blueprint_classes": [...], "string_count": 1080}
```

### `fmodel asset strings --file <.uasset> [--filter <pattern>]`
Extract all readable strings from a .uasset/.uexp pair.
```bash
fmodel asset strings --file MotionControllerPawn.uasset --filter "FireBall"
```

## Agent Guidance

- Always use `--json` for machine-readable output
- `pak info` is fast (reads footer only) — use first to assess a PAK
- `pak list` reads the full index (~300KB for large PAKs) — use `--filter` to narrow
- `asset inspect` needs companion `.uexp` in same directory
- Return code 0 = success, non-zero = error with message on stderr
