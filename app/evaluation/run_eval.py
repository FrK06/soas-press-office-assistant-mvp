from __future__ import annotations

import json

from app.evaluation.common import (
    DATASET_PATH,
    OUTPUT_DIR,
    EvalCase,
    aggregate_metrics,
    evaluate_case,
    load_dataset,
    write_detailed_csv,
)


OUTPUT_JSON = OUTPUT_DIR / 'evaluation_results.json'
OUTPUT_CSV = OUTPUT_DIR / 'evaluation_detailed_results.csv'


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(DATASET_PATH)
    print(f'Loaded {len(dataset)} evaluation cases')

    case_results = []
    for case in dataset:
        result = evaluate_case(case)
        case_results.append(result)
        print(
            f"[{case.test_id}] "
            f"Top1={result['top1_hit']} "
            f"Top3={result['top3_hit']} "
            f"Top5={result['top5_hit']} "
            f"MRR={result['reciprocal_rank']}"
        )

    metrics = aggregate_metrics(case_results)
    output = {
        'metrics': metrics,
        'cases': case_results,
    }

    OUTPUT_JSON.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8',
    )
    write_detailed_csv(case_results, OUTPUT_CSV)

    print('\nEvaluation complete')
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f'\nSaved JSON results to: {OUTPUT_JSON}')
    print(f'Saved CSV results to: {OUTPUT_CSV}')


if __name__ == '__main__':
    main()
