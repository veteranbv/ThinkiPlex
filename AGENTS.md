# Agent guide

ThinkiPlex downloads Thinkific courses, organizes them for Plex and can
transcribe and summarize them. See README.md and DEVELOPMENT.md.

Never commit `config/thinkiplex.yaml`, cookies, client dates, API keys or
downloaded course media.

CI runs lint only. The unit tests fail on `main` today (the config fixture
writes a str to a binary temp file, and the parallel tests submit local
functions that cannot be pickled); fix them before adding pytest to CI. Ruff
ignores nine rules as a baseline in `pyproject.toml`; remove each one once
its findings are fixed.

Run before pushing:

```bash
ruff check .
```

## Pull requests and review

Finish and test a coherent change locally, then run a local code and security
review before asking for remote review. The owner requests Codex review for
the exact pushed head (`@codex review <full head SHA>`), one request at a
time. Address every finding on the same pull request and resolve its thread;
after three rounds that still find substantive issues, stop and reconsider the
change. Merge only a qualified head.

Required checks are `quality` and `review-gate`. `review-gate` comes from
`.github/workflows/review-gate-trusted.yml` (`pull_request_target`): it runs
the default branch's copy with a read-only token and never runs pull request
code, so a pull request cannot rewrite it. Protection pins the check to the
GitHub Actions app, not that workflow, so a pull request could still add a
same-named job; merge only through the owner's qualification tooling, which
counts the trusted run alone. No AI attribution in commits, titles or
descriptions, and commits come from a person's identity, not an app or bot
account (Dependabot excepted); `review-gate` rejects both.

The files in `.github/scripts/` are vendored. Do not edit them here; change
them at their source and re-vendor. CI tools are
pinned with hashes in `.github/ci-requirements.txt`; edit
`.github/ci-requirements.in` and recompile with the command in its header.

### Review guidelines

Reviewers (Codex, Claude Code, humans) apply these to every pull request.

- Failure here means: cookies, client dates or API keys logged, committed or
  sent anywhere but their own service; downloads or organization that delete
  or overwrite existing media; shell or PHP command injection from course
  names or config values; CI that runs pull request code with secrets or
  write tokens. Prioritize these.
- Report only issues the change introduces or makes worse; mark pre-existing
  problems as pre-existing.
- Every finding needs file:line evidence and a concrete failure scenario.
- At most three nitpicks per review; skip what ruff enforces.
- Skip vendored files in `.github/scripts/`. Always check tests and fixtures
  for real cookies, keys or private content.
- Start the summary with the number of findings; say plainly when nothing
  needs fixing.
