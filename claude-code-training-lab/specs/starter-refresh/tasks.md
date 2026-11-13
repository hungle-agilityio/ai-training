# Tasks: starter-refresh

## T1: Bootstrap copies every cited decision record and the prototype path of the new layout

- **ACs:** AC1 to AC8
- **Matrix rows:** M1 to M7
- **Files likely touched:** `ops/bootstrap_manifest.toml`, `ops/bootstrap_layout.py`, `ops/bootstrap.py`, `ops/tests/test_bootstrap_starter_refresh.py` (NEW), `specs/starter-refresh/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T2: Refresh agent-flow-starter and add the Prototype step to the kickoff

- **ACs:** AC9 to AC12
- **Matrix rows:** M8 to M10
- **Files likely touched:** the template repository `hungle-agilityio/agent-flow-starter` (whole refresh), `/mnt/project-files/new-project-setup/kickoff-instructions.md`, Notion pages "Những gì cần cho một dự án mới" and "Nguồn của flow"
- **Depends on:** T1
- **Risk:** low
- **needs-ui:** no
- **Label:** none: another repository, built by hand through the Mac mini; the owner clicks Merge
