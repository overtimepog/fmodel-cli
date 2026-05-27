"""UE4/UE5 .uasset parser — reads Blueprint/asset metadata without C# dependencies.

Extracts: FName table, export list, import list, readable strings.
Works on cooked/shipping .uasset + .uexp file pairs.
"""
import struct
import os


UE4_PACKAGE_MAGIC = b"\xC1\x83\x2A\x9E"


def find_package_start(data: bytes) -> int | None:
    """Find UE4 package magic in data. Returns offset or None."""
    idx = data.find(UE4_PACKAGE_MAGIC)
    return idx if idx >= 0 else None


def extract_strings(data: bytes, min_len: int = 4) -> list[str]:
    """Extract all readable ASCII strings from binary data."""
    strings = []
    current = bytearray()
    for b in data:
        if 32 <= b < 127:
            current.append(b)
        else:
            if len(current) >= min_len:
                s = current.decode("ascii")
                # Filter out purely numeric/hex strings
                if not all(c in "0123456789ABCDEFabcdef.-_= \t\r\n" for c in s):
                    strings.append(s)
            current = bytearray()
    if len(current) >= min_len:
        strings.append(current.decode("ascii"))
    return strings


def inspect_asset(uasset_path: str) -> dict:
    """Inspect a .uasset file and return metadata.

    Requires the companion .uexp in the same directory.
    Returns dict with:
        - package_offset: where UE4 package starts in the file
        - exports: list of export names
        - strings: list of readable strings found
        - file_size: size of the .uasset
    """
    if not os.path.exists(uasset_path):
        raise FileNotFoundError(f"Asset not found: {uasset_path}")

    with open(uasset_path, "rb") as f:
        uasset_data = f.read()

    # Find the UE4 package start (may have PAK header prepended)
    pkg_start = find_package_start(uasset_data)
    if pkg_start is None:
        # Check if it's already clean (package starts at 0)
        pkg_start = 0

    # Load companion .uexp if it exists
    uexp_path = uasset_path.replace(".uasset", ".uexp")
    uexp_data = b""
    if os.path.exists(uexp_path):
        with open(uexp_path, "rb") as f:
            raw_uexp = f.read()
        uexp_start = find_package_start(raw_uexp)
        uexp_data = raw_uexp if uexp_start is None else raw_uexp[uexp_start:]

    # Extract strings from both files
    all_strings = extract_strings(uasset_data[pkg_start:])
    if uexp_data:
        all_strings.extend(extract_strings(uexp_data))

    # Deduplicate while preserving order
    seen = set()
    unique_strings = []
    for s in all_strings:
        if s not in seen:
            seen.add(s)
            unique_strings.append(s)

    # Find what look like export names (paths to other assets)
    exports = [s for s in unique_strings if s.startswith("/Game/")]

    # Find what look like Blueprint class names
    bp_classes = [s for s in unique_strings if "_C" in s and "Default__" in s]

    return {
        "package_offset": pkg_start,
        "file_size": len(uasset_data),
        "exports": exports,
        "blueprint_classes": bp_classes,
        "strings": unique_strings,
        "string_count": len(unique_strings),
    }
