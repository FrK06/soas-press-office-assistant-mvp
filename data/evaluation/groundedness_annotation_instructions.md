# Groundedness Audit Instructions

This audit supports **E4 Groundedness / Evidence Support** for the SOAS Press Office Assistant.

## Purpose

The system should be evaluated as a retrieval-augmented expert recommendation and decision-support system. The goal of this audit is to judge whether each recommended expert is justified by the retrieved supporting evidence shown to the user.

## Unit of annotation

- Annotate one row per recommended expert.
- Each row corresponds to one recommendation rank for one benchmark case.
- Use only the retrieved supporting chunks shown in the sheet for the annotation decision.

## Labels

### Supported
Use `Supported` when the retrieved evidence explicitly and convincingly supports the recommendation for the enquiry.

This means the evidence clearly links the expert to the enquiry topic, issue, region, population, or media-relevant expertise. A staff reviewer could justify the recommendation from the retrieved evidence alone.

### Partially Supported
Use `Partially Supported` when the evidence is relevant but indirect, broad, incomplete, or weakly specific.

This means the recommendation is plausible, but the retrieved evidence does not fully justify it on its own.

### Unsupported
Use `Unsupported` when the retrieved evidence does not substantively justify the recommendation.

This includes recommendations that appear generic, only loosely related, or reliant on assumptions not present in the retrieved material.

## Annotation procedure

1. Read the enquiry subject and body.
2. Read the recommendation rationale.
3. Review the supporting chunks provided for that recommendation.
4. Assign exactly one label in `annotation_label`.
5. Add a short note in `annotation_note` when the recommendation is `Partially Supported` or `Unsupported`.

## Important constraints

- Do not use outside knowledge about the academic or institution.
- Do not use the expected expert labels from the benchmark.
- Judge only the evidence presented in the audit sheet.
- If the recommendation seems sensible but the evidence is weak, prefer `Partially Supported` rather than `Supported`.

## Output expectations

The scorer will compute:

- `Supported@1`
- `Supported@3`
- `Supported-or-Partially-Supported@3`
- `Unsupported_rate`

Strict `Supported` metrics are the primary groundedness results. `Supported + Partially Supported` is a secondary relaxed metric, and `Unsupported_rate` is the key error metric.
