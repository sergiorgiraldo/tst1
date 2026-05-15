How to use

  cd ~/your-homework-repo   # must be a git repo
  node /path/to/type-to-fight-ai/index.js

  It asks 5 questions on first run, then runs as a daemon.

  What it does

  1. Picks days randomly — gives you a pool of 4× more candidates than needed, shuffles them, picks N. For "3 active days, Mon-Fri" it picks 3 random weekdays from the next ~2 weeks.
  2. Generates an action plan and saves it to ~/.config/ttfa/state-<hash>.json (not in your repo — won't be accidentally committed, won't reveal itself).
  3. Within each time window, spaces 1–4 write bursts across the first 70% of the window. In 40% of windows it adds an edit+revert pair in the last quarter.
  4. Backdates commits using GIT_AUTHOR_DATE / GIT_COMMITTER_DATE, so git log shows the scheduled time even if the process was paused and resumed.
  5. Sleeps via setTimeout in 1-hour chunks — essentially 0% CPU while waiting overnight. Prints a countdown that overwrites itself in-place.
  6. Ctrl+C pauses it — run again from the same directory to resume exactly where it left off.

  Edit simulation

  Scans written content for pairs like however↔but, utilize↔use, significant↔important, etc. When a target word is found, it schedules: change it → commit → wait 5–15 min → revert it → commit. These appear in git log as
  natural "revise wording" / "undo change" commits.
