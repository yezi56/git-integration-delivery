#!/usr/bin/env python3
"""Report total, test, and non-test Git diff line counts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import PurePosixPath


TEST_DIRS = {
    "__snapshots__",
    "__tests__",
    "cypress",
    "fixture",
    "fixtures",
    "spec",
    "specs",
    "test",
    "testdata",
    "tests",
}


def is_default_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    pure_path = PurePosixPath(normalized)
    if any(part in TEST_DIRS for part in pure_path.parts[:-1]):
        return True

    name = pure_path.name
    if name in {"conftest.py", "test.py", "tests.py"}:
        return True
    if name.startswith("test_"):
        return True
    if re.search(r"_(test|spec)\.[^.]+$", name):
        return True
    if ".cy." in name or ".test." in name or ".spec." in name:
        return True
    return bool(
        re.match(
            r"^(cypress|jest|playwright|pytest|tox|vitest)(\.config)?\.", name
        )
    )


def parse_numstat(raw: bytes) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    fields = raw.split(b"\0")
    index = 0

    while index < len(fields) and fields[index]:
        header = fields[index]
        index += 1
        parts = header.split(b"\t", 2)
        if len(parts) != 3:
            raise ValueError("unexpected git --numstat -z record")

        additions_raw, deletions_raw, path_raw = parts
        if path_raw:
            path = path_raw.decode(errors="surrogateescape")
        else:
            if index + 1 >= len(fields):
                raise ValueError("incomplete rename/copy record")
            index += 1  # The old path is not used for final-path classification.
            path = fields[index].decode(errors="surrogateescape")
            index += 1

        binary = additions_raw == b"-" or deletions_raw == b"-"
        entries.append(
            {
                "path": path,
                "additions": 0 if binary else int(additions_raw),
                "deletions": 0 if binary else int(deletions_raw),
                "binary": binary,
            }
        )

    return entries


def compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    try:
        return [re.compile(pattern) for pattern in patterns]
    except re.error as error:
        raise ValueError(f"invalid path regex: {error}") from error


def classify_path(
    path: str,
    test_patterns: list[re.Pattern[str]],
    non_test_patterns: list[re.Pattern[str]],
) -> bool:
    explicit_test = any(pattern.search(path) for pattern in test_patterns)
    explicit_non_test = any(pattern.search(path) for pattern in non_test_patterns)
    if explicit_test and explicit_non_test:
        raise ValueError(f"path matches both test and non-test overrides: {path}")
    if explicit_test:
        return True
    if explicit_non_test:
        return False
    return is_default_test_path(path)


def summarize(entries: list[dict[str, object]]) -> dict[str, int]:
    additions = sum(int(entry["additions"]) for entry in entries)
    deletions = sum(int(entry["deletions"]) for entry in entries)
    return {
        "files": len(entries),
        "additions": additions,
        "deletions": deletions,
        "changed_lines": additions + deletions,
        "binary_files": sum(bool(entry["binary"]) for entry in entries),
    }


def run_git(repo: str, arguments: list[str]) -> bytes:
    command = [
        "git",
        "-C",
        repo,
        "diff",
        "--numstat",
        "-z",
        "--find-renames",
        "--no-ext-diff",
        "--no-textconv",
        *arguments,
        "--",
    ]
    return subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout


def resolve_ref(repo: str, ref: str) -> str:
    return subprocess.run(
        ["git", "-C", repo, "rev-parse", "--verify", f"{ref}^{{commit}}"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count total, test, and non-test changed text lines in a Git diff."
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--cached", action="store_true", help="compare HEAD to index")
    scope.add_argument("--from", dest="from_ref", help="starting commit or ref")
    scope.add_argument("--self-test", action="store_true")
    parser.add_argument("--to", dest="to_ref", default="HEAD", help="ending ref")
    parser.add_argument("--repo", default=".", help="repository path")
    parser.add_argument("--test-regex", action="append", default=[])
    parser.add_argument("--non-test-regex", action="append", default=[])
    parser.add_argument("--show-paths", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def run_self_test() -> None:
    raw = (
        b"3\t2\tsrc/service.py\0"
        b"4\t1\ttests/test_service.py\0"
        b"0\t0\t\0old_test.py\0src/service_test.go\0"
        b"-\t-\tassets/image.png\0"
    )
    entries = parse_numstat(raw)
    assert len(entries) == 4
    assert entries[2]["path"] == "src/service_test.go"
    assert entries[3]["binary"] is True
    assert is_default_test_path("tests/test_service.py")
    assert is_default_test_path("internal/service_test.go")
    assert is_default_test_path("web/widget.spec.ts")
    assert is_default_test_path("cypress/e2e/login.cy.ts")
    assert is_default_test_path("web/__snapshots__/widget.snap")
    assert not is_default_test_path("src/contest.py")
    assert summarize(entries)["changed_lines"] == 10
    assert classify_path("src/service.py", [re.compile(r"^src/")], [])
    try:
        classify_path(
            "src/service.py", [re.compile(r"^src/")], [re.compile(r"service")]
        )
    except ValueError:
        pass
    else:
        raise AssertionError("overlapping path overrides must fail")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        print("self-test passed")
        return 0

    try:
        test_patterns = compile_patterns(args.test_regex)
        non_test_patterns = compile_patterns(args.non_test_regex)
        if args.cached:
            from_sha = resolve_ref(args.repo, "HEAD")
            scope = {"mode": "cached", "from": from_sha, "to": "INDEX"}
            raw = run_git(args.repo, ["--cached"])
        else:
            from_sha = resolve_ref(args.repo, args.from_ref)
            to_sha = resolve_ref(args.repo, args.to_ref)
            scope = {"mode": "commits", "from": from_sha, "to": to_sha}
            raw = run_git(args.repo, [from_sha, to_sha])

        entries = parse_numstat(raw)
        test_entries = []
        non_test_entries = []
        for entry in entries:
            target = (
                test_entries
                if classify_path(
                    str(entry["path"]), test_patterns, non_test_patterns
                )
                else non_test_entries
            )
            target.append(entry)

        result = {
            "scope": scope,
            "total": summarize(entries),
            "test": summarize(test_entries),
            "non_test": summarize(non_test_entries),
            "test_paths": [entry["path"] for entry in test_entries],
            "non_test_paths": [entry["path"] for entry in non_test_entries],
        }
    except (subprocess.CalledProcessError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"scope: {scope['from']} -> {scope['to']} ({scope['mode']})")
    for label in ("total", "test", "non_test"):
        counts = result[label]
        print(
            f"{label}: files={counts['files']} +{counts['additions']} "
            f"-{counts['deletions']} changed_lines={counts['changed_lines']} "
            f"binary_files={counts['binary_files']}"
        )
    if args.show_paths:
        for label in ("test_paths", "non_test_paths"):
            print(f"{label}:")
            for path in result[label]:
                print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
