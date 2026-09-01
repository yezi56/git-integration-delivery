---
name: git-integration-delivery
description: Safely deliver FarmLynk backend changes through integration branches, controlled release branches, production tags, deployment verification, and main, with conflict-impact and pre-commit risk review gates. Use for FarmLynk branch handoffs, commits, conflict analysis, release preparation, production tags, recovery, or merge-request work; for other repositories, inspect and follow their own local policy.
---

# FarmLynk Git Delivery And Release

## Purpose And Scope

Apply this workflow to the FarmLynk backend repository `back-end-group/farmlynk`. Its code paths are independent:

```text
feature/fix -> integration/dev  -> dev
feature/fix -> integration/test -> test
approved feature/fix -> rX.Y.Z -> tag vX.Y.Z-N -> deployment-repository MR -> production
rX.Y.Z -> main
```

`dev` and `test` are long-lived environment branches, not production-release candidates or substitutes for `main`. Production is selected from an `rX.Y.Z` branch; never promote all of `dev` or `test` by merging it to `release` or `main`.

For a non-FarmLynk repository, do not assume its release branches, CI behavior, migration framework, or deployment repository match this skill. Read its local policy first. The generic environment-integration safeguards below still apply only when they agree with that policy.

## Authorization Boundaries

- Separate local inspection, commits, remote feature pushes, integration pushes, MR creation or update, MR merge, release creation, tag push, deployment-repository MR merge, and production deployment. Require explicit authorization in the current request for every remote mutation and for commits or staging of files.
- A request to "deliver" does not authorize a push, MR, tag, MR merge, or deployment. A production-tag push is a distinct high-impact authorization because it requests production deployment.
- Only an authorized owner merges an MR to `dev`, `test`, `main`, or a protected release branch. Only QA or the release owner merges the deployment-repository MR and confirms production acceptance.
- Preserve unrelated tracked and untracked files. Never stage, commit, push, or add local verification files, `.env` files, credentials, environment addresses, test data, or temporary scripts.
- Treat conflict review and pre-commit review as mandatory gates. A prior request to deliver or commit does not authorize resolving conflicts or crossing a `Critical` or `High` finding.

## Branch Rules

- New ordinary work starts from current `origin/main` as `feat/<task>-<short-english>` or `fix/<task>-<short-english>`. Starting from `dev` or `test` is allowed only for a documented dependency on unpublished environment code.
- Use `hotfix/rX.Y.Z-<short-english>` for an urgent production fix and `rX.Y.Z` for a release candidate. Do not create new numeric, date, personal-prefix, ambiguous `test*`, or per-feature integration branches.
- `integration/dev` and `integration/test` are the only long-lived integration branches. Do not create replacements if they are absent; report that the project owner must establish them from the current target baseline.
- Ordinary work must not merge directly from `feature` or `fix` to `dev`, `test`, or `main`. Do not merge `integration/dev` into `integration/test`, or vice versa.
- Direct `feature` or `fix` to `rX.Y.Z` is a controlled exception: it requires explicit release-owner approval and an MR explaining the validated environments, intended release, migration impact, and rollback plan.
- A private, unshared branch may be rewritten only after confirming no one depends on it. Once pushed, present in an MR, or merged into any integration, environment, release, or main branch, do not reset, rebase-and-force-push, or otherwise rewrite its shared history. Repair with a new fix commit or `git revert`.

## Batch Feature Work Before Integration

- A feature or fix branch may accumulate multiple coherent commits and authorized pushes before it is delivered to an integration branch. Pushing the source branch does not by itself require an `integration/dev` or `integration/test` merge.
- Default to delivering a complete, independently testable batch: finish the related edits, run the focused validation for that batch, then merge the accumulated source HEAD into each required integration branch once. Do not make integration branches mirror every intermediate source-branch push.
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

