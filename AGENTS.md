# Working agreement and recovery procedure

This repository implements SPEC.md. The user requires a runnable Python MVP, incremental
commits and durable state. Do not restart implementation after a context reset.

Before continuing after any interruption:
1. Inspect the repository structure.
2. Read PROJECT_STATUS.md, TODO.md, README.md and relevant code.
3. Run git status, git log -5 --oneline and git diff (also staged diff if present).
4. Run the existing test suite; determine actual state from files/tests/history.
5. Continue the first unfinished step. Preserve working architecture unless a concrete
   bug or necessary advantage justifies changing it; record that reason in PROJECT_STATUS.md.

After each major completed stage:
1. Run relevant tests and fix failures.
2. Update PROJECT_STATUS.md: implemented behavior, architecture, changed files, verified
   parts, passing/failing tests, bugs/limitations, current stage, next concrete step,
   remaining work and decisions to preserve.
3. Update TODO.md. Stubs and pseudocode are not completed tasks.
4. Review git diff, including diff --check.
5. Make a clear incremental local commit. Do not squash the whole project into one commit.

Before stopping: save work, test, update both status files and commit.
Before final delivery: run all tests, verify README CLI and UI startup, audit tracked
files for secrets, confirm .env is ignored/untracked, commit and push to existing origin:
https://github.com/salimadze2005-beep/find_ai_news.git
Never put credentials in code, command arguments or history. Use existing environment auth.

Core invariants: public web only, strict date window for confirmed events, historical
context separate, primary + independent evidence, claims/facts/inferences separate,
configurable scoring, explicit synthetic mock mode, bounded paid calls and persisted usage.
