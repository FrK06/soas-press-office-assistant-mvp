from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


INPUT_JSON = Path("data/evaluation/evaluation_results.json")
INPUT_CSV = Path("data/evaluation/evaluation_detailed_results.csv")
OUTPUT_DIR = Path("data/evaluation")


def load_results(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Evaluation results not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_case_rows(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Evaluation case results not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def format_metric(value: float) -> str:
    formatted = f"{value:.4f}".rstrip("0").rstrip(".")
    if "." not in formatted:
        formatted += ".0"
    return formatted


def compute_concentration(case_rows: list[dict]) -> list[dict]:
    counter: Counter[str] = Counter()
    for row in case_rows:
        experts = [item.strip() for item in row.get("predicted_experts", "").split("|") if item.strip()]
        counter.update(experts)
    return [{"expert": expert, "count": count} for expert, count in counter.most_common(10)]


def compute_verification_counts(case_rows: list[dict]) -> tuple[int, int]:
    recognised = sum(1 for row in case_rows if row.get("recognised_outlet") == "True")
    manual_review = sum(1 for row in case_rows if row.get("manual_review_required") == "True")
    return recognised, manual_review


def plot_main_metrics(metrics: dict, output_path: Path) -> None:
    labels = [
        "Top-1",
        "Top-3",
        "Top-5",
        "Precision@3",
        "MRR",
        "Coverage",
        "Approval Proxy",
    ]
    values = [
        metrics["top1_accuracy"],
        metrics["top3_accuracy"],
        metrics["top5_accuracy"],
        metrics["precision_at_3"],
        metrics["mrr"],
        metrics["coverage"],
        metrics["approval_proxy_rate"],
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, values)

    ax.set_title("Figure 12. Automated evaluation metrics for the final accepted system")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            format_metric(value),
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_concentration(case_rows: list[dict], output_path: Path) -> None:
    concentration = compute_concentration(case_rows)
    if not concentration:
        raise ValueError("No recommendation concentration data found.")

    experts = [item["expert"] for item in concentration][::-1]
    counts = [item["count"] for item in concentration][::-1]

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(experts, counts)

    ax.set_title("Figure 13. Recommendation concentration across the final evaluation set")
    ax.set_xlabel("Number of recommendations")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    for bar, value in zip(bars, counts):
        ax.text(
            value + 0.1,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            fontsize=10,
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_verification_distribution(case_rows: list[dict], output_path: Path) -> None:
    recognised_count, manual_review_count = compute_verification_counts(case_rows)
    total = len(case_rows)
    labels = [
        f"Recognised outlet\n({recognised_count}/{total})",
        f"Manual review required\n({manual_review_count}/{total})",
    ]
    values = [recognised_count, manual_review_count]

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        values,
        labels=labels,
        autopct=lambda p: f"{p:.1f}%",
        startangle=90,
    )
    ax.set_title("Figure 14. Verification pathway distribution across the final evaluation set")
    ax.axis("equal")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_shortlist_depth(metrics: dict, output_path: Path) -> None:
    labels = ["Top-1", "Top-3", "Top-5"]
    values = [
        metrics["top1_accuracy"],
        metrics["top3_accuracy"],
        metrics["top5_accuracy"],
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(labels, values, marker="o")
    ax.set_title("Figure 15. Retrieval performance by shortlist depth")
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1.05)
    ax.grid(True, linestyle="--", alpha=0.4)

    for x, y in zip(labels, values):
        ax.text(x, y + 0.03, format_metric(y), ha="center", va="bottom", fontsize=10)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_hit_vs_precision(metrics: dict, output_path: Path) -> None:
    labels = ["Top-3 Accuracy", "Precision@3"]
    values = [
        metrics["top3_accuracy"],
        metrics["precision_at_3"],
    ]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, values)

    ax.set_title("Figure 16. Shortlist hit rate versus shortlist precision")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            format_metric(value),
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = load_results(INPUT_JSON)
    case_rows = load_case_rows(INPUT_CSV)
    metrics = results["metrics"]

    if len(case_rows) != metrics["n_cases"]:
        raise ValueError(
            f"Mismatch between JSON n_cases ({metrics['n_cases']}) and detailed CSV rows ({len(case_rows)})."
        )

    files = {
        "figure_12_main_metrics.png": lambda p: plot_main_metrics(metrics, p),
        "figure_13_concentration.png": lambda p: plot_concentration(case_rows, p),
        "figure_14_verification_distribution.png": lambda p: plot_verification_distribution(case_rows, p),
        "figure_15_shortlist_depth.png": lambda p: plot_shortlist_depth(metrics, p),
        "figure_16_hit_vs_precision.png": lambda p: plot_hit_vs_precision(metrics, p),
    }

    for filename, plotter in files.items():
        path = OUTPUT_DIR / filename
        plotter(path)
        print(f"Saved: {path}")


if __name__ == "__main__":
    main()
