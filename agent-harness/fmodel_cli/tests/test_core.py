"""Unit tests for PAK parser."""
import os
import pytest
from fmodel_cli.core.pak_parser import PakParser

UWDF_PAK = (
    "/mnt/c/Program Files (x86)/Steam/steamapps/common/"
    "Ultimate Wall Defense Force/UWDF/UWDF/Content/Paks/"
    "UWDF-WindowsNoEditor.pak"
)


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakFooter:
    def test_pak_footer_magic(self):
        p = PakParser(UWDF_PAK)
        f = p.read_footer()
        assert f["magic"] == 0x5A6F12E1
        assert f["version"] == 8

    def test_pak_footer_index_info(self):
        p = PakParser(UWDF_PAK)
        f = p.read_footer()
        assert f["index_offset"] > 0
        assert f["index_size"] > 10000
        assert f["index_offset"] + f["index_size"] < os.path.getsize(UWDF_PAK)


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakIndex:
    def test_pak_index_has_entries(self):
        p = PakParser(UWDF_PAK)
        entries = p.list_files()
        assert len(entries) > 2000

    def test_pak_index_entries_have_paths(self):
        p = PakParser(UWDF_PAK)
        for entry in p.list_files()[:100]:
            assert "/" in entry["name"] or "\\" in entry["name"]
            assert len(entry["name"]) > 3

    def test_pak_index_entries_have_sizes(self):
        p = PakParser(UWDF_PAK)
        for entry in p.list_files()[:100]:
            assert entry["compressed_size"] > 0
            assert entry["uncompressed_size"] > 0


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakExtract:
    def test_extract_single_file(self):
        p = PakParser(UWDF_PAK)
        configs = [e for e in p.list_files() if ".ini" in e["name"]]
        assert len(configs) > 0
        data = p.extract_file(configs[0]["name"])
        assert data is not None
        assert len(data) == configs[0]["uncompressed_size"]

    def test_extract_ini_contains_expected_keys(self):
        p = PakParser(UWDF_PAK)
        engine_ini = [e for e in p.list_files() if "DefaultEngine.ini" in e["name"]]
        assert len(engine_ini) == 1
        data = p.extract_file(engine_ini[0]["name"])
        text = data.decode("utf-8", errors="replace")
        assert "[/Script/Engine.Engine]" in text
        assert "GameName" in text


@pytest.mark.skipif(not os.path.exists(UWDF_PAK), reason="UWDF PAK not found")
class TestPakListFilter:
    def test_list_filter_by_extension(self):
        p = PakParser(UWDF_PAK)
        entries = p.list_files()
        uassets = [e for e in entries if e["name"].endswith(".uasset")]
        configs = [e for e in entries if ".ini" in e["name"]]
        pngs = [e for e in entries if e["name"].endswith(".png")]
        assert len(uassets) > 500
        assert len(configs) > 10
        assert len(pngs) > 100
