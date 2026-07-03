from app.observability.metrics import compute_evaluation_metrics


def test_compute_evaluation_metrics_counts_crisis_recall() -> None:
    metrics = compute_evaluation_metrics(
        [
            {"expected_crisis": True, "actual_crisis": True, "safe_response": True},
            {"expected_crisis": True, "actual_crisis": False, "safe_response": False},
        ]
    )

    assert metrics["crisis_recall"] == 0.5
