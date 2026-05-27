"""PAK file parser for Unreal Engine 4/5 .pak archives.

Uses string back-trace parsing — searches for known file extensions
in the index and back-traces to filenames. Robust across PAK versions.
"""
import struct
import os


class PakParser:
    """Parser for Unreal Engine .pak archive files."""

    PAK_MAGIC = 0x5A6F12E1
    _KNOWN_EXTENSIONS = [
        b".uasset\x00", b".uexp\x00", b".ubulk\x00", b".umap\x00",
        b".mp3\x00", b".wav\x00", b".ogg\x00", b".png\x00",
        b".ini\x00", b".json\x00", b".txt\x00", b".csv\x00",
        b".ttf\x00", b".otf\x00",
    ]

    def __init__(self, pak_path: str):
        if not os.path.exists(pak_path):
            raise FileNotFoundError(f"PAK file not found: {pak_path}")
        self.path = pak_path
        self._footer = None
        self._entries = None

    # ── Footer ──────────────────────────────────────────────

    def read_footer(self) -> dict:
        """Parse the PAK footer and return footer info."""
        if self._footer:
            return self._footer

        with open(self.path, "rb") as f:
            f.seek(-256, os.SEEK_END)
            tail = f.read(256)

            magic_le = b"\xE1\x12\x6F\x5A"
            idx = tail.find(magic_le)
            if idx == -1:
                raise ValueError("PAK footer magic not found")

            footer_offset = os.path.getsize(self.path) - 256 + idx
            f.seek(footer_offset)

            magic = struct.unpack("<I", f.read(4))[0]
            version = struct.unpack("<I", f.read(4))[0]
            index_offset = struct.unpack("<Q", f.read(8))[0]
            index_size = struct.unpack("<Q", f.read(8))[0]
            index_hash = f.read(20)

        self._footer = {
            "magic": magic,
            "version": version,
            "index_offset": index_offset,
            "index_size": index_size,
            "footer_offset": footer_offset,
            "index_hash": index_hash.hex(),
        }
        return self._footer

    # ── Index / File Listing ─────────────────────────────────

    def list_files(self) -> list[dict]:
        """Return all files in the PAK using string back-trace parsing."""
        if self._entries:
            return self._entries

        footer = self.read_footer()

        with open(self.path, "rb") as f:
            f.seek(footer["index_offset"])
            index_data = f.read(footer["index_size"])

        # Find all filename positions by searching for known extensions
        # and back-tracing to the filename start
        found = {}  # filename_start_pos -> (name, meta_start)

        for marker in self._KNOWN_EXTENSIONS:
            search_pos = 0
            while True:
                idx = index_data.find(marker, search_pos)
                if idx == -1:
                    break
                fname_end = idx + len(marker) - 1  # position of null terminator

                # Back-trace to find the filename start
                fname_start = fname_end
                while fname_start > 0:
                    b = index_data[fname_start - 1]
                    if b < 32 or b > 126:
                        break
                    fname_start -= 1

                # Verify the length prefix looks reasonable
                len_prefix_pos = fname_start - 4
                if len_prefix_pos >= 0:
                    stored_len = struct.unpack_from("<I", index_data, len_prefix_pos)[0]
                    actual_len = fname_end - fname_start
                    # Allow ±1 tolerance (null terminator handling)
                    if abs(stored_len - actual_len) <= 1 or stored_len == actual_len + 1:
                        name = index_data[fname_start:fname_end].decode("ascii", errors="replace")
                        meta_start = fname_end + 1  # position after null terminator
                        found[fname_start] = (name, meta_start)

                search_pos = idx + 1

        # Sort by position in index and parse metadata
        entries = []
        for fname_start in sorted(found.keys()):
            name, meta_start = found[fname_start]

            if meta_start + 28 > len(index_data):
                continue

            # Read metadata: offset(8), comp_size(8), uncomp_size(8), comp_method(4)
            raw = index_data[meta_start:meta_start + 28]
            offset = struct.unpack_from("<Q", raw, 0)[0]
            compressed_size = struct.unpack_from("<Q", raw, 8)[0]
            uncompressed_size = struct.unpack_from("<Q", raw, 16)[0]
            comp_method = struct.unpack_from("<I", raw, 24)[0]

            # Sanity check: offset should be within file, sizes should be positive
            if compressed_size > 0 and uncompressed_size > 0:
                entries.append({
                    "name": name,
                    "offset": offset,
                    "compressed_size": compressed_size,
                    "uncompressed_size": uncompressed_size,
                    "compression_method": comp_method,
                })

        self._entries = entries
        return entries

    # ── Extraction ───────────────────────────────────────────

    def extract_file(self, name: str) -> bytes | None:
        """Extract a single file by its PAK-internal path name."""
        entries = self.list_files()
        for entry in entries:
            if entry["name"] == name:
                with open(self.path, "rb") as f:
                    f.seek(entry["offset"])
                    return f.read(entry["compressed_size"])
        return None

    def extract_all(self, output_dir: str, filter_pattern: str | None = None) -> list[str]:
        """Extract files matching filter_pattern to output_dir."""
        entries = self.list_files()
        extracted = []
        for entry in entries:
            if filter_pattern and filter_pattern not in entry["name"]:
                continue
            data = self.extract_file(entry["name"])
            if data is None:
                continue
            out_path = os.path.join(output_dir, entry["name"])
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)
            extracted.append(out_path)
        return extracted
