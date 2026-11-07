# Start here — GUH Poker sprint handoff

This folder is a context/reference package. It is NOT a replacement for the competition repository, organiser files, or official `CLAUDE.md`.

1. Clone or open **your own fork** `https://github.com/study-holic/poker_bot.git`.
2. Extract this whole folder **inside the fork**, so `poker_bot/GUH_Handoff/START_HERE.md` exists. Do NOT overwrite `poker_bot/CLAUDE.md`, `engine.py`, `game_state.py`, etc.
3. Open Claude Code **from the repo root**.
4. Paste `GUH_Handoff/MASTER_PROMPT.md` into Claude Code (or copy the stand-alone prompt `.txt`). In a new conversation, explicitly tell Claude to read that file and act.
5. The three v4 backup files are inside `GUH_Handoff/baseline_v4/` and use the proper names. Copy into the repository's root **only after** Claude records existing state and chooses to restore that baseline. They are source from an earlier model, NOT officially validated or confirmed optimal.
6. The final submission is NOT the ZIP. The official `python -m submit --team NAME` must create the `.pkl`, and the form requires the pickle plus every `.py` printed in the file manifest.

Current authoritative live rules from the user's event page (7 Nov 2026): two rounds, 10s/move, top five advance, entries until 18:00. User's internal hard stop is **17:50 GMT**.

Do not assume a prior assistant's performance claims were reproduced using the official engine. There are no fresh official benchmark results in this pack.

Source URLs:
- Current event site: https://poker-arena-site.vercel.app/#/
- Submission site: https://poker-arena-site.vercel.app/#/submit
- Submission form: https://forms.gle/usKbBRkG5fkiq6qN9
- User fork: https://github.com/study-holic/poker_bot.git
- Organiser source: https://github.com/Manchester-AI-Society/poker_bot
- Organiser rules: https://github.com/Manchester-AI-Society/poker_bot/blob/main/CLAUDE.md
