from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.evaluation.common import (
    DATASET_PATH,
    OUTPUT_DIR,
    build_output,
    evaluate_case,
    load_dataset,
    write_detailed_csv,
)


DEFAULT_OUTPUT_JSON_NAME = 'evaluation_results.json'
DEFAULT_OUTPUT_CSV_NAME = 'evaluation_detailed_results.csv'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the SOAS Press Office Assistant benchmark evaluation.')
    parser.add_argument('--dataset-path', type=Path, default=DATASET_PATH)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT_DIR)
    parser.add_argument('--label', default='cleaned_default')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_json = output_dir / DEFAULT_OUTPUT_JSON_NAME
    output_csv = output_dir / DEFAULT_OUTPUT_CSV_NAME

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = load_dataset(args.dataset_path)
    print(f'Loaded {len(dataset)} evaluation cases from {args.dataset_path}')

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

    output = build_output(case_results, dataset_path=args.dataset_path, label=args.label)
    output_json.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8',
    )
    write_detailed_csv(case_results, output_csv)

    print('\nEvaluation complete')
    print(json.dumps(output['metrics'], indent=2, ensure_ascii=False))
    print(f'\nSaved JSON results to: {output_json}')
    print(f'Saved CSV results to: {output_csv}')


if __name__ == '__main__':
    main()
