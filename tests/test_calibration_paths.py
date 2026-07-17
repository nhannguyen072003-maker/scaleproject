from pathlib import Path

from calibration import calibration_manager


def test_calibration_path_is_based_on_project_root(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    expected = Path(__file__).resolve().parents[1] / "measurement" / "calibration.json"

    assert calibration_manager.get_calibration_path() == expected
