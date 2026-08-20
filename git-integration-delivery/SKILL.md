---
name: git-integration-delivery
description: Safely deliver a Git feature branch through long-lived integration/dev and integration/test branches into dev and test. Use when a user asks to push a feature, prepare or create merge requests for dev/test, synchronize integration branches, resolve delivery conflicts, or re-deliver QA fixes under this branch policy.
---

# Git Integration Delivery

## Overview

Keep feature development isolated while allowing authorized owners to merge verified integration branches into protected environment branches. Treat `dev` and `test` as targets only: never merge a feature directly into either branch.

## Enforce The Branch Policy

- Deliver development changes only through `feature -> integration/dev -> dev`.
- Deliver test changes only through `feature -> integration/test -> test`.
- Resolve all delivery conflicts locally on the corresponding integration branch. Do not use the GitLab web conflict resolver.
- Keep `integration/dev` and `integration/test` as long-lived branches. Do not create them if they are absent; report that the project owner must establish them from the latest respective baseline.
- Keep all feature fixes, including QA fixes, on the original feature branch. Re-run both delivery paths after committing the fix.
- Do not merge, push, force-push, create a merge request, or merge a merge request without the user's explicit approval in the current request. Do not assume permission from the word "deliver" alone.

## Inspect Before Changing Git State

1. Identify the repository root, current branch, remotes, worktrees, and working-tree state.

   ```bash
   git rev-parse --show-toplevel
   git status --short --branch
   git branch --show-current
   git remote -v
   git worktree list
   ```

2. Confirm that the current branch is the intended feature branch, not `dev`, `test`, `integration/dev`, or `integration/test`. Stop if the feature work is uncommitted; show the files and ask whether the user wants to commit them.
3. Fetch the current remote references, then verify that both integration branches exist.

   ```bash
   git fetch origin dev test integration/dev integration/test
   git show-ref --verify refs/remotes/origin/integration/dev
   git show-ref --verify refs/remotes/origin/integration/test
   ```

4. Record the feature SHA, intended targets, existing open merge requests, and the repository's focused validation command. Do not guess a test command; inspect project documentation and manifests first.
5. Stage only user-approved files. Before every commit or push, re-run `git status --short` and inspect the intended diff. Preserve unrelated tracked and untracked files.

## Deliver To One Target

Run this procedure once for `integration/dev` with baseline `origin/dev` and target `dev`, then independently for `integration/test` with baseline `origin/test` and target `test`. Always merge the feature branch, never one integration branch into the other.

1. Use the existing worktree that has the integration branch checked out. If none exists, create a separate worktree only after confirming that its path is safe and does not already exist. Keep the feature worktree untouched.
2. Synchronize the local integration branch with its remote using a fast-forward-only update. Stop if local-only commits exist and report them instead of overwriting them.

   ```bash
   git switch integration/<environment>
   git merge --ff-only origin/integration/<environment>
   ```

3. Reconcile the integration branch with its baseline before adding the feature:

   - If `origin/<environment>` is already an ancestor of the integration branch, continue.
   - If the integration branch is an ancestor of `origin/<environment>`, fast-forward it.
   - If both contain unique commits, merge `origin/<environment>` into the integration branch and resolve any conflicts there locally.

   ```bash
   git merge-base --is-ancestor origin/<environment> integration/<environment>
   git merge-base --is-ancestor integration/<environment> origin/<environment>
   git merge --ff-only origin/<environment>
   ```

4. Merge the feature with an explicit merge commit. Resolve conflicts only in this integration worktree. Stage only conflict-resolution files, inspect the merge diff, and finish the merge commit.

   ```bash
   git merge --no-ff <feature-branch>
   git status --short
   git diff --check
   ```

5. Review the changes relative to the target baseline and run the agreed focused validation. State precisely what was and was not tested.

   ```bash
   git log --oneline origin/<environment>..HEAD
   git diff --stat origin/<environment>...HEAD
   git diff --check origin/<environment>...HEAD
   ```

6. Before the user-approved push, report the integration branch, target branch, feature SHA, commits/diff, validation result, conflicts, and whether another open MR already uses the same source/target pair.
7. After explicit approval, push only the intended integration branch without force options. Create or update exactly one merge request from that integration branch to its designated target, then read it back to verify source, target, title, and open state.

   ```bash
   git push origin integration/<environment>
   glab mr create --source-branch integration/<environment> --target-branch <environment>
   glab mr view
   ```

Only the authorized owner merges the verified MR into `dev` or `test`. Do not merge it on the user's behalf unless they explicitly request that action and have authority.

## Preserve MR Description Formatting

Treat an MR description as a Markdown artifact, not a shell-escaped one-line string. Build it with actual newline characters, then pass the completed value as one quoted argument. ANSI-C single quoting preserves Markdown backticks as text while producing real line breaks:

```bash
mr_description=$'## Changes\n- Describe the behavior\n\n## Validation\n- `python manage.py test <scope>`\n\n## Untested\n- State the remaining boundary'
glab mr create --source-branch integration/<environment> --target-branch <environment> --description "$mr_description"
```

For an existing MR, pass the same value to `glab mr update <iid> --description "$mr_description"`. A regular double-quoted argument containing literal `\n` does not create line breaks, and Markdown backticks inside such an argument can be interpreted by the shell. Keep both as data in `mr_description`.

Immediately read the stored Markdown back before reporting the MR:

```bash
glab mr view <iid> --output json --jq .description
```

Completion requires visible headings and list items on separate lines, actual blank lines between sections, literal command text intact, and no visible `\n` sequences. Correct the description and reread it before declaring the MR created or updated.

## Handle Optional Feature Push

Push the feature branch only after confirming the branch and showing its pending commits and status. Use `git push -u origin <feature-branch>` only when the branch has no upstream; otherwise use `git push origin <feature-branch>`. Never use `--force`, `--force-with-lease`, or a destination branch name unless the user explicitly requests and confirms it.

## Report The Result

Report the feature branch and SHA, the two integration SHAs, the exact MR source/target pairs, validation evidence, conflict-resolution commits, untested areas, and remaining owner action. Clearly distinguish local preparation, remote pushes, MR creation, and final merge status.
