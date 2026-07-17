# SpiderPi Auto-Commit Setup

This project includes Cursor hooks that automatically commit and push Agent file edits.

## Requirements

1. Open `D:\SpiderPi` as the Cursor workspace root.
2. Connect GitHub in Cursor: **Settings -> General -> Account -> Integrations -> GitHub -> Connect**.
3. Ensure Git can authenticate to GitHub (Git Credential Manager or Personal Access Token).

## How It Works

- Hook event: `afterFileEdit`
- Debounce: 60 seconds after the last Agent edit
- One commit per burst of Agent changes
- Push target: current branch on `origin`

## Files

- `.cursor/hooks.json`
- `.cursor/hooks/auto-commit.ps1`
- `.cursor/hooks/auto-commit-worker.ps1`
- `.cursor/hooks/auto-commit.log` (generated at runtime, ignored by git)

## Branch Note

Your GitHub repo already had README commits on `main`. The full local project was pushed to:

- `origin/full-local-project`

Future auto-commits push to that upstream branch. When ready, merge it into `main` on GitHub with a pull request.

## Manual Push (first time)

If the remote already has README commits and your local repo is new:

```powershell
cd D:\SpiderPi
$env:GIT_SSL_NO_VERIFY = "true"
git fetch origin
git pull origin main --allow-unrelated-histories
git push origin main
```

## Manual Hook Test

```powershell
cd D:\SpiderPi
'{"file_path":"README.md"}' | powershell -NoProfile -ExecutionPolicy Bypass -File .cursor\hooks\auto-commit.ps1
```

Wait about 60 seconds, then check `.cursor/hooks/auto-commit.log`.
