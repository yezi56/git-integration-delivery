# Conflict And Pre-Commit Review

## Conflict Impact Review

Keep the conflicted operation unchanged while gathering evidence:

```bash
git status --short --branch
git diff --name-only --diff-filter=U
git ls-files -u
git diff --summary
git diff --cc -- <path>
git show :<stage>:<exact-stage-path>
```

Read the actual stage and path pairs from `git ls-files -u`: stage 1 is the merge base, stage 2 is the current side, and stage 3 is the incoming side. A stage may be absent in add/add, delete/modify, rename/delete, and similar conflicts; renamed sides can use different paths. Inspect only entries that exist, using each entry's exact path, and use the status/summary output to map renamed or deleted sides. Adapt the side terminology for cherry-pick, revert, or rebase. Avoid printing secrets or large generated and binary content; inspect metadata and the smallest useful source context instead.

For each conflicted file, trace:

- The role of the file and the behavior each side intends to preserve.
- Changed callers, consumers, API schemas, events, configuration keys, migrations, generated artifacts, and tests.
- User-visible behavior, authorization and tenant boundaries, stored-data compatibility, rollout/startup behavior, and rollback consequences.
- Whether accepting either side would silently discard an independent change.
- Resolution choices, tradeoffs, recommended verification, and any evidence still missing.

Report findings first in severity order. Use exact `file:line` references where the conflict or affected code has stable lines. Then provide one row per conflicted file with: competing intent, affected behavior or contract, downstream impact, viable choices, and validation needed.

Stop after the report. Do not modify the index or working tree, and do not run `--continue`, `--abort`, or `git commit`. After the user resolves the conflict, verify with:

```bash
git status --short
git diff --name-only --diff-filter=U
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Re-trace the resolved behavior through affected callers and contracts before starting the pre-commit review.

## Pre-Commit Risk Review

Review the exact proposed commit, not a convenient subset:

```bash
git status --short --branch
git diff --cached --stat
git diff --cached --check
git diff --cached --no-ext-diff
git diff --stat
git diff --name-only
git ls-files --others --exclude-standard
```

For an integration merge, also compare the staged result to its environment baseline with `git diff --cached origin/<environment> --`. For an ordinary feature or fix, use the repository's confirmed baseline and inspect both the staged delta and the branch delta so the proposed commit is understood in context.

Protect validation integrity:

- Prefer a clean dedicated worktree where `git diff --quiet` confirms there are no unstaged tracked changes. Inspect untracked files and ensure none can affect test discovery, imports, generation, configuration, build output, or runtime behavior.
- If unrelated working-tree state must remain, validate an isolated materialization of the exact index tree using a repository-appropriate temporary checkout, container, or equivalent. Do not stash, delete, or include the user's unrelated changes.
- Record the reviewed index tree with `review_tree=$(git write-tree)`. If this fails because the index contains intent-to-add or missing objects, treat the proposed snapshot as unreviewable; fully stage the intended content under the existing authorization, then restart the review. Before and after validation, require the validation checkout to have no unstaged tracked changes and require `git -C <validation-checkout> write-tree` to equal `$review_tree`; otherwise the validation does not apply to the proposed commit. `git write-tree` records the index as a tree object without creating a commit or moving a ref.
- Recheck the staged diff after validation. If the exact staged snapshot cannot be tested, label that boundary explicitly; classify it as a blocker when the affected behavior could conceal a `Critical` or `High` failure.

Check at least these high-risk surfaces when they are present:

- Authentication, authorization, tenant isolation, credentials, cryptography, and input validation.
- Destructive writes, schema or migration compatibility, irreversible data changes, and rollback feasibility.
- Concurrency, transactions, retries, idempotency, ordering, leases, and duplicate delivery.
- Public API, event, database, cache, configuration, and cross-service contract compatibility.
- Deployment manifests, startup commands, CI/CD, feature flags, defaults, environment-specific behavior, and secret handling.
- Error handling, timeouts, partial failure, fallback behavior, observability, and operational recovery.
- Dependency, generated-code, lockfile, vendored, permission, and unusually broad changes.
- Tests that fail to cover the changed risk, tests removed or weakened, and validation that cannot run locally.

Classify findings as:

- `Critical`: likely security breach, unrecoverable data loss, or production-wide outage.
- `High`: plausible serious regression, incompatible contract, unsafe migration, privilege failure, or deployment blocker.
- `Medium`: correctness or operability risk with limited blast radius or a practical mitigation.
- `Low`: maintainability or defensive-hardening issue with no immediate material failure.

Lead with findings, each containing severity, `file:line`, evidence, impact, and required action. Then report validation performed, untested boundaries, and residual risk. If there are no findings, say so explicitly without implying that unrun tests or unavailable environments were verified.

Treat `Critical` and `High` findings as blockers and wait for a new instruction. With no blocking finding, commit only if the current request explicitly authorizes committing after review; otherwise return the review and wait. Any index change invalidates the completed review and requires a fresh one.
