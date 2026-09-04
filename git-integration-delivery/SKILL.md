---
name: git-integration-delivery
description: Safely deliver FarmLynk backend changes through integration branches, controlled release branches, production tags, deployment verification, and main, with conflict-impact review, pre-commit risk review, and total/test/non-test diff line reporting. Use for FarmLynk branch handoffs, commits, conflict analysis, release preparation, production tags, recovery, or merge-request work; for other repositories, inspect and follow their own local policy.
---

# FarmLynk Git Delivery And Release

## Purpose And Scope

Apply this workflow to the FarmLynk backend repository `back-end-group/farmlynk`. Its code paths are independent:

```text
feat/<requirement-id> -> integration/dev  -> dev
feat/<requirement-id> -> integration/test -> test
approved source branch -> rX.Y.Z -> tag vX.Y.Z-N -> deployment-repository MR -> production
rX.Y.Z -> main
```

`dev` and `test` are long-lived environment branches, not production-release candidates or substitutes for `main`. Production is selected from an `rX.Y.Z` branch; never promote all of `dev` or `test` by merging it to `release` or `main`.

For a non-FarmLynk repository, do not assume its release branches, CI behavior, migration framework, or deployment repository match this skill. Read its local policy first. The generic environment-integration safeguards below still apply only when they agree with that policy.

## Authorization Boundaries

- Separate local inspection, commits, remote source-branch pushes, integration pushes, MR creation or update, MR merge, release creation, tag push, deployment-repository MR merge, and production deployment. Require explicit authorization in the current request for every remote mutation and for commits or staging of files.
- Never create a local or remote branch unless the user explicitly authorizes that exact branch in the current request. If a required branch is absent, occupied, stale, diverged, or otherwise unsuitable, stop and ask the user; do not invent a feature, fix, delivery, or temporary branch name. Use a detached dedicated worktree when branch creation is unnecessary.
- A request to "deliver" does not authorize a push, MR, tag, MR merge, or deployment. A production-tag push is a distinct high-impact authorization because it requests production deployment.
- Only an authorized owner merges an MR to `dev`, `test`, `main`, or a protected release branch. Only QA or the release owner merges the deployment-repository MR and confirms production acceptance.
- Preserve unrelated tracked and untracked files. Never stage, commit, push, or add local verification files, `.env` files, credentials, environment addresses, test data, or temporary scripts.
- Treat conflict review and pre-commit review as mandatory gates. A prior request to deliver or commit does not authorize resolving conflicts or crossing a `Critical` or `High` finding.

## Branch Rules

- New ordinary requirement work starts from current `origin/main` as `feat/<requirement-id>`, for example `feat/7048051759` or `feat/vv1002`. Use the exact approved requirement ID and do not append an English title or description. Starting from `dev` or `test` is allowed only for a documented dependency on unpublished environment code.
- Use `fix/<requirement-id>` only when the project owner explicitly classifies the work as a fix, `hotfix/rX.Y.Z-<requirement-id>` for an urgent production fix, and `rX.Y.Z` for a release candidate. Do not create new bare numeric, date, personal-prefix, ambiguous `test*`, descriptive-suffix, or per-requirement integration branches.
- `integration/dev` and `integration/test` are the only long-lived integration branches. Do not create replacements if they are absent; report that the project owner must establish them from the current target baseline.
- Ordinary work must not merge directly from `feat/<requirement-id>` or `fix/<requirement-id>` to `dev`, `test`, or `main`. Do not merge `integration/dev` into `integration/test`, or vice versa.
- Direct source branch to `rX.Y.Z` is a controlled exception: it requires explicit release-owner approval and an MR explaining the validated environments, intended release, migration impact, and rollback plan.
- A private, unshared branch may be rewritten only after confirming no one depends on it. Once pushed, present in an MR, or merged into any integration, environment, release, or main branch, do not reset, rebase-and-force-push, or otherwise rewrite its shared history. Repair with a new fix commit or `git revert`.

## Remote Source Branch Is The Only Feature Delivery Input

- Put every feature or fix commit on the explicitly authorized existing remote source branch before integration. Fetch it, record `source_sha=$(git rev-parse origin/<source-branch>)`, and merge exactly `origin/<source-branch>` into `integration/<environment>`.
- Never commit feature or fix implementation directly on an integration branch. Never use a detached HEAD, raw commit SHA, local-only branch head, synthetic tree commit, patch application, or cherry-pick as a substitute for the remote source-branch merge. Baseline synchronization with the corresponding environment branch remains the only exception described below.
- A detached worktree may prepare a commit only to preserve a dirty checkout. Push that commit to the authorized existing source branch first, fetch the branch back, confirm its remote SHA, and only then begin integration delivery.
- After creating the `--no-ff` integration merge commit, verify that its incoming parent equals the recorded remote source SHA: `test "$(git rev-parse HEAD^2)" = "$source_sha"`. Treat any mismatch as a delivery blocker and do not push the integration branch.
- If the remote source branch and integration branch have diverged so that the required branch merge would reintroduce, discard, or conflict with already delivered behavior, stop and report the branch graph and affected diff. Do not bypass the source branch by placing an isolated corrective commit on integration.

