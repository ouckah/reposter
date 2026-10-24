import os
import stat

import pytest

from scripts.youtube_auth import save_token


def test_token_saved_privately_and_not_printed(tmp_path, capsys):
    destination = tmp_path / ".secrets" / "token.txt"
    save_token("synthetic-test-value", destination)
    assert destination.read_text() == "synthetic-test-value"
    if os.name == "posix":
        assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert capsys.readouterr().out == ""


def test_existing_token_not_overwritten(tmp_path):
    destination = tmp_path / "token.txt"
    destination.write_text("original")
    with pytest.raises(FileExistsError):
        save_token("replacement", destination)
    assert destination.read_text() == "original"


def test_token_writer_does_not_follow_symlink(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("original")
    destination = tmp_path / "token.txt"
    destination.symlink_to(target)
    with pytest.raises(FileExistsError):
        save_token("replacement", destination)
    assert target.read_text() == "original"
