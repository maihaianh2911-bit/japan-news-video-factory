# japan-news-video-factory — notes for Claude

The owner is Vietnamese and not technical: answer in short, simple Vietnamese, no jargon. Their standing decisions
are in `maihaianh2911-bit/japan-video-factory` → `docs/HANDOVER.md` (real pictures only, Claude looks at every
picture, a script the owner sends is translated faithfully to Japanese and never cut or rewritten, quality is not
traded for usage).

This repo makes vertical Japanese news shorts (1080×1920): news frame, VOICEVOX voice 青山龍星, captions timed to
the voice. The daily schedule is off (owner, 12/11/2026). Since 13/11/2026 it works like the owner's other channels:
one issue `[Tin Nhật] …` = one video, opened by the owner from the issue form or by you from a chat. The machine
steps run in `.github/workflows/news-video.yml` (results on the `renders` branch); Claude's steps at each label are
in `AGENT_JNEWS.md`. Unattended, the owner's Claude task "japan-video-factory" does them when GitHub calls it
(it also checks `jnews-*` issues, see `maihaianh2911-bit/japan-video-factory` → `AGENT_NIGHTLY.md`), or this
repo's own task when each repo has its own Claude seat (its prompt: "Làm theo AGENT_JNEWS.md của repo
maihaianh2911-bit/japan-news-video-factory."); either needs the secrets `CLAUDE_TASK_URL` and `CLAUDE_TASK_TOKEN` in this repo. There is no hourly run: a missed call waits for the
button "Gọi Claude ngay" (`wake.yml`) or a chat.

## When you were started by GitHub (a Claude task, nobody in the chat)
The prompt may be as short as "Làm việc đang chờ trong repo này" ("do the work waiting in this repo"), and GitHub
adds a line such as "Phiếu tin Nhật số 2: ảnh đã tìm xong, chờ chọn ảnh". Then: follow `AGENT_JNEWS.md` from §0 (its first check lists the `jnews-*` issues waiting for you). Nobody answers questions, so do not ask; comments go on the issues
(🤖, Vietnamese).

## When the owner pastes a script in a chat
1. Create one issue in this repo: title `[Tin Nhật] <Japanese headline> — <main idea in Vietnamese>`, body with
   the sections of the issue form (`.github/ISSUE_TEMPLATE/tin-nhat.yml`): `### Kịch bản (bắt buộc)` = the script
   exactly as pasted, `### Nguồn tin (không bắt buộc)`, `### Ngày của tin (không bắt buộc)`, `### Ghi chú (không
   bắt buộc)` (`_No response_` when empty). No labels: the workflow adds them.
2. Do the steps of `AGENT_JNEWS.md` for that issue right away (claim with `jnews-busy`). While a machine step runs,
   say so in one line and wait; if the owner does not want to wait, stop after any step: the Claude task continues
   from the labels when GitHub calls it.
3. Give the owner the links to the video, the subtitles and `credits.txt`.

The workflow only runs for files on `main`: story files and their picks are pushed to `main` (the owner asked
for this way of working on 12/11/2026). If the session may only push to its own branch, say so in one line and
ask the owner to allow `main`.

## Story format, pictures and preview (used by `AGENT_JNEWS.md`)
1. Write `stories/<date>-<short-name>.json` (see `stories/mau-boj.json`; file name in ASCII letters, digits, `.`,
   `_`, `-` only) and push it to `main`. Every story file added, changed or renamed in a push gets its own run.
   - `title` (not shown in the video), `date` (shown on screen), `source` (shown as 出典; leave out if there is
     none), `stage: "find"`, `issue` (the issue number: the workflow then moves its labels, comments and calls
     Claude after each step).
   - `scenes`: one idea each. `label` (short tag), `headline` (≤ 2 lines, `\n` between; longer ones get a smaller
     font, up to 3 lines), `lines` (a list: the script, in Japanese, sentence by sentence — every sentence of the
     owner's script, nothing added), optional `value` (a big figure such as `0.5％`) and `evidence` (small text).
     Where they appear: on a picture scene, headline, then value, then evidence under each other below the picture
     (evidence only if it fits above the captions — the preview prints a warning when it does not); on a text card
     (no picture), headline, value, then evidence. A card shows nothing else: no title, so give a text card an
     `evidence` or a `value`. A line the voice may misread is written `{"text": "caption", "say": "reading in kana"}`.
   - `searches`: Wikimedia Commons searches, numbered from 1 in order (English works best; `incategory:"…"` for a
     person, building or place). Only append to the list later: the picks use the numbers, and a pick whose search
     text changed is refused.
   - Check before pushing: `python -m news.custom stories/<name>.json` lists every problem (unknown keys such as
     `photos`, `lines` not a list, bad `focus`/`fit`, missing fields) and the scenes without a picture.
2. The push runs the workflow (find stage, ~2 min). First check that the run for your commit succeeded (the
   session's GitHub tools `actions_list` / `actions_get`); then `git fetch origin renders` and check that
   `<name>/find/status.json` has your commit (`commit`) before trusting the folder. Look at
   `<name>/find/sheet_<k>.jpg` yourself. A search with no usable picture has no `sheet_<k>.jpg` (0 results in
   `index.json`); a search that failed has `"error"` in `index.json`, the run is red and `status.json` says
   `"outcome": "partial"` — run it again (re-run the job, or Run workflow → `story` + the name) and only the
   failed searches are tried again. If a scene has no fitting picture, append searches and push again.
3. Put the picks in the scenes: `"photo": "<k>-<n>"`, or `{"pick": "<k>-<n>", "focus": [x, y]}` (the point kept in
   the frame, 0–1) or `{"pick": …, "fit": "contain"}` (whole picture: portraits, charts). Preview before rendering:
   `python -m news --story stories/<name>.json --pictures <find folder> --stills <out>` and look at `sheet.jpg`
   (needs `sudo apt-get install -y fonts-noto-cjk` and `pip install -r requirements.txt` for budoux; `<find
   folder>`: `git archive origin/renders <name>/find | tar -x -C <dir>`). It also checks the picks against the
   find `index.json` and lists the scenes without a picture. Then set `stage: "render"` and push.
4. The render (~3–6 min) replaces `renders/<name>/` (keeping `find/`): `video.mp4`, `subtitles.srt`,
   `sources.json` and `credits.txt` (picture credits; `credits.txt` is for the video description), `stills/sheet.jpg`, `status.json`. Check the run succeeded and that
   `status.json` has your commit (an old video stays there when a render fails). Look at the stills and the
   subtitles, then give the owner the links
   `https://github.com/maihaianh2911-bit/japan-news-video-factory/blob/renders/<name>/video.mp4` (and the two
   others), and say which scenes have no picture and why.

Owner, 12/11/2026: a video with only a few pictures is not acceptable. Give every scene its own fitting
picture: write 2–3 searches per scene from the start and search again until each scene has one; a text card is
the exception (pure figures), and the owner is told which scenes have none and why. Wikimedia refuses requests from Claude's cloud session (429), which is why
the search runs on GitHub. The voice engine runs only on GitHub (Docker).

## Changing the pipeline
`python3 -m compileall -q news`, `python -m news.custom` on every story, and a stills preview of
`stories/mau-boj.json` (look at the sheet). A push of code to `main` runs the same check on GitHub, offline (no
voice, no live sources; the stills are in the run's Artifacts). The live demo (`--demo`, boj.or.jp + VOICEVOX)
runs only from Run workflow → `demo`. `tools/publish.sh` replaces a folder of `renders` as a whole and writes
`status.json`. Never touch secrets. No pull requests unless asked.
