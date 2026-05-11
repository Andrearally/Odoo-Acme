# Odoo MCP Connection Plan — master / staging / development

Goal: let an AI client (Claude Code) **read everything** in our Odoo.SH databases and
**write only what we explicitly confirm**, across the production (`master`), `staging`,
and `development` branches — without forcing our external GitHub admin (the supplier)
to merge anything into the Odoo.SH repo.

## Decision

| Item | Choice |
|---|---|
| Connector | **[tuanle96/mcp-odoo](https://github.com/tuanle96/mcp-odoo)** — external MCP process, MIT, Odoo 16-19, zero Odoo-side module, built-in write-gate |
| Topology | One MCP server entry per Odoo.SH branch (`odoo-prod`, `odoo-staging`, `odoo-dev`) — each branch is a separate DB/URL |
| Production write policy | Writes **enabled** but every write requires explicit confirmation in Claude; the Odoo `mcp-bot` user is restricted to an agreed model list |
| Staging/dev write policy | Writes enabled; Claude still confirms each write |
| Audit/native option | `muk_mcp` (native LGPL-3 addon, MCP-badged chatter) kept as a possible later phase if the supplier will merge & maintain a module |
| Dev tooling (separate) | `ahmed-lakosha/odoo-plugins` — Claude Code plugins for Odoo dev work (security audit, upgrade, tests, reports); not part of the runtime connection |

### Connectors evaluated

- **tuanle96/mcp-odoo** — chosen. External, no repo change, 24 tools (10 read/discover, 5 gated-write, diagnostics, migration helpers), stdio + streamable-HTTP, write-gate via `ODOO_MCP_ENABLE_WRITES` + approval token + `fields_get` validation + explicit confirm.
- **muk_mcp** (MuK IT) — native Odoo addon, best audit trail (MCP chatter badge), but needs the supplier to merge/maintain a module and exposes a public `/mcp` endpoint. Reserved as a later phase.
- **ivnvxd/mcp-server-odoo** — addon + a local process per workstation; more moving parts.
- **bmya/claude-odoo-api** — external, but Odoo 19 + Custom plan only; 8 plain CRUD tools, no built-in write-gate.
- **rosenvladimirov/odoo-claude-mcp** — 197+ tools, AGPL-3.0 + commercial tier, Bulgaria-localization focus; overkill.
- **ahmed-lakosha/odoo-plugins** — not an MCP server; Claude Code dev plugins. Complementary only.

## Architecture

```
Claude Code (developer machine)
  ├─ mcp server "odoo-prod"     → https://acme.odoo.com                    writes: confirm-each
  ├─ mcp server "odoo-staging"  → https://acme-staging-XXXX.dev.odoo.com   writes: confirm-each
  └─ mcp server "odoo-dev"      → https://acme-dev-XXXX.dev.odoo.com       writes: confirm-each

Each connects with a dedicated Odoo technical user "mcp-bot" + per-branch API key.
```

### Defense in depth

1. **Connector layer** — `ODOO_MCP_ENABLE_WRITES=1` on every env (per the decision above); the connector still requires an approval token + live field validation + explicit confirm before any write.
2. **Claude layer** (`.claude/settings.json`) — read/discovery tools auto-allowed; all `create/update/write/delete/unlink/execute/post_message` tools set to `ask` on every server.
3. **Odoo layer** — `mcp-bot` is **not** an admin. On production its security groups grant broad read but write/create/unlink only on the agreed model list; on staging/dev it can be broader.

## Repo artifacts (committed here)

- `.mcp.json` — three MCP server entries, secrets pulled from env vars (`${ODOO_*}`), nothing sensitive committed.
- `.claude/settings.json` — permission rules (allow reads, ask on writes). Tool names are best-effort; refine the lists once `uvx odoo-mcp --health` and a `list_tools` call confirm the exact 24 tool names.
- `.env.mcp.example` — template of every env var to fill. Copy to `.env.mcp` (gitignored).
- `.gitignore` — ignores `.env.mcp`, `.env`, `.claude/settings.local.json`.

## Manual actions runbook

### A. Gather facts
- [ ] Production URL + DB name
- [ ] Staging branch URL(s) + DB name(s)
- [ ] Development branch URL(s) + DB name(s)
- [ ] Confirm Odoo version (→ `xmlrpc` for 16-19, `json2` available on 19) and Odoo.SH plan tier
- [ ] Agree the **write-allowed model list** on production

### B. Create the `mcp-bot` user — on each branch (Odoo admin)
- [ ] Settings → Users & Companies → Users → create `mcp-bot`
- [ ] Groups: production = read-broad + write/create/unlink only on the agreed models; staging/dev = broader as needed
- [ ] Developer mode → that user → API Keys → **Generate API Key** → record it
- [ ] (Optional) record rule pinning `mcp-bot` to specific companies

### C. Local machine (developer)
- [ ] Install the connector: `uvx odoo-mcp --health` (or `pipx install odoo-mcp`)
- [ ] `cp .env.mcp.example .env.mcp` and fill URLs / DB names / API keys
- [ ] Load it before starting Claude Code: `set -a; source .env.mcp; set +a`
- [ ] Restart Claude Code; read smoke test: `list_models`, `search_records` on `res.partner` against `odoo-dev`
- [ ] Write smoke test on `odoo-dev` only — confirm the approval prompt fires before the write lands
- [ ] Repeat read smoke tests against `odoo-staging` and `odoo-prod`

### D. (Optional) Claude Code dev plugins
- [ ] Add `ahmed-lakosha/odoo-plugins` via the Claude Code plugin marketplace (confirm exact command from that repo's README); use `odoo-security`, `odoo-upgrade`, `odoo-test`, etc. on the dev branch.

### E. (Optional, later) Native `muk_mcp` phase — needs the external GitHub admin
- [ ] Pick a `development` branch to pilot on
- [ ] Supplier adds `muk_mcp` (pinned to a release tag, not `main`) to the Odoo.SH repo for that branch
- [ ] Supplier confirms rate-limiting / WAF on the public `/mcp` endpoint
- [ ] Install the module; generate per-user MCP keys from user preferences
- [ ] Point/duplicate the relevant MCP server entry at the `/mcp` endpoint; re-test
- [ ] Promote dev → staging → production once validated

### F. Governance
- [ ] Record who holds `mcp-bot` keys + a rotation schedule
- [ ] Treat any change to the production write-allowed model list as a deliberate, logged change
- [ ] If `muk_mcp` is adopted, monitor the "MCP" chatter badge for AI-driven writes

## Notes / caveats

- The `.claude/settings.json` tool names are a starting set; once the connector is installed, run a tool listing and reconcile the `allow`/`ask` arrays with the real 24 tool names.
- `.mcp.json` env-var interpolation requires the `ODOO_*` variables to be present in the shell that launches Claude Code.
- This plan deliberately keeps the Odoo.SH repo untouched so the external supplier has nothing to review/merge for the baseline setup.
