# Intent: release-deploy

## Problem

The auto-deploy spec puts every merge to `main` online once its checks are green. The owner wants the live site to change only when a sprint or an epic is finished, so that QA, BA and clients look at a whole piece of work and not at half-done steps.

## Goal

Merging into `main` no longer changes the live site. When a sprint is done, the owner presses one card in the Project; the Mac mini cuts a release branch `release/sprint-N` from the current green `main`, tags it with the date, and moves the branch Render follows, so Render deploys exactly that commit.

## Users

The owner, who decides when a release goes out, and the people the owner sends the link to (QA, BA, clients).

## Out of scope

- Hotfixes on a release branch: a fix goes through `main` and a new release.
- A GitHub ruleset for the release branches (a written rule only, ADR-017).
- Changes to `.github/` or to the `Checks` workflow.
- Release notes pages or GitHub Releases; the release prints the list of merged pull requests.
- Changes to the app's pages, settings or data.
