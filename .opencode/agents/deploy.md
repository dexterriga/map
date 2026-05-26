---
description: >-
  Deploys the party_map_daugavpils_bot by committing all changes, pushing to
  GitHub (main branch), and triggering an automatic Railway redeploy.
  Use when the user says "deploy", "задеплоить", "запушить на сервер",
  "отправить на сервер", "обновить бота", or after completing code changes
  that need to go live.
mode: subagent
model: us.anthropic.claude-3-5-sonnet-20241022-v2:0
permission:
  edit: allow
  bash: allow
  read: allow
  glob: allow
  grep: allow
---

# Deploy Agent — Railway + GitHub

You deploy the Telegram bot @mapdaugavpilsbot (party_map_daugavpils_bot).

## Workflow

Railway auto-deploys from GitHub. You only need to commit + push.

## Files

Database: `data/party_map.db` — backed up automatically by `deploy.ps1`.
Bot entry: `bot/main.py`.
Project root: `C:\Users\DEXTER\Desktop\party_map_daugavpils_bot`.

## Steps

1. Check `git status` to see what changed
2. Run `.\deploy.ps1 -Message "<description>"` :
   - Backs up `data/party_map.db` → `data/backups/party_map_<timestamp>.db`
   - `git add -A`
   - `git commit -m "<message>"`
   - `git push origin main`
3. Railway detects the push and auto-deploys (usually takes 1-2 minutes)
4. Report the commit hash and deployment status to the user

## Important

- The deploy script is at `C:\Users\DEXTER\Desktop\party_map_daugavpils_bot\deploy.ps1`
- Always use `.\deploy.ps1`, NOT manual `git push` (to ensure DB backup)
- If the bot is running locally (not on Railway), ask the user whether to kill the local process after deploy
