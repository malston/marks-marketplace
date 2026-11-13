"""Retries must re-resolve the target window, not reuse a dead window ID.

macOS invalidates a window ID as soon as the window goes away. An app that
briefly shows a second window -- a settings modal, a sheet -- can therefore be
resolved as the target, and the ID dies the moment that window closes. Every
remaining retry then addresses a window that no longer exists, so retrying
cannot help unless the window is looked up again.
"""

from pathlib import Path

import pytest

from screen_recorder import actions
from screen_recorder.models import (
    CaptureBackend,
    CaptureError,
    OutputFormat,
    RecordingConfig,
    VerificationResult,
    VerificationStrategy,
    VideoInfo,
    WindowBounds,
    WindowTarget,
)

DEAD_WINDOW_ID = 64976
LIVE_WINDOW_ID = 64907


def _target(window_id: int) -> WindowTarget:
    return WindowTarget(
        window_id=window_id,
        app_name="Claude",
        window_title="Claude",
        pid=14896,
        bounds=WindowBounds(x=310, y=70, width=1454, height=964),
    )


@pytest.fixture
def recorded_windows(monkeypatch, tmp_path):
    """Stub the capture stack; return the window IDs recording was attempted on.

    The first lookup returns the doomed window (mimicking a transient modal
    being matched first); later lookups return the surviving one. Capture fails
    for any window that is not currently alive.
    """
    attempted: list[int] = []
    lookups = iter([_target(DEAD_WINDOW_ID)])
    fallback = _target(LIVE_WINDOW_ID)

    def fake_find_target_window(config):
        return next(lookups, fallback)

    def fake_record_window_with_sck(window_id, output_path, duration, fps=30):
        attempted.append(window_id)
        if window_id != LIVE_WINDOW_ID:
            raise CaptureError(f"Window {window_id} not found")
        Path(output_path).write_bytes(b"fake movie")

    monkeypatch.setattr(actions, "find_target_window", fake_find_target_window)
    monkeypatch.setattr(actions, "record_window_with_sck", fake_record_window_with_sck)
    monkeypatch.setattr(actions, "is_video_streaming_supported", lambda: True)
    monkeypatch.setattr(actions, "_detect_space_switch_needed", lambda target: _NoSpaceSwitch())
    monkeypatch.setattr(
        actions,
        "run_verifications",
        lambda path, config: (
            VerificationResult(
                strategy=VerificationStrategy.BASIC, passed=True, message="ok"
            ),
        ),
    )
    monkeypatch.setattr(
        actions,
        "get_video_info",
        lambda path: VideoInfo(
            path=Path(path),
            duration_seconds=1.0,
            frame_count=10,
            fps=10.0,
            width=1454,
            height=964,
            file_size_bytes=10,
            format_name="mov",
        ),
    )
    return attempted


class _NoSpaceSwitch:
    """Stand-in for space context indicating no Space switch is required."""

    original_space_index = None
    target_space_index = None
    switched = False


def _config(tmp_path: Path) -> RecordingConfig:
    return RecordingConfig(
        app_name="Claude",
        duration_seconds=1.0,
        output_path=str(tmp_path / "out.mov"),
        output_format=OutputFormat.MOV,
        capture_backend=CaptureBackend.SCREENCAPTUREKIT,
        activate_first=False,
        max_retries=3,
        retry_delay_ms=0,
    )


def test_retry_rebinds_to_a_live_window(recorded_windows, tmp_path):
    """A retry after the target dies must look the window up again."""
    result = actions.record_verified(_config(tmp_path))

    assert recorded_windows == [DEAD_WINDOW_ID, LIVE_WINDOW_ID], (
        "expected the retry to re-resolve the window; "
        f"instead recording was attempted on {recorded_windows}"
    )
    assert result.verified
    assert result.window_id == LIVE_WINDOW_ID
    assert result.attempt == 2


def test_first_attempt_does_not_re_resolve(monkeypatch, tmp_path):
    """A recording that works first time looks the window up exactly once."""
    lookups: list[int] = []

    def fake_find_target_window(config):
        lookups.append(1)
        return _target(LIVE_WINDOW_ID)

    monkeypatch.setattr(actions, "find_target_window", fake_find_target_window)
    monkeypatch.setattr(
        actions,
        "record_window_with_sck",
        lambda window_id, output_path, duration, fps=30: Path(output_path).write_bytes(b"m"),
    )
    monkeypatch.setattr(actions, "is_video_streaming_supported", lambda: True)
    monkeypatch.setattr(actions, "_detect_space_switch_needed", lambda target: _NoSpaceSwitch())
    monkeypatch.setattr(
        actions,
        "run_verifications",
        lambda path, config: (
            VerificationResult(
                strategy=VerificationStrategy.BASIC, passed=True, message="ok"
            ),
        ),
    )

    result = actions.record_verified(_config(tmp_path))

    assert result.verified
    assert len(lookups) == 1, f"window resolved {len(lookups)} times, expected 1"


def test_zero_retries_reports_a_recording_error(tmp_path):
    """A retry budget of zero must explain itself, not crash internally."""
    config = RecordingConfig(
        app_name="Finder",
        duration_seconds=1.0,
        output_path=str(tmp_path / "out.mov"),
        output_format=OutputFormat.MOV,
        max_retries=0,
    )

    with pytest.raises(actions.RecordingError) as excinfo:
        actions.record_verified(config)

    assert "max_retries" in str(excinfo.value)


def test_zero_retries_reports_a_recording_error(tmp_path):
    """A retry budget of zero must explain itself, not crash internally."""
    config = RecordingConfig(
        app_name="Finder",
        duration_seconds=1.0,
        output_path=str(tmp_path / "out.mov"),
        output_format=OutputFormat.MOV,
        max_retries=0,
    )

    with pytest.raises(actions.RecordingError) as excinfo:
        actions.record_verified(config)

    assert "max_retries" in str(excinfo.value)


def test_rebind_is_a_noop_without_a_window_target():
    """Full-screen recording has no window to re-resolve."""
    ctx = actions._RecordingContext(
        config=RecordingConfig(full_screen=True),
        target=None,
        region=None,
        raw_path=Path("raw.mov"),
        final_path=Path("out.mov"),
        settings={},
    )

    actions._rebind_target(ctx)

    assert ctx.target is None
    assert ctx.region is None


def test_every_retry_is_not_spent_on_the_same_dead_id(monkeypatch, tmp_path):
    """With the window permanently gone, retries must not all reuse one dead ID."""
    attempted: list[int] = []

    def fake_find_target_window(config):
        # A fresh (still doomed) ID each lookup, as macOS would hand out.
        return _target(DEAD_WINDOW_ID + len(attempted))

    def fake_record_window_with_sck(window_id, output_path, duration, fps=30):
        attempted.append(window_id)
        raise CaptureError(f"Window {window_id} not found")

    monkeypatch.setattr(actions, "find_target_window", fake_find_target_window)
    monkeypatch.setattr(actions, "record_window_with_sck", fake_record_window_with_sck)
    monkeypatch.setattr(actions, "is_video_streaming_supported", lambda: True)
    monkeypatch.setattr(actions, "_detect_space_switch_needed", lambda target: _NoSpaceSwitch())

    with pytest.raises(actions.MaxRetriesError):
        actions.record_verified(_config(tmp_path))

    assert len(set(attempted)) > 1, (
        f"all {len(attempted)} attempts reused the same window ID: {attempted}"
    )
