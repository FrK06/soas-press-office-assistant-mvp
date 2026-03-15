# UI Smoke Test Findings (50 Live API Cases)

## Scope

This note summarizes a live API smoke-test run of 50 manually designed UI cases against the local `POST /enquiries/process` endpoint using the current improved SOAS Press Office Assistant runtime.

Input cases:
- `data/evaluation/ui_smoke_test_cases.csv`

Live outputs:
- `data/evaluation/ui_smoke_test_results.csv`
- `data/evaluation/ui_smoke_test_results.json`

## Headline Results

- All 50 requests completed successfully with HTTP `200`.
- `31/50` cases returned one or more recommendations.
- `19/50` cases returned zero recommendations.
- `12/50` cases were routed to manual review.
- `38/50` cases were recognized as outlet-linked.

## What Worked Well

- Weak-match suppression was strong. All seven clearly off-domain weak-match cases returned zero recommendations.
- Manual-review routing behaved correctly for the freelance, blog, personal-email, and Substack-style cases.
- Several strong topical domains produced plausible and specific top experts, especially migration, Sudan, gender/care economy, Myanmar, Islamic law, and parts of Middle East public law.
- Paraphrase stability was good for cases that already retrieved well:
  - `UI008/UI009` returned the same top expert.
  - `UI029/UI031` returned the same top expert.
  - `UI032/UI036` returned the same top expert.

## Main Weakness Patterns

### 1. Development finance and African political economy remain the clearest live failure mode

These cases returned zero recommendations despite being on-domain and academically reasonable:

- `UI003` sovereign debt / IMF reform / African development finance
- `UI012` climate finance and African debt
- `UI018` debt restructuring in Zambia and Ghana
- `UI026` African industrial policy and green transition

This suggests the current system is still too brittle for debt, finance, IMF, and industrial-policy phrasing in the Africa/development economics space.

### 2. Some regional conflict-politics cases still miss despite being in scope

The following strong-match cases returned zero recommendations:

- `UI023` Iran sanctions and regional politics
- `UI024` Ethiopia conflict and post-war politics
- `UI030` migration routes through the Horn of Africa

This indicates that region-plus-politics queries can still fail when the request is broad, policy-oriented, or not expressed in the exact terminology used in the indexed evidence.

### 3. Query normalization improved, but abbreviation handling is still weak

Normalization-style cases were mixed:

- `UI037` citation fragment -> 1 recommendation
- `UI038` repeated generic tail -> 2 recommendations
- `UI039` malformed punctuation -> 1 recommendation
- `UI007` noisy stress query -> 0 recommendations
- `UI040` initials fragment (`M.E.` and `IHL`) -> 0 recommendations

This suggests the normalization layer is helping on malformed punctuation and repeated boilerplate, but it still struggles with short abbreviations, compressed initials, and underspecified shorthand.

### 4. Paraphrase robustness is conditional rather than uniform

Paraphrase behavior was strong where the underlying topic already retrieved well, but weak where the base query was already fragile:

- migration pair `UI008/UI009`: stable
- Gaza-related pair `UI029/UI031`: stable on top expert
- gender pair `UI035/UI036`: stable on top expert
- debt pair `UI033/UI034`: both returned zero recommendations

This indicates that the current system is robust to reformulation only when the original retrieval path is already strong.

### 5. Top-expert concentration is still noticeable

Among the 31 cases with at least one recommendation, the most frequent top experts were:

- `Professor Fiona B Adamson` -> 5
- `Professor Shirin Rai` -> 5
- `Dr Frank Maracchione` -> 4
- `Professor Thoko Kaime` -> 4
- `Dr Tolga Sinmazdemir` -> 3
- `Professor Matthew J Nelson` -> 3
- `Professor Michael W. Charney` -> 3

This is not necessarily wrong, but it suggests the ranking layer may still be over-concentrating on a relatively small cluster of strong profiles.

## Highest-Value Improvements Suggested by the 50 Live Cases

1. Improve query-term matching for development finance and industrial-policy language.
   Focus on phrases such as `sovereign debt`, `debt restructuring`, `IMF reform`, `climate finance`, `multilateral lenders`, `industrial policy`, and `green transition`.

2. Expand abbreviation and shorthand normalization.
   Add targeted handling for patterns such as `M.E.` -> `Middle East` and `IHL` -> `international humanitarian law`, while preserving cautious behavior for ambiguous abbreviations.

3. Strengthen retrieval support for Africa/Horn and regional political-economy phrasing.
   The current evidence-first setup appears strong on direct migration and conflict language, but weaker on regional policy framing and cross-country development-economics language.

4. Review whether current thresholds are slightly too strict for high-value in-domain cases.
   The system is excellent at suppressing off-domain noise, but some legitimate in-domain development and regional-politics cases now fall below the recommendation threshold.

5. Continue monitoring expert concentration.
   The system appears to prefer a small number of repeatedly high-scoring experts. This may be partly desirable, but it should be checked against evidence specificity and exposure balance.

## Bottom Line

The live 50-case run shows a system that is now safer and more selective than before, with good behavior on weak-match suppression, manual-review routing, and several high-confidence topic areas. The main remaining quality problem is not general instability; it is uneven coverage. In particular, development-finance and some regional politics queries are still under-served, and abbreviation-heavy noisy inputs remain a meaningful edge case.
