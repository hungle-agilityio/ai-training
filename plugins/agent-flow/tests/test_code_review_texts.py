"""A loop build runs the code-review skill on its changes and a whole epic is reviewed once.

Spec: specs/test-harden/spec.md (AC5 to AC10), issue #498 (AC1, AC2, AC4, AC5, AC6).
Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
WORK_QUEUE = (PLUGIN / "skills" / "work-queue" / "SKILL.md").read_text()
FALLBACK_LINE = "/code-review did not run: <reason>; reviewer only."


def section_between(start: str, end: str) -> str:
    """The text from `start` up to `end`; empty when `start` is missing."""
    begin = WORK_QUEUE.find(start)
    if begin == -1:
        return ""
    stop = WORK_QUEUE.find(end, begin + len(start))
    return WORK_QUEUE[begin : stop if stop != -1 else len(WORK_QUEUE)]


STEP_9 = section_between("9. **Review**", "\n10. **Verify and hand over**")
SUB_STEP_5 = section_between("   5. Write the body", "\n## 3.")
EPIC_HEADING = "\n## Epic review"
EPIC = section_between(EPIC_HEADING, "\n## 2. One new issue").lstrip("\n")
ONE_TARGET = section_between("## One target (from the tick)", "\n## Whose words count")


# M6: step 9 runs the code-review skill at the level of review_level.py


def test_step_9_gets_the_level_from_review_level_py_as_one_plain_command() -> None:
    assert "review_level.py" in STEP_9
    assert "uv run python <this skill's folder>/review_level.py" in STEP_9
    assert "--base origin/<base branch of the pull request to be opened>" in STEP_9
    assert "first line" in STEP_9 and "`standard`" in STEP_9 and '"high"' in STEP_9
    assert "other than 0" in STEP_9


def test_step_9_marks_new_files_with_intent_to_add_before_the_review() -> None:
    assert "git add --intent-to-add" in STEP_9
    assert STEP_9.index("git add --intent-to-add") < STEP_9.index("`code-review`")


def test_step_9_runs_code_review_with_medium_for_standard_and_high_for_high() -> None:
    assert "`code-review` skill" in STEP_9 and "Skill tool" in STEP_9
    assert '"medium"' in STEP_9 and '"high"' in STEP_9
    assert "no target" in STEP_9


def test_step_9_runs_the_reviewer_when_the_rules_require_it_or_the_level_is_high() -> None:
    assert "`reviewer`" in STEP_9
    assert "rules/workflow.md" in STEP_9
    assert 'level is "high"' in STEP_9 or "level is high" in STEP_9


def test_step_9_fixes_each_finding_or_dismisses_it_with_a_one_line_reason() -> None:
    assert "fixed" in STEP_9 and "test first" in STEP_9 and "`implementer`" in STEP_9
    assert "dismissed" in STEP_9 and "one-line reason" in STEP_9
    assert "false positive" in STEP_9


def test_step_9_allows_two_rounds_and_fails_the_issue_after_round_two() -> None:
    assert "at most two rounds" in STEP_9
    assert "one more review at the same level" in STEP_9
    assert "`agent:failed`" in STEP_9
    assert "(with the marker)" in STEP_9
    assert "no pull request" in STEP_9


def test_step_9_no_longer_says_review_only_with_reviewer_when_workflow_requires_it() -> None:
    assert "**Review** with `reviewer` when `rules/workflow.md` requires it, at most" not in (
        WORK_QUEUE
    )


# M7: the fallback when the code-review skill cannot run


def test_step_9_falls_back_to_the_reviewer_when_code_review_cannot_run() -> None:
    assert "cannot run" in STEP_9
    assert "no `code-review`" in STEP_9 or "has no `code-review`" in STEP_9
    assert "twice" in STEP_9
    assert "runs `reviewer` instead" in STEP_9
    assert "goes on" in STEP_9 or "go on" in STEP_9


def test_step_9_names_the_did_not_run_line_as_the_first_line_of_the_code_review_file() -> None:
    assert f"`{FALLBACK_LINE}`" in STEP_9
    assert "first line" in STEP_9 and "Code review file" in STEP_9


# AC4: the code review file that step 10 passes to the draft


def test_step_10_passes_the_code_review_file_written_with_the_write_tool() -> None:
    assert "--code-review out/pr-draft/code-review.md" in SUB_STEP_5
    assert "Write tool" in SUB_STEP_5


def test_the_code_review_file_holds_level_rounds_and_the_findings_table() -> None:
    assert "`Level: standard`" in SUB_STEP_5
    assert "`Level: high (<matched paths, comma separated>)`" in SUB_STEP_5
    assert "`Rounds: <n>`" in SUB_STEP_5
    assert "`| Finding | File | Result |`" in SUB_STEP_5
    assert '"fixed"' in SUB_STEP_5 and "`dismissed: <reason>`" in SUB_STEP_5
    assert "`No findings.`" in SUB_STEP_5


def test_the_code_review_file_is_written_before_the_commit_right_after_the_review() -> None:
    assert "before the commit of sub-step 4" in SUB_STEP_5
    assert "right after the review ends" in SUB_STEP_5


# M10: the epic review section


def test_the_epic_review_section_sits_after_section_1_and_before_section_2() -> None:
    assert EPIC.startswith("## Epic review")
    assert WORK_QUEUE.index("## 1. The owner's answers first") < WORK_QUEUE.index(EPIC_HEADING)
    assert WORK_QUEUE.index(EPIC_HEADING) < WORK_QUEUE.index("## 2. One new issue")


def test_one_target_has_a_bullet_for_the_epic_review() -> None:
    assert "**Epic review:**" in ONE_TARGET
    assert "`## Epic review`" in ONE_TARGET


def test_the_epic_review_applies_to_its_prompt_on_the_epic_branch() -> None:
    assert "Use the work-queue skill for pull request #<N> only: epic review." in EPIC
    assert "`epic/<n>-<slug>`" in EPIC
    assert "head of pull request #N" in EPIC


def test_the_epic_review_runs_code_review_high_on_the_pull_request() -> None:
    assert "`code-review` skill" in EPIC
    assert '"high"' in EPIC
    assert "`#<N>`" in EPIC


def test_the_epic_review_makes_one_fix_attempt_per_finding_and_commits_it_alone() -> None:
    assert "one at a time" in EPIC and "clean tree" in EPIC
    assert "one fix attempt" in EPIC
    assert "test first" in EPIC and "`implementer`" in EPIC
    assert "`create-commit`" in EPIC and "`Part of #<epic issue>`" in EPIC
    assert "alone" in EPIC


def test_the_epic_review_drops_a_failed_attempt_and_leaves_the_finding() -> None:
    assert "git add -A" in EPIC
    assert "git switch --discard-changes <epic branch>" in EPIC
    assert "`left: <reason>`" in EPIC


def test_the_epic_review_pushes_the_epic_branch_without_a_new_pull_request() -> None:
    assert "git push" in EPIC
    assert "no new pull request" in EPIC
    assert "when it made a commit" in EPIC


def test_the_epic_review_builds_no_verify_report() -> None:
    assert "No verify report" in EPIC
    assert "#495" in EPIC


def test_the_epic_review_comment_has_both_markers_the_level_and_the_table() -> None:
    assert "`<!-- work-queue -->`" in EPIC and "`<!-- epic-review -->`" in EPIC
    assert EPIC.index("<!-- work-queue -->") < EPIC.index("<!-- epic-review -->")
    assert "`## Epic review`" in EPIC
    assert "`Level: high`" in EPIC
    assert "`| Finding | File | Result |`" in EPIC
    assert "`fixed in <short sha>`" in EPIC
    assert "`No findings.`" in EPIC
    assert "pull request #N" in EPIC


def test_the_epic_review_waits_for_ci_and_sets_the_label_as_after_a_push() -> None:
    assert "waits for CI" in EPIC
    assert "After a push" in EPIC


def test_the_epic_review_is_one_round_only_and_ends_at_once_if_already_commented() -> None:
    assert "One round only" in EPIC
    assert "never reviews again" in EPIC
    assert "already has the comment" in EPIC
    assert "ends the run at once" in EPIC


# M11: findings that would change the requirement, and the fallback in an epic


def test_a_finding_that_would_change_an_issue_requirement_is_left_not_fixed() -> None:
    assert "left: changes the requirement of #<n>" in EPIC
    assert "never fixed" in EPIC


def test_the_epic_review_falls_back_to_the_reviewer_on_the_diff_against_main() -> None:
    assert "cannot run" in EPIC
    assert "`reviewer`" in EPIC
    assert "git diff origin/main...HEAD" in EPIC
    assert f"`{FALLBACK_LINE}`" in EPIC
    assert "level line" in EPIC
