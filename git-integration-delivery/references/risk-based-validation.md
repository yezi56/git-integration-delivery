# Risk-Based Validation

Use this reference to select validation proportional to the proposed tree's risk. The goal is strong evidence for affected behavior without rerunning an unrelated full suite at every Git step.

## Record The Validation Plan

Before the first source commit and again whenever the diff expands, record:

- The exact proposed tree SHA from `git write-tree`, or `<commit>^{tree}` for an existing commit.
- Changed behavior, affected modules, callers, contracts, and operational surfaces.
- Selected validation level, commands, environment, and why that level is sufficient.
- Untested boundaries and the condition that would require broader validation.

Repository policy or an explicit user request overrides the defaults below.

## Level 1: Commit Checks

Use for every proposed commit:

- Review the complete staged diff and run `git diff --cached --check`.
- Run repository-required formatting, generation, compile, static-analysis, or configuration validation for the changed paths.
- Run the narrowest meaningful tests that exercise the changed behavior and its failure path.
- For documentation-only or bounded metadata changes, the relevant parser, schema, link, or configuration validator may replace runtime tests. State why runtime behavior is unaffected.

Level 1 is normally sufficient for a small local change confined to one module with stable interfaces. It does not mean running the repository's full suite.

## Level 2: Affected-Surface Validation

Add Level 2 when a change crosses a module boundary or when preparing an integration handoff:

- Test the changed module plus directly affected callers, consumers, adapters, serializers, and contract tests.
- Validate the final staged integration tree, because the target baseline can change behavior even when the source commit already passed.
- Run migration gates whenever migrations are present.
- Include the smallest meaningful service, database, or API integration test when unit tests cannot exercise the changed contract.

Level 2 is the default for `integration/dev` and `integration/test` handoffs. It can still be a focused selection rather than the full suite.

## Level 3: Full Validation

Run the repository's full suite, or require equivalent successful CI evidence, when any of these triggers applies:

- Authentication, authorization, tenant isolation, credentials, cryptography, or security middleware changes.
- Database schema or migration changes, destructive writes, data backfills, or rollback-sensitive persistence changes.
- Shared middleware, startup wiring, dependency or lockfile changes, global configuration, generated code, build tooling, or CI/CD changes.
- Public or cross-service API/event contracts, shared serialization, or code used across many modules.
- Concurrency, transaction, retry, idempotency, ordering, lease, or duplicate-delivery behavior with broad impact.
- A conflict resolution combines independently changed behavior across modules or makes the affected surface difficult to bound.
- Tests or test infrastructure are removed, weakened, or changed in a way that reduces confidence.
- The diff is unusually broad, the impact cannot be bounded reliably, or focused validation exposes failures outside the expected surface.
- A release candidate is being prepared for a production tag and repository policy does not define another release suite.

A trigger may be cleared by stronger evidence that narrows the impact, but state that evidence explicitly. Do not silently downgrade validation.

## Reuse Existing Evidence

Do not rerun tests only because a ref name, commit object, push, or MR changed.

Reuse a successful result only when all of these are true:

- The exact Git tree SHA is identical.
- The command, dependency set, runtime version, relevant services, and configuration are equivalent.
- The result is recent enough for the current delivery and no external contract it depends on has changed.
- The recorded output proves success and identifies the tested tree or commit.

Record reusable evidence as:

```text
tree=<tree-sha>
level=<1|2|3>
command=<exact command>
environment=<local worktree or CI job and relevant versions>
result=<pass/fail and evidence link or captured output>
```

If an integration merge produces the same tree as already validated, reuse the evidence and run only integration-specific checks. If its tree differs, select validation again for the new tree.

Successful required CI for the exact commit/tree can satisfy Level 3. Do not duplicate it locally unless local reproduction is needed, CI omits a required surface, or the user explicitly requests it.

## Failure And Blocking Rules

- A failed required check is a blocker until understood and resolved or explicitly accepted by the authorized owner.
- Inability to run a full suite is a blocker only when Level 3 is required or the missing coverage could conceal a `Critical` or `High` defect.
- Inability to run a focused test is a blocker when no other evidence covers the changed high-risk behavior.
- For lower-risk gaps, report the untested boundary and residual risk; do not inflate the validation level merely to avoid stating uncertainty.
