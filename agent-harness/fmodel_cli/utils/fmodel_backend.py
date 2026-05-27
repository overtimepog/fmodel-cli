"""FModel backend integration.

Wraps FModel.exe for GUI operations. FModel is a Windows-only .NET/WPF app
with no native CLI. This backend detects FModel installations and provides
subprocess wrappers for launching the GUI and exporting assets.

For headless operations (PAK parsing, uasset inspection), the pure-Python
parsers in core/ are used instead — no FModel dependency needed.

Future: build a thin C# CLI wrapper using CUE4Parse libraries for headless
export of textures, meshes, and animations.
"""
import os
import shutil
import subprocess
import sys


def find_fmodel() -> str | None:
    """Locate FModel.exe on the system. Returns path or None."""
    # Common install locations
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "FModel", "FModel.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "FModel", "FModel.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "FModel", "FModel.exe"),
        os.path.expanduser("~/Desktop/FModel/FModel.exe"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    # Try PATH
    found = shutil.which("FModel")
    return found


def launch_fmodel(pak_path: str | None = None) -> subprocess.Popen | None:
    """Launch FModel GUI. Optionally with a PAK path.

    Returns the Popen process handle, or None if FModel not found.
    """
    fmodel = find_fmodel()
    if not fmodel:
        raise RuntimeError(
            "FModel not found. Install from: https://github.com/4sval/FModel/releases\n"
            "The CLI can parse PAK files and inspect .uasset files without FModel.\n"
            "FModel is only needed for GUI browsing and advanced export features."
        )

    args = [fmodel]
    if pak_path:
        args.extend(["--pak", pak_path])

    return subprocess.Popen(args)


def is_fmodel_available() -> bool:
    """Check if FModel is installed and accessible."""
    return find_fmodel() is not None
