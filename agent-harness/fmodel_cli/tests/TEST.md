# TEST.md — FModel CLI Test Plan

## Test Inventory

| File | Planned Tests | Type |
|------|--------------|------|
| test_core.py | 12 | Unit (pak parsing, uasset parsing, extraction) |
| test_full_e2e.py | 8 | E2E (real PAK files, real FModel backend) |
| **Total** | **20** | |

## Unit Test Plan

### `core/pak_parser.py` — 6 tests
- `test_pak_footer_parse` — Parse PAK footer (version, index offset, index size)
- `test_pak_index_parse` — Parse PAK index (mount point, entry count, file entries)
- `test_pak_index_entries_have_paths` — File entries contain valid path strings
- `test_pak_index_entries_have_sizes` — File entries contain valid offset/size
- `test_pak_extract_file` — Extract a single file from PAK by path
- `test_pak_extract_file_binary_match` — Extracted file matches known content

### `core/asset_parser.py` — 4 tests
- `test_uasset_find_package_magic` — Find UE4 package magic in extracted data
- `test_uasset_read_name_table` — Parse FName table from .uasset
- `test_uasset_list_exports` — List export entries from .uasset
- `test_uasset_extract_strings` — Extract readable strings from Blueprint

### `utils/fmodel_backend.py` — 2 tests
- `test_find_fmodel` — Locate FModel executable on system
- `test_fmodel_not_found_error` — Clear error when FModel not installed

## E2E Test Plan

### Real PAK file tests (set FMODEL_TEST_PAK env var)
- `test_pak_list_full` — List all files in real 263MB PAK, verify count > 1000
- `test_pak_extract_config` — Extract .ini files, verify content contains expected keys
- `test_pak_extract_uasset` — Extract .uasset, verify UE4 package magic
- `test_asset_inspect_blueprint` — Inspect MotionControllerPawn, find known variable names

### FModel backend tests
- `test_fmodel_launch` — Launch FModel with a PAK path (verifies process starts)
- `test_fmodel_export` — Export a texture via FModel subprocess (if supported)

### CLI subprocess tests
- `test_cli_help` — `cli-anything-fmodel --help` returns 0
- `test_cli_pak_list_json` — `cli-anything-fmodel --json pak list --path <pak>` prints valid JSON

## Realistic Workflow Scenarios

### Workflow 1: Modding Recon
Simulates: "What's in this game? Find the player blueprint."
1. `pak list` — List all files
2. `pak extract --pattern "*MotionController*"` — Extract key blueprints
3. `asset inspect --file MotionControllerPawn.uasset` — Read properties
4. `asset strings --file MotionControllerPawn.uasset` — Find power names
Verified: File count > 0, extracted files exist, strings contain expected keywords

### Workflow 2: Extract All Config
Simulates: "Get the game config for modding."
1. `pak list --filter "*.ini"` — Find config files
2. `pak extract --filter "*.ini" --output ./configs/` — Extract all
Verified: Config files exist, DefaultEngine.ini contains [URL] section

### Workflow 3: Full Export Pipeline
Simulates: "Extract a texture to edit."
1. `pak list --filter "*.png"` — Find textures
2. `pak extract --path "path/to/texture.png"` — Extract raw
3. `export texture --path "path/to/texture.uasset" --format png` — Export via FModel
Verified: Output PNG exists, has valid PNG magic bytes, size > 0
