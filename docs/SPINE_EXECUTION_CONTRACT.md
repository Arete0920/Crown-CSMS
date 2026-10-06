# CROWN Execution Contract

This contract defines repository execution rules for contributors, development tools, automation, and support processes. Its purpose is to prevent scope expansion, hidden regressions, and unverified completion claims.

## 1. Non-negotiables

- One pull request has one purpose.
- The allowed change surface must be declared before edits.
- Unrelated improvements do not belong in the active lane.
- Proof is retained command output, test output, committed evidence, or current GitHub status.
- Unexpected changes require stopping and returning to the declared scope.

## 2. Change-surface rule

Every pull request must identify:

- exact allowed files or directories;
- explicit exclusions;
- validation commands;
- rollback approach.

Any tool or editor change outside the allowed surface must be reverted or separately reviewed before work continues.

## 3. Deterministic execution pattern

Use this sequence:

1. capture branch, HEAD, and working-tree status;
2. inspect the intended diff;
3. run the smallest relevant local validation;
4. commit only the approved change;
5. push the isolated branch;
6. open or update the pull request;
7. allow required checks to complete;
8. merge only when repository policy is satisfied.

## 4. Required proof

Minimum local proof normally includes:

- `git status -sb`;
- `git diff --stat`;
- relevant backend, frontend, documentation, or contract validation.

Required CI proof depends on the changed paths and repository rules. Pending, failed, cancelled, stale, or action-required checks do not constitute PASS.

## 5. Deployment determinism

For deployment-related changes:

- the application must expose the deployed build identity;
- automation must bind deployment to an immutable commit identity;
- the workflow must verify the expected identity against the running service;
- identity mismatch must fail closed.

## 6. Work-instruction rule

Instructions given to a contributor, development tool, or automated process must specify:

- exact file paths;
- the bounded objective;
- prohibited changes;
- commands to run;
- expected evidence;
- a clear stop condition.

## 7. Definition of done

A task is done only when:

- the final diff matches the declared scope;
- relevant local proof is clean;
- required CI is green at the unchanged head;
- review requirements are satisfied;
- deployment identity is verified where applicable.

Development tooling may support work and findings. Tool output does not constitute independent approval or release authority.
