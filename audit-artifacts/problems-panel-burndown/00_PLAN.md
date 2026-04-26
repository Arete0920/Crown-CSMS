# Problems Panel Burndown Plan

## Scope

This branch is separate from the validated release authority state.

## Do Not Mix

- no Gate 4 changes
- no release packet changes
- no PR #756/#757/#760 work
- no dashboard redesign unless directly tied to a diagnostic
- no broad cleanup without classification

## Classification Order

1. YAML workflow parse/blockers
2. Python runtime/test blockers
3. frontend test/lint blockers
4. CSS warnings
5. markdownlint documentation noise
6. duplicate workspace/path noise

## First Pass Rule

Classify before fixing.

No file should be edited until its diagnostic category and owner are clear.
