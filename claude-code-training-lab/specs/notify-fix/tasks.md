# Tasks: notify-fix

## T1: Urgent loop messages ring, the rest arrive silently

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC9 (the `test_tick_notify_priority.py` part), AC8 (the "Rings" column)
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_notify_priority.py` (new)
- **Depends on:** none (the tick holds it back while another issue that touches `ops/agent_tick.py` builds or waits for review)
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T2: The loop starts at login and says so

- **ACs:** AC5 (the `start-loop.sh` call), AC6, AC7, AC8 ("Start at login", "No messages?"), AC9 (the `test_launchd_plist.py` part)
- **Files likely touched:** `ops/start-loop.sh`, `ops/install-launchd.sh` (new), `ops/README.md`, `ops/tests/test_launchd_plist.py` (new)
- **Depends on:** T1 (it calls `agent_tick.py started`; both change `ops/README.md`)
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`
