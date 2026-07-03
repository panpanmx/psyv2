import json
import subprocess
import sys
from pathlib import Path


def test_run_evaluation_script_generates_report(tmp_path: Path) -> None:
    report_path = tmp_path / "evaluation_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_evaluation.py",
            "--report-path",
            str(report_path),
        ],
        cwd=Path(__file__).parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["case_count"] == 55
    assert len(report["cases"]) == 55
    assert report["summary"]["case_count"] == 55
    assert "pass_rate" in report["summary"]
    assert "p95_latency_ms" in report["summary"]
    assert all("latency_ms" in case for case in report["cases"])