## Batch Source Work Before Integration

- A source branch may accumulate multiple coherent commits and authorized pushes before it is delivered to an integration branch. Pushing the source branch does not by itself require an `integration/dev` or `integration/test` merge.
- Default to delivering a complete, independently testable batch: finish the related edits, run the focused validation for that batch, push and confirm the accumulated remote source HEAD, then merge it into each required integration branch once. Do not make integration branches mirror every intermediate source-branch push.
- Deliver an intermediate batch only when the user explicitly requests environment validation, another team is blocked on that batch, or an urgent scoped fix requires it. State why the earlier integration handoff is needed and which source SHA it contains.
- Each integration merge remains an explicit authorized operation. A later batch is a new source HEAD and follows the same inspection, validation, and authorization gates; do not rewrite an earlier shared integration delivery.

## Inspect Before Changing Git State

1. Identify the checkout, branch, remotes, linked worktrees, and all local changes. Do not switch a dirty shared worktree just to inspect another branch.

   ```bash
   git rev-parse --show-toplevel
   git status --short --branch
   git branch --show-current
   git remote -v
   git worktree list
   ```

2. Confirm the requested source, target, and operation. Record the task-start SHA as the final diff-report baseline, source SHA, target SHA, existing open MRs for that source-target pair, and the project-specific focused validation command. Inspect repository documentation and manifests rather than guessing a test command.
3. Fetch only the relevant remote refs, then confirm the required integration, environment, release, or main refs exist. Recheck current status and intended diff immediately before every staging, commit, push, tag, or MR action.

   ```bash
   git fetch origin main dev test integration/dev integration/test
   git show-ref --verify refs/remotes/origin/integration/dev
   git show-ref --verify refs/remotes/origin/integration/test
   git diff --check
   ```

4. Before an ordinary source-branch commit, verify the branch's baseline. For a normal branch this is `origin/main`; if it intentionally uses an environment baseline, make the dependency explicit in the MR. Follow **Review Before Every Commit** before creating the commit.
5. For every MR, state business behavior, API/configuration/database-migration effects, validation commands and results, rollback considerations when relevant, and untested boundaries. Build Markdown descriptions with real newlines, then read the stored description back before reporting the MR.

   ```bash
   mr_description=$'## Changes\n- Describe the behavior\n\n## Validation\n- `python manage.py test <scope>`\n\n## Untested\n- State the remaining boundary'
   glab mr create --source-branch <source> --target-branch <target> --description "$mr_description"
   glab mr view <iid> --output json --jq .description
   ```

## Analyze Conflicts And Wait

Before starting a conflict-prone delivery or release operation, use a dedicated worktree for its target branch; do not use the user's active dirty or source worktree. When any merge, cherry-pick, revert, or rebase reports conflicts, keep the operation and conflict files in that worktree, then follow [Conflict And Pre-Commit Review](references/conflict-and-pre-commit-review.md#conflict-impact-review).

- Preserve the conflict state without editing, staging, continuing, committing, aborting, or restarting the operation.
- Use the reference to inspect the actual conflict stages and affected behavior, report the impact and resolution tradeoffs, then stop and wait for the user to handle the resolution or give a new instruction.
- After the user reports the resolution complete, verify that no unmerged entries remain, inspect the complete resolved result and its downstream effects, run the applicable validation, then follow **Review Before Every Commit**. Do not assume that removing conflict markers produced a correct merge.

## Review Before Every Commit

