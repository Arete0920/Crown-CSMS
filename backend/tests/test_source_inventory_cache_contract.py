"""Characterize the shared source snapshot without relaxing sentinel assertions."""

from ._source_inventory import repository_python_files, repository_python_source


def test_source_inventory_matches_original_inclusive_repo_semantics(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "a.py").write_text("school_id = 1\n", encoding="utf-8")
    (tmp_path / "nested" / "b.py").write_text("AuditLog = 'ok'\n", encoding="utf-8")
    (tmp_path / "not_python.txt").write_text("Should not be read", encoding="utf-8")

    repository_python_files.cache_clear()
    repository_python_source.cache_clear()
    try:
        files = repository_python_files(tmp_path)
        assert set(files) == {tmp_path / "a.py", tmp_path / "nested" / "b.py"}
        expected = "".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)
        assert repository_python_source(tmp_path) == expected
        assert "school_id" in expected
        assert "AuditLog" in expected
        assert "Should not be read" not in expected

        assert repository_python_source(tmp_path) is repository_python_source(tmp_path)
        assert repository_python_source.cache_info().hits == 1
    finally:
        repository_python_files.cache_clear()
        repository_python_source.cache_clear()
