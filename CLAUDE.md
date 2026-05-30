# Acme Racing — Odoo MCP project handoff

This file is the durable handoff for **Claude Code sessions running locally** (PowerShell or WSL2) after work started in a Claude Code **web/sandbox** session. Web sessions can't be resumed locally — the git branch, the PR, and this file *are* the handoff.

## TL;DR — what this project is

- Customer: **Acme Racing**, on **Odoo.SH**, **Odoo 19**.
- Two databases:
  - **Production (master):** `https://www.acme-racing.com` — db `acme-racing`
  - **Development branch:** `https://acmeracing-19-0-31791711.dev.odoo.com` — db `acmeracing-19-0-31791711`
  - **No dedicated staging branch today.**
- Goal: let Claude Code **read everything** in those Odoo DBs and **write only what the user confirms**, across both branches.
- GitHub admin on the Odoo.SH repo is an **external supplier** → we deliberately avoid any solution that needs them to merge a custom module for the baseline.

## Decisions already taken

| Item | Decision |
|---|---|
| MCP connector | **`tuanle96/mcp-odoo`** — PyPI package `odoo-mcp`, entry-point `odoo-mcp` (MIT, external process, Odoo 16-19, built-in write-gate). |
| Transport | `xmlrpc` (works on Odoo 19, simplest). `json2` available later if needed. |
| Topology | One MCP server per branch: `odoo-prod`, `odoo-dev`. Add `odoo-staging` later if a staging branch is created. |
| Production write policy | Writes **enabled** but Claude must confirm each write; `mcp-bot` user on Odoo has restricted groups. (Open to switching to "fully read-only on prod" — see Open Questions.) |
| Dev write policy | Writes enabled, confirm each. |
| Auth | Per-branch Odoo technical user **`mcp-bot`** + API key. Never use admin. |
| Audit (later, optional) | `muk_mcp` native addon for MCP-badged chatter — only if the supplier agrees to merge a module. |
| Dev plugins (later, optional) | `ahmed-lakosha/odoo-plugins` (Claude Code plugins for Odoo dev: security, upgrade, tests, reports). |
| Rejected | `bmya/claude-odoo-api` (Odoo 19 Custom plan only), `rosenvladimirov/odoo-claude-mcp` (AGPL, overkill), `ivnvxd/mcp-server-odoo` (more moving parts). |

## Defense in depth (don't weaken without thinking)

1. **Connector layer** — `ODOO_MCP_ENABLE_WRITES` flag + approval token + live `fields_get` validation.
2. **Claude layer** (`.claude/settings.json`) — read tools auto-allowed; all write tools (`create/update/write/delete/unlink/execute/post_message`) set to `ask`.
3. **Odoo layer** — `mcp-bot` is **not** admin. Broad read, write/create/unlink only on agreed models on prod.

## Current local status (Windows, from the user's `claude mcp list` on 2026-05-30)

- Claude Code CLI **2.1.156** working on Windows.
- `odoo-mcp.exe` installed at `C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\Scripts\odoo-mcp.exe`.
- **`odoo-acme-staging` ✓ Connected** — **likely actually points to the dev branch** (the user previously said there is no staging). Needs verification with `claude mcp get odoo-acme-staging` and probable rename to `odoo-dev`.
- **`odoo-prod` ❌ not yet configured.**
- Global skills present: `frontend-design`, `omc-reference`, `skill-creator`. **Missing:** `odoo-19` (unclecatvn), `odoo-development` (mindrally).
- Microsoft 365 + WordPress.com MCPs need authentication (irrelevant to Odoo work).
- WSL2 is installed but not in use; current setup is Windows-native and works.

## Open questions (need user input)

1. **`odoo-acme-staging` rename**: confirm its `ODOO_URL`; if it's the dev branch (`acmeracing-19-0-31791711.dev.odoo.com`), rename to `odoo-dev`.
2. **Prod write scope**: fully read-only on prod, or writes enabled with confirm + restricted `mcp-bot` groups? List the models `mcp-bot` may write/create/unlink.
3. **Config source of truth**: keep only the global CLI config (`claude mcp add`), keep only the project-scoped `.mcp.json` in this repo, or both (risk: duplicates). Recommend project-scoped because it's versioned and shareable.

