from pathlib import Path

import pytest

from potent.renderers import BasicRenderer, NoopRenderer
from potent.run_events import (
    DirectorySkipped,
    DirectoryStarted,
    OperationCompleted,
)


class TestNoopRenderer:
    @pytest.fixture
    def renderer(self) -> NoopRenderer:
        return NoopRenderer()

    def test_send_does_nothing(self, capsys: pytest.CaptureFixture, renderer):
        renderer.send(DirectoryStarted(path=Path("some/dir")))
        renderer.send(DirectorySkipped(path=Path("some/other/dir")))
        renderer.send(
            OperationCompleted(
                summary="step",
                result="success",
                output="output",
                cmd="echo hi",
                path=Path("some/dir"),
            )
        )
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_log_does_nothing(self, capsys: pytest.CaptureFixture, renderer):
        renderer.log("hello")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestBasicRenderer:
    @pytest.fixture
    def renderer(self) -> BasicRenderer:
        return BasicRenderer()

    def test_starts_with_no_skipped_steps(self, renderer: BasicRenderer):
        assert renderer.skipped_steps == []

    def test_log_prints_message(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        renderer.log("hello world")
        captured = capsys.readouterr()
        assert "hello world" in captured.out

    def test_prints_directory_name(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        renderer.send(DirectoryStarted(path=Path("/tmp/my-project")))
        captured = capsys.readouterr()
        assert "my-project" in captured.out
        assert "/tmp/" not in captured.out

    def test_prints_already_finished(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        renderer.send(DirectorySkipped(path=Path("some/other/dir")))
        captured = capsys.readouterr()
        assert "already finished" in captured.out

    def test_success_prints_succeeded(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        renderer.send(
            OperationCompleted(
                summary="install deps",
                result="success",
                output="all good",
                cmd="npm install",
                path=Path("/tmp/proj"),
            )
        )
        captured = capsys.readouterr()
        assert "install deps" in captured.out
        assert "Succeeded" in captured.out
        assert "npm install" in captured.out
        assert "all good" in captured.out

    def test_failure_prints_failed(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        renderer.send(
            OperationCompleted(
                summary="run tests",
                result="failure",
                output="boom",
                cmd="pytest",
                path=Path("/tmp/proj"),
            )
        )
        captured = capsys.readouterr()
        assert "run tests" in captured.out
        assert "Failed" in captured.out
        assert "boom" in captured.out
        assert ">>>" in captured.out

    def test_no_output_shows_placeholder(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        renderer.send(
            OperationCompleted(
                summary="noop step",
                result="success",
                output="",
                path=Path("/tmp/proj"),
            )
        )
        captured = capsys.readouterr()
        assert "no output" in captured.out
        # no cmd means no angle brackets
        assert ">>>" not in captured.out

    def test_skipped_operation_is_collected_not_printed_immediately(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        summary = "i was skipped"
        renderer.send(
            OperationCompleted(
                summary=summary,
                result="skipped",
                output="",
                path=Path("/tmp/proj"),
            )
        )
        assert renderer.skipped_steps == [summary]
        captured = capsys.readouterr()
        # nothing printed yet for the skipped step itself
        assert summary not in captured.out

    def test_skipped_batch_flushed_on_next_non_skip(
        self, renderer: BasicRenderer, capsys: pytest.CaptureFixture
    ):
        renderer.send(
            OperationCompleted(
                summary="skip one",
                result="skipped",
                output="",
                cmd="",
                path=Path("/tmp/proj"),
            )
        )
        renderer.send(
            OperationCompleted(
                summary="skip two",
                result="skipped",
                output="",
                cmd="",
                path=Path("/tmp/proj"),
            )
        )
        captured = capsys.readouterr()
        assert "skip one" not in captured.out
        assert "skip two" not in captured.out
        assert len(renderer.skipped_steps) == 2

        renderer.send(
            OperationCompleted(
                summary="finally run",
                result="success",
                output="done",
                cmd="",
                path=Path("/tmp/proj"),
            )
        )
        captured = capsys.readouterr()
        assert "skip one" in captured.out
        assert "skip two" in captured.out
        assert "finally run" in captured.out

        # collection should reset after flushing
        assert renderer.skipped_steps == []
