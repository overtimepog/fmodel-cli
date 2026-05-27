"""Unit tests for PAK parser — RED phase: these WILL fail (module doesn't exist yet)."""
import os
import pytest

# The module we're building — doesn't exist yet (RED)
# from cli_anything.fmodel.core.pak_parser import PakParser

# Test fixture: UWDF PAK file
UWDF_PAK = (
    "/mnt/c/Program Files (x86)/Steam/steamapps/common/"
    "Ultimate Wall Defense Force/UWDF/UWDF/Content/Paks/"
    "UWDF-WindowsNoEditor.pak"
)


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakFooter:
    """PAK footer parsing — the first thing any PAK reader needs."""

    def test_pak_footer_magic(self):
        """PAK footer should contain the magic 0x5A6F12E1."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        footer = parser.read_footer()
        assert footer["magic"] == 0x5A6F12E1
        assert footer["version"] == 8

    def test_pak_footer_index_info(self):
        """PAK footer should point to the index."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        footer = parser.read_footer()
        assert footer["index_offset"] > 0
        assert footer["index_size"] > 10000  # 373KB for UWDF
        assert footer["index_offset"] + footer["index_size"] < os.path.getsize(UWDF_PAK)


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakIndex:
    """PAK index parsing — lists all files in the archive."""

    def test_pak_index_has_entries(self):
        """PAK index should contain 2000+ file entries."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        entries = parser.list_files()
        assert len(entries) > 2000

    def test_pak_index_entries_have_paths(self):
        """Every entry should have a valid path string."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        entries = parser.list_files()
        for entry in entries[:100]:
            assert "name" in entry
            assert "/" in entry["name"] or "\\" in entry["name"]
            assert len(entry["name"]) > 3

    def test_pak_index_entries_have_sizes(self):
        """Every entry should have offset and size fields."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        entries = parser.list_files()
        for entry in entries[:100]:
            assert "offset" in entry
            assert "compressed_size" in entry
            assert "uncompressed_size" in entry
            assert entry["compressed_size"] > 0
            assert entry["uncompressed_size"] > 0


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakExtract:
    """PAK file extraction."""

    def test_extract_single_file(self):
        """Extract a known file by path and verify it exists."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        entries = parser.list_files()

        # Find a config file
        config_files = [e for e in entries if ".ini" in e["name"]]
        assert len(config_files) > 0

        target = config_files[0]
        data = parser.extract_file(target["name"])
        assert data is not None
        assert len(data) == target["uncompressed_size"]

    def test_extract_ini_contains_expected_keys(self):
        """Extracted .ini should contain expected section headers."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        entries = parser.list_files()

        engine_ini = [e for e in entries if "DefaultEngine.ini" in e["name"]]
        assert len(engine_ini) == 1

        data = parser.extract_file(engine_ini[0]["name"])
        text = data.decode("utf-8", errors="replace")
        assert "[/Script/Engine.Engine]" in text
        assert "GameName" in text


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakListFilter:
    """Filtering PAK file lists."""

    def test_list_filter_by_extension(self):
        """List files filtered by extension."""
        from cli_anything.fmodel.core.pak_parser import PakParser

        parser = PakParser(UWDF_PAK)
        entries = parser.list_files()

        uassets = [e for e in entries if e["name"].endswith(".uasset")]
        configs = [e for e in entries if ".ini" in e["name"]]
        pngs = [e for e in entries if e["name"].endswith(".png")]

        assert len(uassets) > 500
        assert len(configs) > 10
        assert len(pngs) > 100
