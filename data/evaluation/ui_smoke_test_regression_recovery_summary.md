# Regression Recovery Smoke-Test Summary

## Scope

This note records the narrow regression-recovery pass applied after the targeted smoke-test improvement pass. The purpose was to recover five newly regressed live cases without losing the majority of the previously rescued valid-domain cases.

## Recovery Target Cases

Regressed before this pass:
- UI001
- UI015
- UI032
- UI039
- UI042

Previously rescued cases to preserve:
- UI003
- UI007
- UI012
- UI023
- UI024
- UI026
- UI030
- UI040

## Main Cause

The regressions were not primarily retrieval failures. In all five cases, relevant experts were still being retrieved from strong research-interest evidence. The main issue was that the new targeted pass had improved single-chunk rescue logic but still required the full final score to clear the default threshold. For these legal-humanitarian and region-plus-issue prompts, overlap evidence was real but not quite strong enough to cross the final score gate.

## Fix Applied

A narrow high-signal final-score override was added in the ranker. It applies only when:
- the top evidence is non-publication profile evidence
- the case already satisfies the evidence-backed single-chunk override conditions
- the query contains at least two canonical in-domain high-signal phrases
- the matched query/evidence token overlap across those high-signal phrases is at least two tokens
- the final score reaches a narrower floor of 0.52

This was intentionally designed to recover valid-domain legal-humanitarian and region-plus-issue prompts without broadly lowering global thresholds.

## Smoke-Test Outcome

### Before recovery pass
- 35/50 cases returned one or more recommendations
- 15/50 cases returned zero recommendations
- weak-match suppression remained 7/7
- manual-review routing remained stable at 12 cases

### After recovery pass
- 40/50 cases returned one or more recommendations
- 10/50 cases returned zero recommendations
- weak-match suppression remained 7/7
- manual-review routing remained stable at 12 cases

### Recovery target cases
Recovered:
- UI001
- UI015
- UI032
- UI039
- UI042

### Preserved rescued cases
Still improved:
- UI003
- UI007
- UI012
- UI023
- UI024
- UI026
- UI030
- UI040

## Bottom Line

The regression-recovery pass met its acceptance goal. All 5/5 regressed cases were recovered, all 8/8 rescued cases remained improved, and both weak-match suppression and manual-review routing stayed stable. On that basis, the targeted pass should be kept rather than reverted.
