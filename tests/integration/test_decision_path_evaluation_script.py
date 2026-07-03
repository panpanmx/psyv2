import json
import subprocess
import sys
from pathlib import Path


def test_decision_path_evaluation_generates_trace_report_and_chinese_summary(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "decision_path_report.json"
    summary_path = tmp_path / "decision_path_summary_zh.md"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_decision_path_evaluation.py",
            "--report-path",
            str(report_path),
            "--summary-path",
            str(summary_path),
        ],
        cwd=Path(__file__).parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert report_path.exists()
    assert summary_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["case_count"] >= 75
    assert report["summary"]["trace_complete_rate"] == 1.0
    assert "route_match_rate" in report["summary"]
    assert all(case["decision_path"] for case in report["cases"])

    first_step = report["cases"][0]["decision_path"][0]
    assert {"step", "node", "before", "after", "latency_ms", "decision"} <= first_step.keys()

    summary = summary_path.read_text(encoding="utf-8")
    assert "Agent 决策路径评估报告" in summary
    assert "典型决策路径" in summary
