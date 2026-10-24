from scripts.check_public import check


def fixture(root):
    (root / "release-files.txt").write_text("release-files.txt\nREADME.md\n.env.example\n")
    (root / "README.md").write_text("Demo by ouckah. Contact: ouckah@gmail.com\n")
    (root / ".env.example").write_text("EXAMPLE_TOKEN=\n")


def test_clean_fixture_passes(tmp_path):
    fixture(tmp_path)
    assert check(tmp_path) == []


def test_unapproved_files_fail(tmp_path):
    fixture(tmp_path)
    (tmp_path / ".env").write_text("synthetic local state")
    assert "Unapproved file: .env" in check(tmp_path)


def test_populated_template_fails_without_echoing_value(tmp_path):
    fixture(tmp_path)
    (tmp_path / ".env.example").write_text("EXAMPLE_TOKEN=synthetic-private-value\n")
    issues = check(tmp_path)
    assert any("populated" in issue for issue in issues)
    assert all("synthetic-private-value" not in issue for issue in issues)


def test_symlink_fails(tmp_path):
    fixture(tmp_path)
    (tmp_path / "linked").symlink_to(tmp_path / "README.md")
    assert any("Symlink" in issue for issue in check(tmp_path))


def test_missing_file_fails(tmp_path):
    fixture(tmp_path)
    (tmp_path / "README.md").unlink()
    assert "Missing release file: README.md" in check(tmp_path)


def test_path_traversal_fails(tmp_path):
    fixture(tmp_path)
    (tmp_path / "release-files.txt").write_text("../outside.txt\n")
    assert check(tmp_path) == ["Unsafe manifest path"]
