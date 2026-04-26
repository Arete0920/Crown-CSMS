# YAML Stale-Clone Verification

## Purpose

Verify whether YAML workflow diagnostics are active in the current main workspace or stale Problems Panel noise from old clones/worktrees.

## Rule

No workflow files are edited in this step.

## Workspace

- Date/time: 2026-04-25 09:56:46 -04:00
- Repo root: C:/w/crown_main_postmerge_verify
- Branch: hygiene/05-yaml-stale-clone-verify
- HEAD: 7a6246d888338362adb51aadd249cd43b5865b93

## Active Workflow Files

```text
54 workflow files discovered under .github/workflows/*.yml
```

## Basic YAML Parse Check

Result: FAIL - parse issue reproduced in active workspace:

- C:\w\crown_main_postmerge_verify\.github\workflows\prod-health-watch.yml
	- yaml.scanner.ScannerError: while scanning a simple key
	- in ".github/workflows/prod-health-watch.yml", line 46, column 1
	- could not find expected ':'
	- in ".github/workflows/prod-health-watch.yml", line 47, column 1

All other active workflow files parsed successfully.

## Known Stale Clone Noise

Earlier Problems Panel snapshots included diagnostics from old paths such as:

- C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr_clean
- C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr
- C:\w\crown_pr756_replacement
- C:\w\pr756_repair

These are not the active main verification workspace.

## Conclusion

YAML diagnostics are not purely stale-clone noise because one parse issue reproduces on current main in the active verification workspace.

Actionability rule remains: only diagnostics reproduced in C:\w\crown_main_postmerge_verify on current main are actionable.
