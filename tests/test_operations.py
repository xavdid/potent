from pathlib import Path
from unittest.mock import patch

from potent.operations.raw_command import Config, RawCommand


@patch("subprocess.run")
def test_os_errors_handled(mock_run, tmp_path: Path):
    mock_run.side_effect = FileNotFoundError(
        "[Errno 2] No such file or directory: 'cool'"
    )

    result = RawCommand(slug="raw-command", config=Config(arguments=[])).run(tmp_path)

    # should fail, but not throw
    assert result.success is False
