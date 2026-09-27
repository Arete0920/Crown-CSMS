# CROWN CI Architecture

**Status:** current target architecture  
**Objective:** preserve rigorous verification while reducing duplicated orchestration and ambiguous merge signals.

## Design rule

A specialized check may remain independent when it protects a distinct high-risk invariant, but branch protection should depend on a small stable set of terminal gate families rather than every implementation workflow.

## Gate families

### 1. Core CI
Owns baseline test execution, immutable-tag verification, and general application checks.

### 2. Security
Owns CodeQL/static analysis, secret scanning, dependency review, vulnerability audit, license review, and SBOM generation.

### 3. Data and Tenancy
Owns schema/migration governance, tenant isolation, authorization boundaries, and data-integrity checks.

### 4. Product Proof
Owns frontend/build quality, route verification, UI/browser proof, demo/proof surfaces, and material module certification tests.

### 5. Release Authority
Owns repository policy/freshness, release verification, claims control, release scorecard, and exact-head promotion rules.

## Consolidation rules

- Do not weaken or delete a control merely to reduce workflow count.
- Prefer reusable workflows or terminal aggregator jobs when multiple workflows duplicate setup and execution.
- Use unique stable job/check names.
- Cancel superseded pull-request executions when a newer commit exists.
- Preserve scheduled/manual production or recovery workflows where cancellation would be unsafe.
- Remove one-time workflows after their bounded purpose is complete and evidence is retained.
- Keep deployment workflows separate from pull-request validation.
- Require only stable terminal contexts in branch protection.

## Change method

Workflow consolidation must be incremental:

1. inventory current trigger, permissions, environment, dependencies, and outputs;
2. identify duplicated setup or identical validation;
3. define the terminal owner gate;
4. migrate one bounded family at a time;
5. prove parity before deleting predecessor workflow paths;
6. update branch-protection contexts only after successful exact-head runs establish the replacement names.

CI simplification is successful only when verification remains at least as strong and failures become easier to diagnose.