2. Confirm the requested source, target, and operation. Record source SHA, target SHA, existing open MRs for that source-target pair, and the project-specific focused validation command. Inspect repository documentation and manifests rather than guessing a test command.
3. Fetch only the relevant remote refs, then confirm the required integration, environment, release, or main refs exist. Recheck current status and intended diff immediately before every staging, commit, push, tag, or MR action.

   ```bash
   git fetch origin main dev test integration/dev integration/test
   git show-ref --verify refs/remotes/origin/integration/dev
   git show-ref --verify refs/remotes/origin/integration/test
   git diff --check
   ```

4. Before an ordinary feature commit, verify the branch's baseline. For a normal branch this is `origin/main`; if it intentionally uses an environment baseline, make the dependency explicit in the MR. Follow **Review Before Every Commit** before creating the commit.
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

Start this procedure only for a requested, independently testable source-branch batch. Confirm the source SHA represents all changes intended for the current environment handoff; ordinary intermediate source-branch pushes stay on the feature/fix branch until the batch is ready.

Run this procedure independently for `integration/dev` with baseline `origin/dev` and target `dev`, then for `integration/test` with baseline `origin/test` and target `test`. Always merge the feature/fix branch into the corresponding integration branch, never one integration branch into the other.

1. Use a dedicated worktree containing the integration branch. If none exists, create a separate worktree only after confirming that the path is safe and available; leave the source worktree unchanged.
2. Synchronize the local integration branch with its remote by fast-forward only. Stop and report local-only commits instead of overwriting them.

   ```bash
   git switch integration/<environment>
   git merge --ff-only origin/integration/<environment>
   ```

3. Bring the integration branch up to its own environment baseline before adding the feature/fix:

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

4. Start the source merge without creating its merge commit. If it conflicts, follow **Analyze Conflicts And Wait**. If it merges cleanly, leave the result staged and follow **Review Before Every Commit**.

   ```bash
   git merge --no-ff --no-commit <feature-or-fix-branch>
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

## Prepare And Maintain A Release

Only the release owner creates or changes an `rX.Y.Z` branch. Confirm the exact release version and explicit authorization before making the branch.

```bash
git fetch origin main
git switch -c rX.Y.Z origin/main
git push -u origin rX.Y.Z
```

- A release contains only approved features and release fixes. Do not merge all of `dev` or `test` into it.
- Select a feature/fix only after its relevant `dev` and `test` validation is known. Its controlled `feature/fix -> rX.Y.Z` MR must identify validated environment branch SHAs, the release target, migration impact, and rollback method.
- Once the release is frozen, admit only clearly scoped `fix/...` or `hotfix/...` changes. Re-run focused validation and migration gates against the current release code after every such change.
- Do not assume an old release cannot return to `main`: a subsequent `rX.Y.Z -> main` MR is valid when it contains only commits added since the last release-to-main merge.

## Tag And Verify Production Release

Tag only the latest confirmed commit of the intended release branch. First confirm the exact tag version and increment: a new release starts at `vX.Y.Z-0`; re-releases of the same release use `-1`, `-2`, and so on. Never tag a feature commit.

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

- For a private unshared feature, confirm no dependency before altering commits. For any shared branch or delivered change, add a corrective commit or use `git revert <bad-commit>`; then repeat the affected integration paths. If the change reached release, use a scoped `fix/...` or `hotfix/...` branch to that release, issue the next incremented production tag after verification, and verify deployment again.
- Never use `git reset --hard`, `git push --force`, `git push --force-with-lease`, or web conflict resolution to repair shared integration, environment, release, or main history. Keep conflicts local to the relevant integration or release worktree, analyze their impact, and wait for user resolution, especially for migration conflicts.
- Report the precise state rather than a generic "released": source/target branches and SHAs, local commits, pushes, MR source-target pairs and states, conflicts, focused tests, migration checks, tag and pipeline evidence, deployment-MR state, rollout evidence, production acceptance, untested boundaries, and the remaining authorized-owner action.
