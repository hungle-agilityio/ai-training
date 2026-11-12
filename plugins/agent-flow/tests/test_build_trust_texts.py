"""A loop build plans, has a test author write its tests, fills the matrix and writes decisions.

Spec: specs/build-trust/spec.md (AC6 to AC14).
Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
WORK_QUEUE = (PLUGIN / "skills" / "work-queue" / "SKILL.md").read_text()
WRITE_ISSUE = (PLUGIN / "skills" / "write-issue" / "SKILL.md").read_text()
TEST_AUTHOR = PLUGIN / "agents" / "test-author.md"
IMPLEMENTER = (PLUGIN / "agents" / "implementer.md").read_text()
SECTION_2 = WORK_QUEUE[WORK_QUEUE.index("## 2. One new issue") : WORK_QUEUE.index("\n## 3.")]
SECTION_1 = WORK_QUEUE[
    WORK_QUEUE.index("## 1. The owner's answers first") : WORK_QUEUE.index("\n## Status labels")
]
VERIFY = SECTION_2[
    SECTION_2.index("**Verify and hand over**") : SECTION_2.index("**Close the run.**")
]
LABEL_CREATE = (
    "gh label create agent:plan-review --color 5319E7 "
    '--description "The loop posted a plan and waits for the owner\'s approval"'
)
LABEL_EDIT = "gh issue edit <n> --add-label agent:plan-review --remove-label agent:running"
APPROVAL_WORDS = ("lgtm", "ok", "duyệt", "approved", "approve", "looks good", "ship it")


# M6: the test author sub-agent


def test_the_test_author_has_its_name_role_tools_and_model() -> None:
    text = TEST_AUTHOR.read_text()
    front = text.split("---")[1]

    assert "name: test-author" in front.splitlines()
    description = next(line for line in front.splitlines() if line.startswith("description:"))
    assert description.startswith("description: Builder of tests.")
    assert "failing tests" in description and "before any code" in description
    assert "tools: Read, Grep, Glob, Edit, Write, Bash" in front.splitlines()
    assert "model: sonnet" in front.splitlines()


def test_the_test_author_text_has_the_four_numbered_rules() -> None:
    body = TEST_AUTHOR.read_text().split("---", 2)[2]
    numbered = [line for line in body.splitlines() if line[:3] in ("1. ", "2. ", "3. ", "4. ")]

    assert len(numbered) == 4
    assert "issue body" in numbered[0] and "Done when" in numbered[0]
    assert "## Test matrix rows" in numbered[0]
    assert "never given the plan" in numbered[0]
    assert '"unit" or "integration"' in numbered[1] and "one test" in numbered[1]
    assert '"browser" or "manual"' in numbered[1] and "no test" in numbered[1]
    assert "path::test_name" in numbered[2] and "fails" in numbered[2]
    assert "already passes" in numbered[2]
    assert "Never write or change application code" in numbered[3]
    assert "already exists on main" in numbered[3] and "never commit" in numbered[3]


# M7: the order of the steps in section 2


def test_section_2_runs_plan_plan_stop_tests_build_in_that_order() -> None:
    order = [
        SECTION_2.index(name)
        for name in (
            "**Plan**",
            "**Plan stop**",
            "**Tests**",
            "**Build**",
            "**Review**",
            "**Verify and hand over**",
            "**Close the run.**",
        )
    ]

    assert order == sorted(order)
    for number, name in enumerate(("Plan", "Plan stop", "Tests", "Build"), 5):
        assert f"{number}. **{name}**" in SECTION_2
    assert "10. **Verify and hand over**" in SECTION_2 and "11. **Close the run.**" in SECTION_2


def test_the_plan_step_runs_for_every_difficulty_and_easy_gets_three_lines() -> None:
    plan = SECTION_2[SECTION_2.index("**Plan**") : SECTION_2.index("**Plan stop**")]

    assert "every difficulty" in plan and "Easy" in plan
    assert "what to change, the test to write first, how to verify" in plan
    assert "approved plan" in plan


def test_the_tests_step_runs_the_test_author_and_copies_its_files() -> None:
    tests = SECTION_2[SECTION_2.index("**Tests**") : SECTION_2.index("**Build**")]

    assert "## Test matrix rows" in tests and "test-author" in tests
    assert "issue body only" in tests
    assert "out/test-author/" in tests and "same file names" in tests
    assert "skipped" in tests


def test_the_build_step_gets_the_plan_and_the_test_authors_report() -> None:
    build = SECTION_2[SECTION_2.index("**Build**") : SECTION_2.index("**Review**")]

    assert "plan" in build and "test author's report" in build
    assert "Existing tests that change" in build and "**Test** with `test-runner`" in build


def test_the_old_step_numbers_are_updated() -> None:
    assert '"no link, no pull request" (step 10)' in WORK_QUEUE
    draft = (PLUGIN / "skills" / "draft-pull-request" / "SKILL.md").read_text()
    assert "`work-queue` step 10" in draft and "`work-queue` step 8" not in draft


# M8: the plan stop


def test_the_plan_stop_posts_the_plan_with_both_markers_and_the_label() -> None:
    stop = SECTION_2[SECTION_2.index("**Plan stop**") : SECTION_2.index("**Tests**")]

    assert "risk:high" in stop
    assert "<!-- work-queue -->" in stop and "<!-- plan -->" in stop
    assert "## Plan" in stop
    assert LABEL_CREATE in stop
    assert LABEL_EDIT in stop
    assert "no commit pushed and no pull request" in stop


def test_the_plan_stop_names_every_approval_word_and_who_may_approve() -> None:
    stop = SECTION_2[SECTION_2.index("**Plan stop**") : SECTION_2.index("**Tests**")]

    for word in APPROVAL_WORDS:
        assert word in stop
    assert "project.owner" in stop and "approved" in stop
    assert "no such comment" in stop and "`agent:ready` again" in stop
    assert "Comments by other logins count for nothing" in stop
    assert "agent:plan-review" in stop and "skips Plan" in stop


def test_the_plan_stop_plans_again_on_other_comments_and_spares_other_issues() -> None:
    stop = SECTION_2[SECTION_2.index("**Plan stop**") : SECTION_2.index("**Tests**")]

    assert "plans again" in stop and "owner's input" in stop
    assert "stops again" in stop
    assert 'An issue without "risk:high" never stops for its plan.' in stop


# M9: the implementer may not weaken the tests


def test_the_implementer_never_deletes_skips_or_weakens_the_test_authors_tests() -> None:
    assert "name: implementer" in IMPLEMENTER and "model: sonnet" in IMPLEMENTER
    assert "test author" in IMPLEMENTER and "failing tests" in IMPLEMENTER
    assert "never deletes, skips or weakens" in IMPLEMENTER
    for weakening in ("removing an assertion", "widening an expected value", "skip or xfail"):
        assert weakening in IMPLEMENTER


def test_the_implementer_may_change_a_contradicting_test_and_says_which() -> None:
    assert "contradicts an AC" in IMPLEMENTER
    assert "only so that it matches that AC" in IMPLEMENTER
    assert "which test, which AC and why" in IMPLEMENTER


def test_the_implementer_keeps_its_six_rules() -> None:
    body = IMPLEMENTER.split("---", 2)[2]

    assert "Never change the requirement of the issue" in body
    assert "Never commit, push or touch GitHub" in body
    assert "Fix review findings in at most two rounds" in body


# M10: the matrix key


def test_verify_writes_the_matrix_key_one_entry_per_row_in_table_order() -> None:
    assert '"matrix"' in VERIFY and "## Test matrix rows" in VERIFY
    assert "in table order" in VERIFY
    for key in ('"row"', '"ac"', '"test"', '"status"', '"evidence"'):
        assert key in VERIFY
    for status in ('"PASS"', '"FAIL"', '"MANUAL"'):
        assert status in VERIFY
    assert "path::test_name" in VERIFY
    assert "no such test" in VERIFY or "no test checks the row" in VERIFY


def test_verify_writes_no_matrix_key_without_the_section() -> None:
    assert "without" in VERIFY and "writes no" in VERIFY
    assert 'writes no "matrix" key' in VERIFY


def test_verify_compares_the_test_author_files_before_the_report() -> None:
    compare = VERIFY.index("out/test-author/")

    assert compare < VERIFY.index("build-verify-report")
    assert "changed test" in VERIFY and "is gone" in VERIFY


def test_verify_passes_the_plan_and_tests_changed_files_to_the_draft() -> None:
    assert "--plan out/pr-draft/plan.md" in VERIFY
    assert "--tests-changed out/pr-draft/tests-changed.md" in VERIFY
    assert "Approved by the owner on <YYYY-MM-DD> (<link to the plan comment>)." in VERIFY
    assert "- `path::test_name`: AC<n>, <why>" in VERIFY
    assert "None." in VERIFY


# M12: the decisions file


def test_the_decisions_file_has_its_heading_table_and_empty_line() -> None:
    assert "**Decisions file**" in SECTION_2
    decisions = SECTION_2[SECTION_2.index("**Decisions file**") :]

    assert '"/decisions/T<k>.md"' in decisions and "## Files likely touched" in decisions
    assert "# Decisions during build: T<k> (#<N>)" in decisions
    assert "| Question | Chosen | Rejected | Why | From |" in decisions
    assert '"owner" or "build"' in decisions
    assert "No decision beyond the issue." in decisions
    assert "writes no decisions file" in decisions


def test_a_change_request_that_changes_behaviour_adds_a_line_to_the_decisions_file() -> None:
    lines = [line for line in SECTION_1.splitlines() if "decisions/T<k>.md" in line]

    assert len(lines) == 1
    line = lines[0]

    assert "changes behaviour" in line
    assert '"From" = "owner"' in line and "link" in line


# M13: write-issue


def test_write_issue_lists_the_decisions_file_and_the_risk_high_line() -> None:
    section = WRITE_ISSUE[WRITE_ISSUE.index("## 7. Handing an issue to the loop") :]

    assert "10. " in section and "11. " in section
    assert "## Files likely touched" in section
    assert "`paths.specs_dir`" in section and "decisions/T<k>.md" in section
    assert "(NEW)" in section
    assert "risk:high" in section and "Summary" in section
    assert "stops after the plan until the owner approves it" in section
    assert "specs/<feature>" not in WRITE_ISSUE
