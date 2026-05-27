"""UE4 Blueprint bytecode analysis — extract variable comparisons.

For cooked BlueprintGeneratedClass .uexp files, finds "compare variable to
integer" patterns in the bytecode and reports which values each variable
is compared against. This reveals Switch-on-Int case values, enum mappings,
and state machine transitions.
"""
import struct


def parse_name_table(uasset_data: bytes) -> list[str]:
    """Parse the FName table from a cooked .uasset file.

    Heuristic: finds the longest run of valid FName entries.
    FName format: [len:uint32][name:bytes (null-terminated)][hash:uint32]
    """
    def try_fname(data, pos):
        if pos + 8 > len(data):
            return None, pos
        name_len = struct.unpack_from("<I", data, pos)[0]
        if name_len < 1 or name_len > 255:
            return None, pos
        if pos + 4 + name_len + 4 > len(data):
            return None, pos
        name_bytes = data[pos + 4 : pos + 4 + name_len]
        if name_bytes[-1] != 0:
            return None, pos
        try:
            name = name_bytes[:-1].decode("ascii")
        except UnicodeDecodeError:
            return None, pos
        if not all(32 <= b < 127 for b in name_bytes[:-1]):
            return None, pos
        return name, pos + 4 + name_len + 4

    # Find longest run of valid FNames
    best_run = []
    for start in range(0, min(len(uasset_data), 0x1000), 4):
        names = []
        pos = start
        for _ in range(1200):
            name, nxt = try_fname(uasset_data, pos)
            if name is None:
                break
            names.append(name)
            pos = nxt
        if len(names) > len(best_run):
            best_run = names

    return best_run


def find_variable_comparisons(
    uexp_data: bytes,
    names: list[str],
    max_value: int = 50,
) -> dict[str, list[int]]:
    """Find all \"EX_LocalVariable(FName) + value\" patterns in bytecode.

    Pattern: 0x00 [FName_idx:uint32] [value:int32]

    This catches both property initializations (in class defaults) and
    bytecode comparisons (in function scripts). For Blueprint vars,
    look for names WITHOUT '/' (asset paths are property defaults).
    """
    from collections import defaultdict

    results = defaultdict(set)

    for i in range(len(uexp_data) - 9):
        if uexp_data[i] != 0x00:
            continue
        fname_idx = struct.unpack_from("<I", uexp_data, i + 1)[0]
        if not (0 <= fname_idx < len(names)):
            continue
        val = struct.unpack_from("<I", uexp_data, i + 5)[0]
        if 0 <= val <= max_value:
            results[names[fname_idx]].add(val)

    return {k: sorted(v) for k, v in results.items()}


def analyze_blueprint_vars(uasset_path: str, uexp_path: str | None = None) -> dict:
    """Analyze a Blueprint's variable comparisons.

    Returns dict with:
        - variables: {name: [compared_values]}
        - name_count: total FNames parsed
    """
    import os

    with open(uasset_path, "rb") as f:
        uasset = f.read()

    if uexp_path is None:
        uexp_path = uasset_path.replace(".uasset", ".uexp")

    if not os.path.exists(uexp_path):
        return {"error": f"Companion .uexp not found: {uexp_path}"}

    with open(uexp_path, "rb") as f:
        uexp = f.read()

    names = parse_name_table(uasset)
    comparisons = find_variable_comparisons(uexp, names)

    # Filter: separate BP variable comparisons from property initializations
    var_comparisons = {}
    bp_mappings = {}  # path → value (property initializations)
    
    for name, vals in comparisons.items():
        if "/Game/" in name:
            bp_mappings[name] = vals
        elif not name.startswith("Default__") and not name.startswith("CallFunc_"):
            # Only show variables with 2+ distinct values (filters out property defaults)
            if len(vals) >= 2:
                var_comparisons[name] = vals
        elif "/Game/" in name:
            bp_mappings[name] = vals

    return {
        "variables": var_comparisons,
        "bp_mappings": bp_mappings,
        "name_count": len(names),
    }
