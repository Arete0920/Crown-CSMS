# Medium Security Strike Prep

- Repo: tcmegahan/Crown2026
- Worktree: C:\Users\JMega\OneDrive\Desktop\Crown2026_main_medium
- Branch: warroom/medium-strike-20260316_011931
- Base SHA: 06ac7fcda98f01748f9e4841cacf0143b03e4a42
- Evidence root: C:\Users\JMega\OneDrive\Desktop\Crown2026_main_medium\MEDIUM_STRIKE_20260316_011931

## Alert counts on main at prep time
- Total: 5
- High: 0
- Medium: 5
- Low: 0

## Files generated
- medium_alerts_main.json
- medium_alerts_main.csv
- snippets\\*.txt

## What to edit now
1. Open each file listed in medium_alerts_main.csv.
2. Remove outward-facing raw exception text.
3. Keep detail in logs only.
4. Do not echo provider payloads or sensitive fields.
5. Save edits in the worktree only.

## Next command
powershell -ExecutionPolicy Bypass -File "C:\Users\JMega\OneDrive\Desktop\Crown2026\scripts\ops\warroom-medium-strike.ps1" -Stage finalize
