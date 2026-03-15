# Targeted UI Smoke-Test Improvement Summary

## Scope

This note summarizes the targeted improvement pass applied after the 50-case live UI smoke test. The pass focused on three known weak areas: abbreviation-heavy shorthand, development-finance / African political-economy queries, and region-plus-issue prompts such as Iran sanctions, Ethiopia post-war politics, and Horn migration routes.

## Before vs After (50 live cases)

### Before
- 50/50 requests succeeded with HTTP 200
- 31/50 returned one or more recommendations
- 19/50 returned zero recommendations
- 12/50 were routed to manual review
- 38/50 were recognised-outlet cases
- weak-match suppression: 7/7 weak-match cases returned zero recommendations

### After
- 50/50 requests succeeded with HTTP 200
- 35/50 returned one or more recommendations
- 15/50 returned zero recommendations
- 12/50 were routed to manual review
- 38/50 were recognised-outlet cases
- weak-match suppression: 7/7 weak-match cases returned zero recommendations

## Target Regression Set Outcomes

Improved from zero recommendations to one or more recommendations:
- UI003 -> 2 recommendations, top expert Dr Dieter Wang
- UI007 -> 5 recommendations, top expert Dr Mujge Kucukkeles
- UI012 -> 4 recommendations, top expert Dr Yannis Dafermos
- UI023 -> 1 recommendation, top expert Dr Tolga Sinmazdemir
- UI024 -> 2 recommendations, top expert Professor Phil Clark
- UI026 -> 2 recommendations, top expert Dr Jing Zhang
- UI030 -> 1 recommendation, top expert Professor Laura Hammond
- UI040 -> 5 recommendations, top expert Dr Moataz El Fegiery

Still failed with zero recommendations:
- UI018
- UI033
- UI034

## New Regressions Observed

The pass did not improve the system uniformly. The following cases returned recommendations before the targeted pass but fell to zero afterwards:
- UI001 strong_match_middle_east_law
- UI015 strong_match_yemen_humanitarian
- UI032 paraphrase_gaza_b
- UI039 normalization_malformed_punctuation
- UI042 manual_review_freelance_middle_east

## Interpretation

The targeted pass improved valid-domain coverage in the intended weak areas without weakening manual-review routing or weak-match suppression. However, it also introduced visible regressions in some already-strong Middle East / humanitarian-law style cases. The result should therefore be treated as a partial improvement rather than a clean win.