Before every ordinary, merge, release-fix, revert, or conflict-resolution commit, follow [Conflict And Pre-Commit Review](references/conflict-and-pre-commit-review.md#pre-commit-risk-review).

1. Use the reference to review the exact staged tree against the correct baseline, isolate validation from unstaged and untracked state, and report findings by severity with untested boundaries and residual risks.
2. Treat every `Critical` or `High` finding, including a validation gap that could conceal one, as a blocker. Return the review without changing the proposed commit and wait for a new instruction.
3. With no blocker, commit only when the current request explicitly authorizes committing after review; otherwise return the review and wait. Re-run the review if the index changes after it was reviewed.

## Deliver To An Environment

Start this procedure only for a requested, independently testable source-branch batch. Confirm the source SHA represents all changes intended for the current environment handoff; ordinary intermediate source-branch pushes stay on `feat/<requirement-id>` or the explicitly approved fix branch until the batch is ready.

Run this procedure independently for `integration/dev` with baseline `origin/dev` and target `dev`, then for `integration/test` with baseline `origin/test` and target `test`. Always merge the source branch into the corresponding integration branch, never one integration branch into the other.

1. Use a dedicated worktree containing the integration branch. If none exists, create a separate worktree only after confirming that the path is safe and available; leave the source worktree unchanged.
2. Synchronize the local integration branch with its remote by fast-forward only. Stop and report local-only commits instead of overwriting them.

   ```bash
   git switch integration/<environment>
   git merge --ff-only origin/integration/<environment>
   ```

3. Bring the integration branch up to its own environment baseline before adding the source branch:

   - If `origin/<environment>` is already an ancestor of the integration branch, continue.
   - If the integration branch is an ancestor of `origin/<environment>`, fast-forward it.
   - If both contain unique commits, start a non-committing merge of `origin/<environment>` locally into the integration branch. If it conflicts, follow **Analyze Conflicts And Wait**. If it merges cleanly, run the applicable migration checks and validation, follow **Review Before Every Commit**, and complete this baseline merge commit only after authorization.

   ```bash
   git merge-base --is-ancestor origin/<environment> integration/<environment>
   git merge-base --is-ancestor integration/<environment> origin/<environment>
   # Run only when the integration branch can fast-forward.
   git merge --ff-only origin/<environment>
   # Run instead only when both sides contain unique commits.
   git merge --no-ff --no-commit origin/<environment>
   ```

   Verify the baseline merge commit and a clean index before continuing. Never start the source merge while this baseline merge is still pending.

4. Fetch the authorized source branch, record its remote SHA, then start the merge from that exact remote-tracking ref without creating its merge commit. If it conflicts, follow **Analyze Conflicts And Wait**. If it merges cleanly, leave the result staged and follow **Review Before Every Commit**.

   ```bash
   git fetch origin <source-branch>
   source_sha=$(git rev-parse origin/<source-branch>)
   git merge --no-ff --no-commit origin/<source-branch>
   git status --short
   git diff --cached --check
   git diff --cached --stat origin/<environment>
   ```

5. If migrations are present, follow **Migration Gates** against the staged merge result. Run the agreed focused validation and state exactly what was and was not tested.
6. Follow **Review Before Every Commit**. After a non-blocking review and explicit commit authorization, create the merge commit and verify its SHA and final diff.
7. Before requesting the explicit push/MR authorization, report the integration branch and SHA, target environment, source SHA, commits and complete diff relative to the baseline, pre-commit review, validation and migration results, conflicts, and any existing source-target MR.
8. After that authorization, push only the intended integration branch without force options. Create or update exactly one MR from `integration/<environment>` to `<environment>`, then read it back to verify source, target, title, description formatting, and open state.

   ```bash
   git push origin integration/<environment>
   glab mr create --source-branch integration/<environment> --target-branch <environment>
   glab mr view <iid>
   ```

## Migration Gates

Treat database migrations as a release contract, not ordinary text conflicts.

- Never rename, renumber, delete, change dependencies of, or edit a migration that is already in a shared branch or deployed environment.
- When two branches add migrations from the same ancestor, create a new empty merge migration that depends on both leaf migrations. Do not invent different fixes for different environments.
- If a migration collision appears during a conflicted Git operation, include this remedy and its deployment impact in the conflict assessment, then wait for the user to handle the resolution.
- The same end-of-graph merge migration must exist in the corresponding `dev`, `test`, and release code sets. When environment branches drift, compare `origin/dev`, `origin/test`, and the target release's commit and migration graphs before resolving.
- Run both checks on the final merged code before it is pushed or proposed for merge:

  ```bash
  python manage.py migrate --plan
  python manage.py makemigrations --check --dry-run
  ```

The deployment startup runs `python manage.py migrate --noinput` before Gunicorn. A failing migration plan can therefore prevent a new Pod from starting; successful code tests alone do not clear this gate.

## Report Diff Line Counts

At every completed implementation, commit, push, integration handoff, or release preparation, report all three text-diff measurements:

- Total diff: file count, additions, deletions, and additions plus deletions.
- Test diff: the same measurements for test files only.
- Non-test diff: the same measurements after excluding test files.

Use [scripts/diff_line_counts.py](scripts/diff_line_counts.py) so the three groups use one classification and add up exactly. Before a commit, run it with `--cached`. After completion, compare the task-start SHA or explicitly agreed delivery baseline to the final SHA:

```bash
python <skill-dir>/scripts/diff_line_counts.py --cached --show-paths
python <skill-dir>/scripts/diff_line_counts.py --from <baseline-sha> --to <final-sha> --show-paths
```

- Inspect the reported test and non-test paths. Use `--test-regex` or `--non-test-regex` when repository conventions require an override; do not silently guess an ambiguous classification.
- Define changed text lines as additions plus deletions from `git diff --numstat`. Report additions and deletions separately as well. Report binary files separately because Git does not provide text-line counts for them.
- Name the exact baseline and final SHA or staged scope. If no test files changed, report a zero test diff rather than omitting it.
- Recompute after any index, commit, merge, or baseline change. Never reuse counts from an earlier diff surface.

## Prepare And Maintain A Release

Only the release owner creates or changes an `rX.Y.Z` branch. Confirm the exact release version and explicit authorization before making the branch.

```bash
git fetch origin main
git switch -c rX.Y.Z origin/main
git push -u origin rX.Y.Z
```

- A release contains only approved requirement branches and release fixes. Do not merge all of `dev` or `test` into it.
- Select a source branch only after its relevant `dev` and `test` validation is known. Its controlled source-to-`rX.Y.Z` MR must identify validated environment branch SHAs, the release target, migration impact, and rollback method.
- Once the release is frozen, admit only clearly scoped `fix/...` or `hotfix/...` changes. Re-run focused validation and migration gates against the current release code after every such change.
- Do not assume an old release cannot return to `main`: a subsequent `rX.Y.Z -> main` MR is valid when it contains only commits added since the last release-to-main merge.

## Tag And Verify Production Release

Tag only the latest confirmed commit of the intended release branch. First confirm the exact tag version and increment: a new release starts at `vX.Y.Z-0`; re-releases of the same release use `-1`, `-2`, and so on. Never tag a requirement-branch commit.

```bash
git fetch origin rX.Y.Z --tags
git tag -a vX.Y.Z-N origin/rX.Y.Z -m 'Release vX.Y.Z-N: <short summary>'
git show --no-patch --format=fuller vX.Y.Z-N
git push origin vX.Y.Z-N
```

Pushing the tag requests formal production release. After an explicitly authorized tag push:

1. Read back the tag object and prove that its target SHA equals the confirmed `origin/rX.Y.Z` SHA.
2. Verify the tag pipeline's status, commit SHA, and image tag in GitLab/Drone. A successful build is not production acceptance.
3. Verify that the `farmlynk-prod` deployment-repository MR was created. Do not merge it, deploy, or claim production completion without the authorized QA/release-owner action.
4. Production is complete only after the deployment MR is merged, the rollout uses the expected image, Pods are Ready, migrations succeeded, and key API/frontend checks and logs are accepted. HTTP 200, image construction, or a running Pod alone is insufficient.

## Archive A Release To Main

Production deployment and `rX.Y.Z -> main` are independent actions. When explicitly authorized to prepare the archive MR, compare the release only to current `origin/main`, inspect the diff for unrelated environment changes, and validate the release fixes.

```bash
git fetch origin main rX.Y.Z
git log --oneline origin/main..origin/rX.Y.Z
git diff --stat origin/main...origin/rX.Y.Z
git diff --check origin/main...origin/rX.Y.Z
```

Create or update exactly one `rX.Y.Z -> main` MR only after the appropriate explicit authorization, then read it back. Do not merge it unless the user explicitly requests the final protected-branch merge and has authority.

## Recovery And Reporting

- For a private unshared source branch, confirm no dependency before altering commits. For any shared branch or delivered change, add a corrective commit or use `git revert <bad-commit>`; then repeat the affected integration paths. If the change reached release, use a scoped `fix/<requirement-id>` or `hotfix/rX.Y.Z-<requirement-id>` branch to that release, issue the next incremented production tag after verification, and verify deployment again.
- Never use `git reset --hard`, `git push --force`, `git push --force-with-lease`, or web conflict resolution to repair shared integration, environment, release, or main history. Keep conflicts local to the relevant integration or release worktree, analyze their impact, and wait for user resolution, especially for migration conflicts.
- Report the precise state rather than a generic "released": source/target branches and SHAs, local commits, pushes, MR source-target pairs and states, conflicts, focused tests, migration checks, total/test/non-test diff line counts, tag and pipeline evidence, deployment-MR state, rollout evidence, production acceptance, untested boundaries, and the remaining authorized-owner action.