## Files in this repo

- `.mcp.json` — project-scoped MCP server definitions (`odoo-prod`, `odoo-dev`), env vars via `${ODOO_*}`.
- `.claude/settings.json` — permission rules: read tools `allow`, write tools `ask`.
- `.env.mcp.example` — env var template (URLs/DB filled, API keys blank).
- `.env.mcp` — **gitignored**, holds real API keys; the user creates it from the example.
- `.gitignore` — ignores `.env.mcp`, `.env`, `.claude/settings.local.json`.
- `docs/odoo-mcp-connection-plan.md` — full plan, alternative connectors comparison, manual runbook.

## How to load env vars before launching Claude Code locally

PowerShell (Windows):
```powershell
Get-Content .env.mcp | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process') }
}
claude
```

Bash (WSL2 / Linux / macOS):
```bash
set -a; source .env.mcp; set +a
claude
```

## Next concrete actions (PowerShell, Windows)

```powershell
# 0. verify what odoo-acme-staging actually points to
claude mcp get odoo-acme-staging

# 1. (if it's the dev branch) rename: remove + re-add as odoo-dev
$EXE = "C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\Scripts\odoo-mcp.exe"

claude mcp remove odoo-acme-staging

claude mcp add odoo-dev --transport stdio `
  --env ODOO_URL=https://acmeracing-19-0-31791711.dev.odoo.com `
  --env ODOO_DB=acmeracing-19-0-31791711 `
  --env ODOO_USERNAME=mcp-bot `
  --env ODOO_PASSWORD=<API_KEY_DEV> `
  --env ODOO_TRANSPORT=xmlrpc `
  --env ODOO_MCP_ENABLE_WRITES=1 `
  -- $EXE

# 2. add odoo-prod (leave ODOO_MCP_ENABLE_WRITES OUT for fully read-only at the connector layer)
claude mcp add odoo-prod --transport stdio `
  --env ODOO_URL=https://www.acme-racing.com `
  --env ODOO_DB=acme-racing `
  --env ODOO_USERNAME=mcp-bot `
  --env ODOO_PASSWORD=<API_KEY_PROD> `
  --env ODOO_TRANSPORT=xmlrpc `
  -- $EXE

# 3. install the two Odoo skills globally
npx skills add unclecatvn/agent-skills --skill odoo-19
npx skills add mindrally/skills --skill odoo-development

# 4. verify
claude mcp list
npx skills list -g
```

## Smoke tests (inside Claude Code, after setup)

- **odoo-dev:** `list_models` → ok. `search_records` on `res.partner` → ok. A trivial `create_record` → must show approval prompt before landing.
- **odoo-prod:** `list_models` → ok. Any write tool → must be blocked at the connector (read-only) or prompt for explicit confirm (writes enabled mode).

## Reconcile when working locally

The first thing to do in the local session is reconcile this repo's `.mcp.json` with the global CLI config:

- **If keeping project-scoped `.mcp.json`** (recommended): `claude mcp remove odoo-dev odoo-prod` so the global ones don't duplicate the project ones. Then `cd` here and run `claude` — `.mcp.json` is picked up automatically.
- **If keeping global CLI config**: delete or ignore `.mcp.json` in this repo; the manual `claude mcp add` commands above are the source of truth.

Do not run both at the same time or you'll see two `odoo-prod` / `odoo-dev` entries in `claude mcp list`.

## Reference

- Connector: https://github.com/tuanle96/mcp-odoo (PyPI `odoo-mcp`)
- Plan + alternatives evaluated: `docs/odoo-mcp-connection-plan.md`
- Branch with all work: `claude/evaluate-mcp-odoo-servers-BrxvM`
- Draft PR: https://github.com/Andrearally/Odoo-Acme/pull/1
