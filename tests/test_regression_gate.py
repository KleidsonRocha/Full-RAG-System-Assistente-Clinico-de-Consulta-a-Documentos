import pytest

from eval.regression import evaluate_regression, summarize_rows


def make_row(
    *,
    row_id="case_001",
    category="bula",
    status="ok",
    retrieval_status="ok",
    generation_status="ok",
    checks=None,
    retrieval_metrics=None,
):
    return {
        "id": row_id,
        "category": category,
        "status": status,
        "retrieval_status": retrieval_status,
        "generation_status": generation_status,
        "checks": checks or {
            "resposta_presente": True,
            "fonte_chunk": True,
        },
        "retrieval_metrics": retrieval_metrics,
        "latency_ms": 100,
    }


def test_summarize_rows_calculates_regression_metrics():
    rows = [
        make_row(
            retrieval_metrics={
                "context_recall_at_2": 1.0,
                "context_precision_at_2": 0.5,
                "hit_rate_at_1": 1.0,
                "hit_rate_at_2": 1.0,
                "hit_rate_at_5": 1.0,
                "hit_rate_at_10": 1.0,
                "mrr_at_10": 1.0,
            },
        ),
        make_row(
            row_id="case_002",
            status="falha",
            retrieval_status="falha",
            generation_status="falha",
            retrieval_metrics={
                "context_recall_at_2": 0.0,
                "context_precision_at_2": 0.0,
                "hit_rate_at_1": 0.0,
                "hit_rate_at_2": 0.0,
                "hit_rate_at_5": 1.0,
                "hit_rate_at_10": 1.0,
                "mrr_at_10": 0.5,
            },
        ),
        make_row(
            row_id="fora_001",
            category="fora_do_acervo",
            checks={"resposta_presente": True, "recusa_esperada": True},
            retrieval_metrics=None,
        ),
    ]

    summary = summarize_rows(rows)

    assert summary["automatic_success_rate"] == pytest.approx(2 / 3)
    assert summary["retrieval_success_rate"] == pytest.approx(1 / 2)
    assert summary["generation_success_rate"] == pytest.approx(2 / 3)
    assert summary["refusal_success_rate"] == 1.0
    assert summary["context_recall_at_2"] == pytest.approx(0.5)
    assert summary["mrr_at_10"] == pytest.approx(0.75)


def test_evaluate_regression_passes_when_metrics_respect_thresholds():
    summary = {
        "retrieval_success_rate": 0.75,
        "hit_rate_at_10": 0.875,
    }
    config = {
        "baseline": {
            "retrieval_success_rate": 0.75,
            "hit_rate_at_10": 0.875,
        },
        "thresholds": {
            "retrieval_success_rate": {"min": 0.7, "max_drop": 0.05},
            "hit_rate_at_10": {"min": 0.8, "max_drop": 0.075},
        },
    }

    assert evaluate_regression(summary, config) == []


def test_evaluate_regression_reports_metric_drop():
    summary = {
        "retrieval_success_rate": 0.68,
    }
    config = {
        "baseline": {
            "retrieval_success_rate": 0.75,
        },
        "thresholds": {
            "retrieval_success_rate": {"min": 0.7, "max_drop": 0.05},
        },
    }

    failures = evaluate_regression(summary, config)

    assert failures == [
        {
            "metric": "retrieval_success_rate",
            "current": 0.68,
            "required": 0.7,
            "baseline": 0.75,
            "min": 0.7,
            "max_drop": 0.05,
        }
    ]
