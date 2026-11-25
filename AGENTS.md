# Repository notes

Docs-only hackathon workspace: no app code, manifest, or build/test/lint commands exist yet. Check `docs/STATUS.md` before changing anything; do not invent commands or frameworks.

## Paths and sources of truth

- `docs/STATUS.md` is the live progress file (team-maintained). Its dates are relative ("tonight", "tomorrow"; last commit 2026-11-24 evening) — verify with git history or the team before acting on timing.
- `docs /CONTEXT.md` — the directory name has a **literal trailing space**. Quote the path in shell commands (`cat "docs /CONTEXT.md"`); unquoted paths and globs will miss it. It is the static event reference (tracks, schedule, rules, judging).
- `docs/ARCHITECTURE.md` is referenced by CONTEXT but does not exist yet (planned after track selection). Check before relying on it.
- `.gitignore` is a stock Python template; it ignores `.env` and `.streamlit/secrets.toml` but nothing for JS/TS (e.g. `node_modules`). Add entries for any new stack before committing.

## Working agreements

- Commit after each working step and update `docs/STATUS.md` in the same commit.
- Never commit API keys. Keys live in `.env`; a committed `.env.example` should contain variable names only. Never paste keys into AI chats.
- Detectif credits are limited (5,000 shared). Save sample API responses as JSON and build UI against fixtures; use real API calls only for verification and the final demo.
- Prefer a simple demo that works live over an ambitious one that may crash. Each member must be able to explain everything submitted.

## Hackathon constraints that affect implementation

- Every project must use Aletheia (`POST /v1/deepfake/detect`) and/or Eidos (`/v1/speakers/enroll`, `/v1/speakers/verify`) via REST or MCP. Noesis is not part of the hackathon; do not rely on it.
- A model score is evidence, not proof: show it with a next step for the user. Only record/clone voices with the owner's permission.
- Reddit post is mandatory and must be live before Day 1 evaluation (16:00), with its link in the Google form; no post means no shortlist. Deliverables: accessible repo, short README, 2-minute demo video, presentation/prototype before each round.
- Exact endpoints, parameters, response fields, and credit costs are marked UNKNOWN in CONTEXT — verify against `https://platform.detectif.ai/docs` (or saved response fixtures) instead of guessing.
