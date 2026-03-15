from pathlib import Path

from app.evaluation.run_ui_smoke_tests import load_smoke_cases


REGRESSION_IDS = {
    'UI003',
    'UI007',
    'UI012',
    'UI018',
    'UI023',
    'UI024',
    'UI026',
    'UI030',
    'UI033',
    'UI034',
    'UI040',
}


def test_ui_smoke_regression_case_set_tracks_known_valid_domain_failures() -> None:
    cases = load_smoke_cases(Path('data/evaluation/ui_smoke_test_regression_cases.csv'))
    assert {case.case_id for case in cases} == REGRESSION_IDS
