# japan-news-video-factory — notes for Claude

## The common rules — every channel of this repo (owner, 26/11/2026)
The owner asked for one list of the rules that hold for every channel, went through it in a chat and said "đẩy bản
quy tắc chung của mày thay cho bản cũ đi" (26/11/2026). It replaces the "Iron rules" of 16/11/2026 and "The owner's
rule changes of 19/11/2026", and **it wins over any older sentence in this file or in `AGENT_JNEWS.md`**. The rules
keep the numbers the owner saw in the chat (12b included). Where an older sentence says "iron rule 1, 2, 3", read
common rules 1, 2, 3; "rule change 1 … 6" are common rules 7, 10, 9, 11, 20, 17. What differs from channel to
channel (the length, the hook pattern, the frame, the voice and its speed, the music, the issue title) is not here:
it stands in that channel's own section.

**A. Iron rules**
1. **The video is in Japanese (tiếng Nhật)**: the voice (a Japanese VOICEVOX voice), the script lines, the
   subtitles and the on-screen text. A script in another language is put into Japanese first. Check the language
   of `lines` and the voice before the voice step, and again on the finished video. A video in the wrong language
   is not delivered: fix it and render again.
2. **Vertical (1080×1920), and never under 61 seconds** (owner, 19/11/2026: "chỉ cần trên 61s"; the "60 seconds"
   of the older text is gone). Under 61 s: add true scenes and details of the same story, never padding, and tell
   the owner what was added. Only exception: a trial or sample video — the owner says so, or the issue title or
   notes say `thử`, `mẫu`, `test` or `demo`.
3. **Every video is 61–65 seconds; only the film channel is longer, 2–3 minutes** (owner, 26/11/2026: "trừ phim
   ra, còn lại cho về hết 61-65s"; before, each channel had its own length: `ts` up to 80 s, history up to 138 s).
   A script that runs longer is cut to its main thread and its most gripping details, never delivered long.
4. **A channel's own rules are for that channel only** (owner, 26/11/2026: "Đừng dùng luật của kênh phim vào
   đây"). A new channel that has no rules of its own yet follows these common rules and nothing else; ask the
   owner for the rest, never borrow another channel's rule.

**B. The script**
5. **Nothing is built before the owner approves the script** (owner, 21/11/2026: "đã chốt kịch bản đâu mà dựng").
   A script Claude wrote or changed is shown in the chat; no issue, no story file, no push and no search before a
   clear yes ("ok", "chốt", "dựng đi"). A remark about the script ("cuốn hơn", "61s thôi") asks for a new draft.
   (An issue the owner opens from the form with a script is the go-ahead for that script: unattended, Claude says
   on the issue what it changed.)
6. **A script is shown as one continuous text**: the Japanese in one piece, then its Vietnamese meaning in one
   piece; never cut into numbered scenes or bullet points (owner, 18/11/2026).
7. **A script the owner sends may be improved** (owner, 19/11/2026: "Sửa cả kịch bản tao gửi"): cut, add, rewrite
   so that it is better and more gripping, keeping the owner's story and main idea. Say what was changed.
8. **A story, never an encyclopedia**: told like a storyteller, every sentence a new idea (nothing said twice),
   the sentences linked into one flowing narration. If the story itself is not gripping, say so and propose
   another one instead of sending a dull script.
9. **The telling may be dramatised** (feelings, a narrator's lead-in, suspense, the order of the telling); **an
   event or a quote of a real person is never made up and told as a fact.**
10. **Rumours and unconfirmed details may be told. The narration has no hedging words** (owner, 24–25/11/2026:
    no 「…といいます」「…と噂されています」「…らしい」「…ようです」); **what is unconfirmed is said in the posting
    caption only**, in a ※ note (which part is a rumour, what is known). Asked on 26/11/2026 whether the narration
    should name its source for a grave claim about a living person, the owner said: "ko, ghi vào caption thôi".
    Again on 26/11/2026: "cho phép sử dụng tin đồn, k ép phải đúng 100% sự thật, sẽ ghi ở caption sau" — a rumour
    someone has told (the press, social media, the owner's source video) may be used; Claude only never makes one up
    (rule 9). A narrator's line such as 「長く語り継がれてきました」 is not a hedge and may stay (owner, of the hook
    of `masako-rikon` with 「僕は、皇太子である前に、君の夫だ」: "2 câu đó rất hay"): it adds feeling, not doubt.
11. **The ending is free** (owner, 19/11/2026: "Tự do, miễn hay"), and not the same form on every video. An ending
    that comes back to the opening brings something new; it never reads the opening line again.

**C. The hook**
12. **What the hook says.** The first line is one complete sentence that someone who has never heard of the story
    understands: who, what happened, and the one thing of the story worth remembering (a contrast, a number, or a
    real quote). A name the Japanese audience recognises at once stands in the first line; an unknown name comes
    later. A channel with a hook pattern of its own follows it (the business channel: 「…の生みの親」).
12b. **The hook has no length to aim at: it only has to say the whole idea** (owner, 26/11/2026: "hook chỉ cần
    hết ý là đc"; the "about 44–48 characters" of the earlier text is gone). Only what the screen holds stays:
    the line printed big on the first picture (`"quote": true`) takes at most 4 rows, 56 characters; a longer
    first sentence is split in two lines of the story, the first part the big quote, the rest a normal line, the
    words unchanged. A hook read for more than 5 seconds needs two pictures in the first scene.
13. **The hook is on screen from the very first frame; the first picture moves from the first frame** (`push-in`
    or `punch-in`, never `hold`) **and stays at most 5 seconds.** (Since 26/11/2026 for every channel; it was the
    star channel's rule.)

**D. The pictures** (the detail of 15 and 16, and what the machine watches: "The picture rules of the edit" below)
14. **Real pictures only, never a picture an image generator made up** (ChatGPT and the like). Claude looks at
    every picture itself. A colourised copy of a real black-and-white photograph is a real picture (owner,
    26/11/2026: "ảnh có màu ko tính là ảnh AI"). The narrator characters the owner had drawn (the samurai, the
    Shiba) are the one exception: they present the story.
15. **The first picture is the best of the video**: sharp, the face of the main person clear (or a place or a
    thing the Japanese audience recognises at once), right for the hook line, a photograph (not a newspaper page,
    a document or a collage with text), the face in the upper half of the frame.
16. **Faces**: the whole face stays in the frame while the picture zooms or pans; no text lies over a face; in a
    picture of several people the one spoken of is the clearest; never a picture in which that person's face is
    very small.
17. **Every scene has its own fitting picture; a scene whose words last over 6 seconds has at least two** (about
    6.5 kana a second at speed 1.0); **every picture moves** (no `hold`). A picture with a logo, a watermark or
    burnt-in text, or a small blurred copy, is left out.
18. **The picture library first** (`python tools/library.py`), the searches for what it lacks; a pick that passed
    the review is kept in the library. When no picture passes, search again or tell the owner which scene lacks
    one: a poor picture is never taken just to be done.
19. **The picture review before the render**: every pick is checked against the words spoken while it is on
    screen and against the title and page of its source (the right person, the right event).
20. **The pictures, the footage, the voice and the music of a video the owner sends may be used** (owner,
    19/11/2026). The owner was told the risk (music under copyright is recognised by YouTube; the more of the
    source a video carries, the more it counts as reused content). The engine cannot put a sound of the source
    into a video yet: that needs new code and a trial the owner approves.

**E. Frame, voice, music**
21. **One voice for every channel: 青山龍星** (owner, 26/11/2026: "quay hết về giọng nam cũ của kênh hoàng gia";
    before, the voice could change with the story). No `"speaker"` key in a new story; another voice only in a
    trial the owner asks for. **No channel has a fixed frame, and the look is never a hard rule** (owner,
    26/11/2026: "tao ko muốn có luật cứng như kiểu khung hay full hình… vì luật cứng thì có video phù hợp có
    video ko phù hợp"): the frame, the narrator character, the moves and the cuts are chosen for each video by
    its pictures and its story ("Frame and voice by content"). Where a channel's own rules name a frame (history
    `band`, `ts` `full`), that is where to start, not a must; say in one line which frame and why. One exception the owner made
    (26/11/2026): the imperial-family kind keeps a set of three frames and turns among them (its block in "The
    rules of each kind of video"). Two things
    the engine ties: a narrator character stands only in the `band` frame, and `full` needs tall, sharp pictures.
    The speed of the voice and the music are the channel's own rule.

**F. Checks and delivery — check before the render, render once** (owner, 26/11/2026: a check that comes only
after the render means rendering again, "như thế sẽ mất thêm nhiều hạn mức")

Before the render (no render is spent):
22. **The reading.** `python tools/readings.py stories/<name>.json` (`pip install pyopenjtalk`) prints every line
    as the voice engine's dictionary reads it. Look at names, numbers and kanji with several readings; a wrong
    one is written `{"text": …, "say": "<kana>"}` in the story, and the tool is run again.
23. **The length.** The same tool estimates the voice from that reading and the real speed of the voice (measured
    on 34 videos: 0.5 s off on average, 1.8 s at most), never from the written characters. Aim at an
    estimate of 63–64 s: the tool warns under 63 s and over 65 s (only the film channel is longer, common rule 3).
24. **The pictures.** Rule 19 on the preview (the stills of every scene and `tools/review_picks.py`), and every
    `warning:` of the preview settled (a cut face, text over a face); and no face that is very small.
25. **The caption** is written and checked (`python -m news.captions`) before the render, and pushed with it.

After the render (light):
26. **One overall look at the finished video, start to end, once**: one frame a second on sheets (`ffmpeg -i
    video.mp4 -vf "fps=1,scale=320:-1,tile=6x3" sheet-%02d.jpg`: the moves, the text, the faces), and the
    machine's numbers (the real length over 61 s, the right voice). Not a second and a third viewing. Take the
    one file, not the whole `renders` branch (10 GB): `gh api "repos/maihaianh2911-bit/japan-news-video-factory/
    contents/<name>/video.mp4?ref=renders" -H "Accept: application/vnd.github.raw" > video.mp4` (a file under
    100 MB; `status.json`, `sources.json` and `subtitles.srt` the same way).
27. **Faults found there are gathered, fixed in one push and rendered again once.** A fault of the caption alone:
    push the caption alone (only the caption is published, the video is not made again).
28. **Listening to the video** (`tools/listen.py`) only for the first video in a new voice, or when a name is not
    in the dictionary.

Delivery:
29. **Only the finished video is sent**: the video file and its caption file in the chat, with the links. No
    previews, stills or progress pictures.
30. **Once a week, for each channel**, the owner sends the numbers of 3–5 videos (views, viewed against swiped
    away, average % viewed); Claude writes what got views into that channel's own rules.

## The rules of each kind of video (owner, 26/11/2026: "oke ổn") — one block a kind
Each chat makes one kind: it follows the common rules above and its own block here, and never borrows another
kind's block (common rule 4). In a block, **must** is what the owner said for that kind; **to start from** is a
suggestion, because the look of a video is chosen for that video (common rule 21). These blocks win over any
older sentence about a kind further down in this file.

**The same for every kind**, so that no block repeats it: Japanese; 61–65 seconds, only the film kind 2–3
minutes; the voice 青山龍星 (no `"speaker"` key); **loud: every new story carries `"voice": 2.4`** (owner,
26/11/2026, asked whether the imperial-family and star videos, until then at 1, should come up to the other
kinds: "có, tăng tiếng của mọi video"); the five effects `fx`; the script approved before anything is built; the
checks before the render; the caption. **A story already told is not told again, on any kind** (the same person
may come back, the same story may not). **The list of every video made is `DA-LAM.md`**, at the root of `main`, one
table a kind (owner, 26/11/2026: "xoá hết video cũ đi", and before, of the other repo: "xoá tất cả video đi (t đã lưu
cả rồi), nhưng lưu cái gì lại để khỏi dựng nhầm 1 video 2 lần"): **read it before proposing or accepting a story**,
and tell the owner when the story is already there instead of making it again; **in the push that sets `stage:
"render"`, add the story's line** at the foot of its kind's table (date, Japanese title, the idea in Vietnamese, the
issue, the story's name between backticks; `python -m news.custom` warns of a story at stage render that is not in
the list). The videos on the `renders` branch are deleted once the owner has saved them (all of them on
26/11/2026: Run workflow → "Dọn video cũ" with `keep_days` 0), so a link to an old video no longer works; the story
files stay in `stories/`, and **the picture library stays** (owner, 26/11/2026: "kho ảnh đã đc chọn thì để lại nhé"):
it is on `main` (`stories/media/library/`), and the picks of every reviewed video go into it before its video is
deleted (common rule 18).

| Kind | Issue title (label) | Seal (`kicker`) | `pace`: speed, line pause, scene pause | Music |
| --- | --- | --- | --- | --- |
| 1. Japanese imperial family | `[Tin Nhật]` (`jnews`) | `皇室の物語` | 1.25, 0.05, 0.15 | the owner's flute, 0.7 |
| 2. Stars | `[Tin Nhật]` (`jnews`) | `夫婦の物語`, `家族の物語`, `昭和のスター` | 1.25, 0.05, 0.15 | the owner's flute, 0.7 |
| 3. History | `[Lịch sử]` (`lich-su`) | `戦国の物語`, `江戸の物語` | 1.25, 0.05, 0.15 | gentle piano, 0.7 |
| 4. Hidden rules | `[Luật ngầm]` (`lich-su`) | `日本の掟` | 1.25, 0.05, 0.15 | gentle piano, 0.7 |
| 5. Places | `[Địa danh]` (`lich-su`) | `あの場所の真実` | 1.25, 0.05, 0.15 | gentle piano, 0.7 |
| 6. Biographies (`ts`) | `[TS]` (`ts`) | `人物伝` | 1.3, 0.05, 0.15 | gentle piano, 0.7 |
| 7. Business people, politicians | `[Doanh nhân]` (`doanh-nhan`) | `創業者の物語` | 1.25, 0.05, 0.15 | gentle piano, 0.7 |
| 8. Films and stories | not settled | not settled | not settled | not settled |

- The speed 1.25 is one speed for every kind since 26/11/2026 (the history videos read at 1.08–1.15 before); `ts`
  keeps the owner's 1.3.
- **The owner's flute** (owner, 25/11/2026, after two trials with flute pieces of Commons: "dùng sáo tao gửi này";
  26/11/2026: "cho 2 kênh hoàng gia, kênh nghệ sĩ dùng sáo trúc tao gửi"): the search
  `"music:file:stories/media/music/owner-flute-1-long.mp3"` (the 58.7-second piece
  `stories/media/music/owner-flute-1.mp3` joined three times with 4-second cross-fades, 168 s, so that it never
  jumps where it would loop; credited 提供音源) and `"music": {"pick": "<k>-1", "volume": 0.7}`. No other flute.
- **The gentle piano** (owner, 21/11/2026: "nhạc nền rít quá, cho nhẹ thôi"): `music:Gymnopédie Satie piano`,
  `music:Chopin Nocturne piano`, `music:Debussy Clair de lune piano` at `"volume": 0.7`; no shakuhachi or other
  shrill solo instrument.
- **The issues**: `[Tin Nhật]` issues (label `jnews`) are moved by the workflow and the Claude task
  (`AGENT_JNEWS.md`). The other titles are not: Claude in the chat opens the issue `[<kind>] <Japanese title> —
  <Vietnamese idea>` with the kind's label, comments the links, and sets `jnews-busy` while working, `jnews-done`
  after.

### 1. The Japanese imperial family
- **Must — the subject**: the Japanese imperial family only (owner, 25/11/2026: "Chat này vẫn chỉ làm hoàng gia
  nhật"; before, angry at a story of a singer: "mày làm hoàng gia nhật cơ mà"): 天皇家, 秋篠宮家, the princesses
  who left it, the emperors and empresses of the past; never a foreign royal family (channel 10 of
  `japan-remix-video-factory`) or a star.
- **Must — the frame is one of three, in turn** (owner, 26/11/2026: "hoàng gia nhật, hoàng gia anh vẫn phải có
  luật khung cụ thể, nhưng có thể thay đổi giữa các khung"; the set is Claude's, approved "oke ổn"): `"story"`
  (the old newspaper: a story of the past, old photographs), `"album"` (the family album: love, a couple, a mother
  and child), `"magazine"` (the weekly-magazine page: news of today, a statement, a press conference). Chosen by
  the story; never more than two videos in a row in the same frame. `"full"` and `"band"` are not used here (the
  looks of the biography and history kinds). Of the 39 videos to 26/11/2026, 35 are in `story`, and the videos
  over 100k views were made before `album` and `magazine` existed: with a week of numbers (common rule 30), see
  which frame draws.
- **Must — the music**: the owner's flute (above).
- **To start from**: a story with a love, couple or mother-and-child side leads with it in the first line (owner,
  17/11/2026: `masako-rikon` was the only video with views); one moment a video (a whole life is the `ts` kind's);
  the owner's model script of 24/11/2026 ("When the owner sends an original video").
- The seal: `皇室の物語` (`皇室の話題` for news of the day).

### 2. Stars
- **Must — the subject**: the love and married life of famous Japanese people — Showa stars, actors, singers,
  athletes: couples, a marriage, a loss, a promise kept (the growth plan the owner accepted on 25/11/2026: "Ok từ
  ngày mai hãy cải thiện"; the kind of story that drew views, `masako-rikon`). No beauty tips, backstage gossip
  or gossip lists (another channel, if the owner opens one).
- **Must — the music**: the owner's flute (above).
- **To start from**: the owner's model script (Takeuchi Yuko's widower, in "When the owner sends an original
  video"); what people said on SNS only as a press article reports it; any of the five frames, by the pictures
  (`full` for tall, sharp modern photographs, `album` for a couple or a family looked back on, `magazine` for a
  statement), and when two fit as well, the one the last video did not use; the first picture the most striking
  face of the story, moving from the first frame (with `fx` the engine shows the hook from the very first frame,
  larger when it is short).
- **The growth plan** (25/11/2026, after videos without views; the causes Claude gave: a weak first two seconds, a
  machine voice, one channel mixing every topic, a mass-produced look). Posting is the owner's side: one or two
  videos a day at 19–21 h Japan time, about 20 videos before judging, never delete a video. With the week's
  numbers (common rule 30): 0–50 views a video points at the channel (settings, re-uploads, VPN), a few hundred
  that stop at the videos. The owner refused shorter test videos (25/11/2026, angry: "Sao lại 36s. Video k đc
  dưới 60s cơ mà").
- Its issues carry `[Tin Nhật]` like kind 1 (the workflow knows that title only); the seal tells the two apart.

### 3. History
- **Must**: the first picture is a drama still or a fine photograph, never an old painting (owner, 24/11/2026,
  angry: "cái hook mở đầu quan trọng nhất mà lại để cái tranh cổ rõ xấu"); the gentle piano (above).
- **One battle or one decision a video** (61–65 s since 26/11/2026; the earlier videos ran 63–138 s). A "top 3"
  (`shingen-top3`, `nobunaga-top3`) keeps two sentences an item.
- **To start from**:
  - the `band` frame with a `masthead` (owner, 24/11/2026: "lịch sử dựng dạng này đẹp hơn, vì mình toàn tìm đc ảnh
    ngang"), another frame when the pictures of the video ask for it;
  - **drama stills first** (owner, 24/11/2026: "nên dùng nhiều hình ảnh phim ảnh hơn"): the people of a history
    story are shown mostly by stills of one taiga drama (one face per person for the whole video: Nobunaga = Oguri
    Shun in `豊臣兄弟！`, Yukimura = Sakai Masato in `真田丸`), found through the press galleries of the episode
    (`page:` of a cinematoday / thetv gallery, `web:<drama> <episode> 場面写真`); two or three real pictures (the
    place today, the real portrait) keep it true;
  - the samurai narrator (`"host": {"name": "samurai", …}`, trial approved on 26/11/2026: "Ổn") when it fits the
    video, not on every one;
  - a hook with the name everyone knows and a number or a contrast (「二十七歳の織田信長は、わずか二千の兵で、
    二万五千の大軍を打ち破りました。」).
- The seal by the period of the story: `戦国の物語` / `江戸の物語`.

### 4 and 5. Hidden rules and traditional life; the truth behind places and haunting real photographs
- "Luật ngầm & Đời sống truyền thống Nhật Bản" (seal `日本の掟`) and "Sự thật đằng sau những địa danh & bức ảnh
  thật gây ám ảnh" (seal `あの場所の真実`). One video each so far (`sumo-banzuke`, `nagoro-kakashi`, 21/11/2026,
  in the `history` frame). Still made: that is Claude's reading of the owner's "có" of 26/11/2026; if the owner
  says otherwise, they are paused.
- No rules of their own yet: the common rules and the row of the table. What else they need is asked of the
  owner, never borrowed from another kind (common rule 4).

### 6. Biographies of famous people (`ts`)
- **Must**: the life of one person from childhood to fame (owner, 24/11/2026: "Cho cái này vào 1 kênh riêng nhé,
  đặt tên là tiểu sử nhân vật nổi tiếng đi, viết tắt kênh ts"), with real pictures of every age; a person the
  Japanese audience loves (the format came from a short on Putin's life the owner sent; the owner agreed that a
  loved person fits better than a foreign politician they dislike); **read fast**, `"pace": {"speed": 1.3,
  "line_pause": 0.05, "scene_pause": 0.15}` (owner: "ban nãy đọc nghe rề rà quá, đọc nhanh như mấy thể loại khác";
  1.2 with pauses was too slow); the gentle piano (above).
- **Four or five turns of the life, a sentence each** (61–65 s since 26/11/2026; before: at most about 80 s, the
  owner of the first cut at 133 s: "Bình thường chỉ 80s là cao thôi mà"). The hook says the one contrast of that
  life.
- **To start from**: the `"full"` frame (owner, 24/11/2026: "Làm kiểu để ảnh full màn hình") when the pictures are
  tall and sharp, another frame when they are not.
- First video: `2026-11-24-naruhito-oyamoto` (issue #66).

### 7. Business people and politicians
- **The chat of this kind** (owner, 26/11/2026: "Kênh này sẽ làm về doanh nhân, chính trị gia như tao đã dán ở chat
  khác") makes videos of business people, politicians and the like only. It began with a Vietnamese short the
  owner showed (a presenter at the foot, the pictures above, a big title between them: "Cha đẻ của TĐ Phú
  Cường"). Claude first took the film kind's way of working for it and was corrected (owner: "Không đúng, đấy là
  luật riêng của kênh phim mà. Còn luật của mày tao đã ra đâu. Đừng dùng luật của kênh phim vào đây").
- **Must**, as the owner gave them (26/11/2026: "Kịch bản sẽ do m viết, độ dài thì từ 61-120s, chọn những thứ có độ
  nhận diện cao với khán giả nhật bản"; the length became 61–65 s the same day):
  - **Claude writes the script** (the owner does not send a source): Claude chooses the person and the story,
    checks every fact and quote in press or official sources, and shows the script for approval before anything
    is built.
  - **Subjects the Japanese audience recognises at once**: a person, a company, a brand or a product everyone in
    Japan knows.
  - **61 to 65 seconds, written like the owner's three samples** (owner, 26/11/2026, sending three 36-second
    Vietnamese shorts of the TikTok channel @chadecua — "Cha đẻ của Con Cưng", "… Three O'Clock", "… Tập đoàn Sơn
    Hải": "Học cách viết, nhưng của nó chỉ 36s, của mình phải 61-65s"). The length was "61-120s" at first; the first script (安藤百福, about 107 s, the whole life beat
    by beat) was turned down: "Quá dài dòng, thiếu cuốn hút, k giữ chân đc ng xem, giảm xuống, 65s thôi". How
    those shorts are written (their words were taken down with `tools/listen.py`):
    1. **a must** (owner, 26/11/2026, of a draft that opened on the product instead: "Hook bắt buộc: cha đẻ của
       ...."): the first words are the title, "the father of <brand>" (`<ブランド>の生みの親`), with the one striking thing
       about the brand or the founder in the same sentence ("famous for daring to guarantee its motorways for
       10 years", "owns 10 cafés open day and night in her early thirties");
    2. the founder at once: name, birth year, title, one credential that surprises (a PhD in the USA, captain of
       the champion Robocon team, a former policeman);
    3. the year it began and where it stands today in hard figures (700 shops, 4,000 billion đồng of revenue, a
       flagship at a named place), the contrast of the start and today ("began with less than 1 billion");
    4. one decision or turn in a line (paid the deposit for the shop with no business plan);
    5. one saying of the founder, quoted;
    6. the last line asks the viewer ("What do you think of <brand>?").
    Plain, quick, news-like sentences, each one a fact; the brand everyone knows leads, not the life story. With
    61–65 s instead of 36 there is room for two turns of the story more, told as plainly.
    **Plain does not mean unlinked** (owner, 26/11/2026, of 「…失った男でした。その名は、安藤百福。1910年生まれ、
    日清食品の創業者です。理事長を務めていた信用組合が破綻し…」: "Chuyển đoạn kiểu đéo gì vậy"): every sentence
    follows from the one before (その男, それでも, その庭に, こうして, ところが). The name comes as the answer to the
    hook and leads straight into what the hook promised; no card of facts (birth year, title) dropped between two
    sentences of the story.
  - **The owner's own model for this channel** (26/11/2026: the owner named the subject, "Cha đẻ của đế chế
    Panasonic", cut Claude's draft himself and sent it back: "Viết như này này"). Its order, sentence by sentence:
    "the father of the Panasonic empire was a man who left school in the 4th year" → "his name is Matsushita
    Konosuke" → at 9 sent away to work in Osaka → at 23 started the company on the ground floor of a rented house,
    three people (he, his wife, her brother) → the first product earned only 10 yen in 4 months, the kimono went
    to the pawnshop → just as things got going, the Depression: sales halved, the store full of stock → the
    managers: the only way is to cut half the staff → from his sickbed he decided: nobody dismissed, full pay →
    everyone gave up holidays to sell, the stock was gone in 2 months → his saying, quoted → "that company is
    Panasonic today, 8 trillion yen of sales" → a question to the viewer. **What the owner cut: the teaser after
    the hook** (「しかも、会社がつぶれかけたとき、彼は社員を一人も辞めさせませんでした」): no line that announces
    what comes later; after the hook the name, then the life in order, plain facts with ages and figures. Four
    drafts on 安藤百福 (a whole life in a long narration; a teaser of two mysteries; a card of name, birth year and
    title cut into the story; a hook on the product instead of the founder) were turned down before this one.
  - **Its frame is the samples' one, with a narrator of its own** (owner, 26/11/2026, asked whether the frame
    should be like the samples — a character at the foot, the pictures above, the big title 「…の生みの親」 — or a
    plain one: "Vẽ nhân vật, đưa propmt đây"). So: `band` with `"host"`, the `masthead` carrying the title. Claude
    gave the owner the ChatGPT prompts for a character it proposed (a Shiba dog standing like a man, navy suit, red
    tie, anime style like the samurai; a man in a suit as the alternative): sheet 1 = neutral, talk, point, cross;
    sheet 2 = present, surprised; pure green, waist up, figures apart, no hand above the head. When the owner
    sends the two sheets: `python tools/host_cut.py <name> <sheet1>:neutral,talk,point,cross
    <sheet2>:present,surprised`, look at `sheet.jpg`, then a short trial for the owner before the first video.
  - **How the first video was made** (`2026-11-26-panasonic-konosuke`, issue #85; the owner approved the script
    with "Chốt, cho đẩy" and sent sheet 1 of the character; these are Claude's choices where the owner set nothing,
    kept until the owner says otherwise): issue `[Doanh nhân] <Japanese title> — <Vietnamese idea>` with the label
    `doanh-nhan` (not `jnews`; `jnews-busy` while working, `jnews-done` after, as the `lich-su` kinds); `"style":
    "band"`, `"host": {"name": "shiba", …}`, `"kicker": "創業者の物語"`, `"masthead": "<ブランド>の生みの親"` (the
    check now allows 12 characters: over 9 the title is drawn smaller, 11 characters still stand at about 85 px);
    the default voice 青山龍星 at `"pace": {"speed": 1.25, "line_pause": 0.05, "scene_pause": 0.15}`, `"voice": 2.4`,
    piano at 0.7. **The narrator `shiba`** (a Shiba dog in a navy suit, drawn by ChatGPT from Claude's prompt) has
    four poses so far: `neutral`, `talk`, `point`, `cross`; `present` and `surprised` wait for the owner's second
    sheet, so do not name them in `poses` until `stories/media/host/shiba/` has them.
  - **Length in practice**: 青山龍星 at speed 1.25 reads about 8.8 kana a second, faster than the 6.5 × speed of the
    estimate: a script estimated at 65 s came out at 59.5 s. For 61–65 s write about 540–560 kana (about 470–490
    written characters), and read the real length after the voice step before telling the owner a number. `python tools/readings.py` gives the
    estimate from the reading now (common rule 23).
  - **Check the readings by listening** (second video, `2026-11-27-daiso-yano`, issue #93, 64.4 s): after a render
    run `tools/listen.py <video> ja 13 9` and read it against the script. It caught 暇 read as いとま in
    「値札を付ける暇がありません」; the `say` now writes ひま. Words to write in kana in `say` from the start: 暇,
    質 (しち/しつ), 借家, 夜逃げ, 値札, 銭失い, 度外視, 罵る, numbers with 店 or 億円.
  Not set yet by the owner: the seal (the choice above stands in); the voice is 青山龍星 as on every channel
  (common rule 21). Never borrow another channel's rule.
- **Business people, politicians and the like**: the "father of …" angle of the sample (「ユニクロを作った男」), people the
  Japanese audience knows. Not the whole life from childhood (that is the `ts` channel): one feat, one decision.
- **A politician** (Claude's proposal, approved on 26/11/2026: "oke ổn"): the same hook, with the work everyone
  knows in the place of the brand (「日本列島改造論の生みの親」 for 田中角栄), then the same order: the name, the
  life in order with ages and figures, one decision, a saying, a question to the viewer.
- **To start from** (the look, not a must): the `band` frame with the narrator `shiba` and the title
  「…の生みの親」 as `masthead`, as on the first video above.

### 8. Films and stories — no video made yet
- **The chat of this kind** (owner, 26/11/2026: "Ở chat này mình sẽ chỉ làm riêng nội dung về phim hoặc là chuyện.
  Như tao đã nói, mày chỉ cần để ý đến luật chung và luật riêng của kênh này, còn những luật của kênh khác thì
  không cần quan tâm") makes film and story videos only. The owner named it with the business kind ("Tao định đẻ
  thêm 2 loại nội dung cho video này, 1 loại sẽ dành cho doanh nhân, chính trị gia v...v, 1 loại sẽ là
  phim/truyện").
- **Films and stories = film reviews.** Claude warned that in Japan a video telling a whole film with its footage is
  ファスト映画 (arrests in 2021, 500 million yen of damages) and proposed behind-the-scenes stories instead; the owner
  answered "TikTok vẫn cho làm review phim mà". So reviews are made, in our own words with our own comment (the
  film's dialogue is not read out at length). The angle is a question about a film, the owner's example: "vì sao khi
  xem mộ đom đóm những người cứng rắn nhất cũng sẽ khóc".
- **How a video of this kind is made** (owner: "tao sẽ gửi cho mày một video khá dài khoảng 10 phút, hoặc là
  tao sẽ gửi cho mày một kịch bản dài. Sau đó mày sẽ dựa vào đó để dựng lại một kịch bản mới khoảng 3 phút, 2 đến 3
  phút thôi. Sau đó thì phần hình ảnh thì có thể lấy ở video tao gửi, nhưng mà mình sẽ chỉ làm khoảng 5 giây đầu hook
  là video, còn đoạn sau mình sẽ dùng hình ảnh"): the owner sends a long source (a video of about 10 minutes, or a
  long script); Claude writes a new script of **2–3 minutes** from it, shown in the chat and approved before anything
  is built; **the first about 5 seconds (the hook) are moving footage** from the owner's video, everything after is
  still pictures (frames of the owner's video, `tools/video_frames.py`, and the searches).
- **Length**: 2–3 minutes are the owner's words for the film channel, so up to 180 s here; it is the only kind
  longer than 61–65 s (common rule 3, owner 26/11/2026: "trừ phim ra, còn lại cho về hết 61-65s").
- **To start from**: the `band` frame with a narrator (`"host"`), as the short the owner showed.
- **Not settled yet** (Claude's proposals, the owner has not answered): the seal `映画の裏話`; the issue title
  `[Phim] …`; a narrator character (proposed: a cinema attendant in uniform holding popcorn, drawn by ChatGPT on
  green like the samurai); the speed and the music.
- **What the engine lacks for it**: a clip comes from Commons or from an https address only (`video:` in
  `news/find.py`): the hook clip of the owner's video needs `video:file:stories/media/<story>/<name>.mp4`, to be
  added and tried on the first source video (the owner approves the trial). The words of a source video are read from its burnt-in captions; when it has
  none, `tools/listen.py` takes its speech down (above); only if that fails, ask the owner for the script as text.
- A first script was drafted before the owner described this way of working (火垂るの墓, about 70 s, in the chat of
  26/11/2026, not approved): it is rewritten to 2–3 minutes from the owner's source when it comes.

## Frame and voice by content (owner, 25/11/2026) — for every channel of this repo
Asked whether one frame for every video makes TikTok see "mass-produced content", the owner decided: "M tự đổi
luân phiên, xem nội dung hợp với khung nào thì làm với khung đó, voice thì có thể tùy biến nam nữ ở voicevox, hợp là
đc". (What was explained to the owner: the frame alone is not the main risk; a slideshow of still pictures with a
machine voice and press photos, barely changed, is what gets flagged as unoriginal; TikTok publishes no exact rule.)
- **The frame fits the story: no channel has a fixed frame** (common rule 21, owner 26/11/2026). It is chosen
  for each video by its pictures and its story; when two frames fit as well, take the one the channel's last
  video did not use, so that a channel does not look mass-produced. The five frames to choose from (owner, 25/11/2026: "M có thể tự làm vài khung nữa, t nghĩ
  khoảng 5 khung đổi liên thiên là ổn"; `"album"` and `"magazine"` made that day): `"story"` (old newspaper: Showa
  and old photographs, a story told in the past), `"full"` (the picture fills the screen: tall, sharp modern photos,
  a person's face), `"band"` (blurred picture behind a wide band: landscape press photos and TV stills, history),
  `"album"` (a family photo album: the picture as a print in a white mat on cream paper, the era written under it —
  love, couple, mother-and-child, a life looked back on), `"magazine"` (a clean white weekly-magazine page: the
  picture across the top, a red rule, a bold black headline — today's news, a statement, a controversy, a press
  conference). `"paper"` and `"history"` stay for their own uses. In `album` and `magazine` no text lies on the
  picture (the quote stands under it, like `band`), and no credits are printed (they are in `credits.txt`). The same story may not suit `full` if its pictures are small or wide: then `band` or
  `story`. Say in the issue which frame and why (one line).
- **One voice for every channel: 青山龍星** (owner, 26/11/2026: "quay hết về giọng nam cũ của kênh hoàng gia";
  common rule 21). A new story carries no `"speaker"` key (without it the voice is 青山龍星). What came before, so
  that nobody goes back to it: on 25/11/2026 the owner allowed the voice to change with the story ("voice thì có
  thể tùy biến nam nữ ở voicevox, hợp là đc") and chose もち子さん for the imperial-family and star videos from a
  sampler of 13 voices; on 26/11/2026, after two videos in it: "Giọng đ hay, quay về giọng cũ đi". 冥鳴ひまり and
  No.7 読み聞かせ were turned down too ("ko hay"), and the history videos tried 剣崎雌雄 (at speed 1.15: "đọc nhanh
  hơi bị cướp chữ, nghe nhiều chữ dính vào nhau") and 玄野武宏. None of these is used any more.
- **Another voice is tried only when the owner asks**: the story key `"speaker"` names a VOICEVOX voice,
  `"<name>"` (its ノーマル style) or `"<name>/<style>"`, and a scene may have its own `"speaker"` (a sampler of
  voices). A name the engine does not have stops the voice step with the list of the voices it has: copy the
  exact name from it. When the owner wants voices compared, send an **mp3** (owner, 25/11/2026: "làm file mp3
  trc, chốt voice đã") with the time each voice starts, not a video. The render credits the voice as
  `VOICEVOX:<name>` on screen and in `credits.txt` (VOICEVOX asks for that credit; keep it in the video
  description).
- The speed and the music of each kind: "The rules of each kind of video" above.

## The picture rules of the edit (owner, 19/11/2026: "hook 5s đầu phải là ảnh đẹp, rồi ảnh k bị mất mặt") — approved one by one
Each rule is a question a look at the picture answers with yes or no. A picture that fails one is not used as it
is: frame it again, pick another, or search again.

**The first picture (the hook, about the first 5 seconds)** — owner, 21/11/2026: "quá dài rồi, chỉ nên để 3 dòng
thôi, ảnh hook đầu không quá 5s"; changed on 25/11/2026, after the three videos of the channel with over 100k views
turned out to have hooks of 44–48 characters on 4 rows: "Cho phép kể hết ý chứ k ép xuống 3 dòng". The hook line
printed big (`"quote": true`) tells the whole idea: **at most 4 rows, so at most 56 characters**; a still longer
first sentence is split in two lines of the story, the first part the quote, the rest a normal line (the words stay
the same, also for a script the owner says to keep unchanged); and **the first picture
stays at most 5 seconds** (with `fx` the engine cuts to the scene's next picture after 5 s, so a first scene read
longer than that needs a second picture). `python -m news.custom` prints a `warning:` for both: settle it.
1. It is the best picture of the whole video: sharp, bright, not blurred, not grainy.
2. It shows the face of the main person clearly, or a place or a thing the Japanese audience recognises at once.
3. It matches the hook line: the right person, the story being told.
4. It is a photograph: not a newspaper page, a document, a collage with text or a picture with a logo.
5. The face is in the upper half of the frame, clear of the hook line printed on the foot of the picture.

**Faces (every scene)**
6. The whole face, forehead to chin, stays inside the frame for as long as the picture is shown, while it zooms or
   pans too.
7. The text on the picture (the headline of the scene, a quote, the captions) does not lie over a face.
8. In a picture of several people, the one being spoken of is the clearest; if not, frame that person or change
   the picture.
9. A scene about one person does not use a picture in which that person's face is very small.

**Every picture**
10. When no picture passes, search again (`web:`, `page:`, the owner's video); if there is still none, tell the
    owner which scene lacks one. A poor picture is never taken just to be done.

The owner turned down two more that were proposed, so they are **not** rules: "a picture is used only once in a
video, and two near-identical pictures are not put side by side", and "the last picture must be a fine one too".
A picture may be used again where it fits.

**What the machine watches** (the preview `python -m news --story … --stills …` prints a `warning:` for each; settle
every one before the render): the first picture under 900 px on one side (under 640 px when `"fx": enhance`
enlarges it), looking soft (its sharpness under 12), or shown whole / marked flat (rules 1 and 4). **The picture
search says how crisp every found picture is** (26/11/2026): `"sharp"` in `index.json` and `s27` on the contact
sheet, about 5 (soft, blurred) to 60 and more (crisp, full of detail), under 12 soft; it counts edges, so a plain
studio portrait scores lower than a crowd: a hint to open the picture in full size, not a verdict. Then a face cut by the frame or leaving it during the move, with the `"focus"` that keeps it when there is one
(rule 6); a face under the headline or the hook line, or in the lower half of the first picture (rules 5 and 7).
The faces are found by `news/faces.py` (YuNet of OpenCV Zoo, the model is `news/face_yunet.onnx`); it needs
`pip install opencv-python-headless numpy`, and without it the preview says `note: faces not checked`: then look
at every face yourself. The machine does not see rules 2, 3, 8 and 9: those are for your eyes, at the review.

## The frames and tools of the new kinds of content (owner, 20–26/11/2026)
What each kind makes and must keep is in "The rules of each kind of video" above; this section describes the
frames, the narrator, the clips and the tools they use.
The owner makes more channels with this engine, in this repo (owner, 20/11/2026: "dựng trong repo này luôn"; the
code went to `main` on 21/11/2026: "cho lên nhánh chính luôn đi"). They differ from the imperial-family and star
videos by their frame and by the name in the seal:
- `"style": "history"`: a dark ink page; the picture (1080×1480, from the top of the frame) melts into the page at
  its foot, the `kicker` stands in a vermilion seal written downwards (keep it to 4–7 characters), the scene's
  `era` in gold at the top right, the headline on the melting foot, ivory captions on the dark page. The video
  comes out of black and goes back into it. The owner approved the look on the first trial (`otani-yoshitsugu`).
- `"style": "full"` (owner, 21/11/2026: "để ảnh full màn hình… không cần khoảng tối… để chữ ở giữa màn hình…
  đến ảnh rồi chữ chạy theo", approved on a 9-second trial; first video `uchida-yuki`): the picture fills the whole
  frame, nothing dark laid over it; the scene's `era` (else the `kicker`) in a red tag at the top left; the headline
  and a quote in white with a dark outline in the middle of the frame, a little under its centre, coming in row by
  row after the picture; the captions in pale gold under them, appearing only as the voice reads them. A quote that
  opens a scene stays there as the scene's headline while its next lines are spoken (a list video: the quote
  `"1. …"` opens each scene). Pick tall pictures at least about 1200 px high (a wide or small one is enlarged a
  lot and looks soft); every face stays above three fifths of the frame (the preview warns). No credits are printed
  on the picture (owner, 24/11/2026, of the small lines at the foot: "m ghi những cái gì ở góc cuối màn hình vậy"):
  the source, the voice (VOICEVOX:青山龍星), the music and the pictures are all in `credits.txt`, which the owner
  pastes in the video's description; say so when giving the links.
- `"style": "band"` — **the frame the history videos start from since 24/11/2026** (where to start, not a must,
  since 26/11/2026: common rule 21; owner, showing a short he liked:
  "lịch sử dựng dạng này đẹp hơn, vì mình toàn tìm đc ảnh ngang"; approved on a 30-second trial: "Dựng đi"): the
  scene's own picture, blurred and dark, fills the frame; at the top the `kicker` small between two gold rules and
  the story's `"masthead"` (a big title of at most 9 characters, e.g. `本能寺の変`) with a small red diamond under it;
  the scene's `era` in gold on the right above the picture; the picture in a wide band across the middle (1080×780,
  between two thin gold lines) — landscape pictures and drama stills fit it whole, a portrait or a scroll is shown
  `"fit": "contain"`; the headline in white and the pale gold captions under the band; the hook quote big and white
  under the band. No text lies on the picture, so a face is never under text; the rule left is that the face stays
  inside the band during the move. First video: `nobunaga-honnoji` (version 3).
- **The narrator ("host")** (owner, 26/11/2026, from a short he liked: "kiểu có 1 con nhân vật ở dưới, còn hình chạy
  ở trên"; trial approved: "Ổn"): a story in the `band` frame may carry `"host": {"name": "samurai", "poses": [one
  per scene]}`. The picture band moves up and becomes 16:9 (1080×608 from y 410), the headline and captions sit under
  it, and the narrator stands at the foot (640 px high, waist up): the scene's gesture for its first 2.2 s, then the
  calm pose with the mouth opening and closing while the voice speaks, a light sway. Poses: `neutral`, `talk` (the
  same with the mouth open), `point`, `cross`, `present`, `surprised`. The character was drawn by ChatGPT for the
  owner (an adult samurai in red and black armour, crescent helmet); `tools/host_cut.py` cut the six poses out of
  the green sheets into `stories/media/host/samurai/`. A new narrator: draw the same six poses on pure green, waist
  up, then `python tools/host_cut.py <name> <sheet>:<pose>,… …`. First video: `2026-11-26-hideyoshi`.
- **Every picture moves** (owner, 24/11/2026: "nhớ phải luôn cho ảnh chuyển động"): no `hold`; a tall picture in the
  band gets `push-in` with its `focus` on the face (a `rise` starts at its foot, with the face out of the band).
  Vary the cuts between scenes (`slide`, `zoom`, `flash`, `dip`, `hard`; owner: "có thể thêm hiệu ứng chuyển cảnh").
- **Clips** (owner: "có thể dùng video (đoạn ngắn)"): a search `video:<words>` finds videos on Wikimedia Commons
  with a free licence (or `video:<address of one video file>`), keeps up to 3 of them as `<k>-<n>.mp4` (30 s at
  most, no sound) and lays six moments of each on `sheet_<k>.jpg` with their time. A picture entry picks one like
  a picture, with `"start"` (seconds into the kept clip) and `"seconds"` (how long, 6 by default):
  `{"pick": "34-1", "start": 0.5, "seconds": 4, "tone": "sepia"}`. The clip plays at its own speed (slowed when
  shorter than its place) and closes in a little; `focus` says which part of it fills the frame. Commons has few
  clips that fit a story (tried on five stories: one or two each); the owner's own videos are the better source.
- `"cut": "flash"`: a burst of pale light on the cut (a blow, a betrayal, the turn of the story).
- `"voice": 2.4` (owner, 21/11/2026: "tăng voice to thêm 70%" → 1.7; 24/11/2026: "tăng voice to hơn 40%" → 2.4):
  how loud the finished sound is, 1 = the usual -16 LUFS (1.7 ≈ -12 LUFS, 2.4 ≈ -9 LUFS with a quicker limiter).
  The music does not come up with it. **Every new video of every kind carries `"voice": 2.4`** (owner, 26/11/2026: "có, tăng tiếng của
  mọi video"; until then the imperial-family and star videos were at 1).
- **Music**: the gentle piano or the owner's flute, by the kind ("The rules of each kind of video").
- **Nothing is built before the owner approves the script** (owner, 21/11/2026, angry that the picture search
  of `shingen-furinkazan` was started right after a rewrite was shown: "đã chốt kịch bản đâu mà dựng"). When the
  script is rewritten or its length changed, show it in the chat and wait for a clear yes (「ok」「dựng đi」「chốt」);
  no issue, no story file, no push and no search before that. An instruction about the script ("cuốn hơn",
  "61s thôi") is a request for a new draft, not a go-ahead.
- **The picture library** (owner, 22/11/2026: "Các lần tìm t thấy đc rất nhiều ảnh luôn, tại sao k lưu những ảnh
  đẹp nhất lại, lần sau chỉ cần quét trong kho là có sẵn"): every picture that passed the review of a video is kept
  in `stories/media/library/<subject>/` (one folder for a person, a couple, a family, a place or an event:
  `masako`, `naruhito`, `naruhito-masako`, `imperial-family`, `aiko`, `kumamoto-2026` …), with `<name>.credit.txt`
  and a line in the folder's `README.md` saying in Vietnamese what it shows; `stories/media/library/README.md`
  lists the subjects. **Before writing the searches of a new video**, run `python tools/library.py list` and
  `python tools/library.py sheet <subject>` for the people, places and events of the story, look at the sheets, and
  add a search `file:stories/media/library/<subject>/<name>.jpg` for every picture that fits (it is credited to its
  first source); search the web only for what the library lacks or to find better. **After the review passes**,
  keep the picks: `python tools/library.py add <find folder> <pick>=<subject>/<name>#<what it shows> …` (the same
  picture is never kept twice; names in lower-case ASCII, a year first when it carries the moment), and push them
  with the story.
- **The `renders` branch is heavy** (26/11/2026): its first `git fetch --depth 1` in a fresh session downloads about
  10 GB and takes about 10 minutes; start it in the background as soon as a story is pushed, and never run two
  fetches at once (the second fails on `shallow.lock`). A find stage with 22 `web:` searches took 13 minutes.
- **Hearing a video without captions** (26/11/2026): the cloud session can take down speech after all.
  `pip install sherpa-onnx numpy`, then `python tools/listen.py <video> [ja|vi|en] [window] [step]` (Whisper
  large-v3-turbo, fetched from a GitHub release, 560 MB; Hugging Face is refused by the network, GitHub is not).
  Over loud music a window can come back as a made-up line: run it twice (windows 20/15 and 13/9) and join.
- Before a render, check every pick against the title and page of its source in `index.json`, not only by eye: on
  the first videos a portrait found by `wiki:` was another man of the same battle, a print was another scene, and a
  web portrait came from the page of the shogun before (`tools/review_picks.py` prints the source beside each).

The owner is Vietnamese and not technical: answer in short, simple Vietnamese, no jargon. They write "tao" (I) and
"mày" (you); answer the same way, "tao" for yourself and "mày" for them. Their standing decisions
are in `maihaianh2911-bit/japan-video-factory` → `docs/HANDOVER.md` (real pictures only, Claude looks at every
picture, quality is not traded for usage; a script the owner sends was translated faithfully and never cut or
rewritten until 19/11/2026: it may now be improved, common rule 7).

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
2. Add `jnews-busy` to the issue right after creating it (the workflow wakes the Claude task at the same time; the
   label keeps it off this issue), then do the steps of `AGENT_JNEWS.md` for that issue right away. Keep
   `jnews-busy` on while you work and wait in the chat: for an issue with a fresh `jnews-busy` (added less than
   2 hours ago) the workflow does not call the Claude task after a machine step and does not write "chưa gọi được
   Claude" on the issue. On a longer chat remove and add it again; remove it after the closing comment. While a
   machine step runs, say so in one line and wait; if the owner does not want to wait, stop right after one of
   your pushes (once the workflow has moved the step label, see "Claim" in `AGENT_JNEWS.md` §0) and remove
   `jnews-busy`: the Claude task continues from the labels when GitHub calls it after that step.
3. Give the owner the links to the video, the subtitles and `credits.txt`.

## When the owner sends an original video (every morning since 14/11/2026)
A scheduled task reminds the owner at about 8:00 (Vietnam time) to send the day's source video (someone else's
short). Its words are the content; our video retells it in our own words and frame (owner, 16/11/2026: "chỉnh
sửa nhẹ kịch bản, giữ khung nội dung nhưng làm cho hay hơn, cuốn hơn, có thể thêm bớt; đọc nhanh như video gốc;
kèm caption cho mỗi video"):
1. Read every caption burnt into the video: `ffmpeg -i <video> -vf "fps=1,crop=1080:500:0:700,scale=540:-1,
   drawtext=text='%{pts\:hms}':x=5:y=5:fontcolor=yellow:fontsize=24,tile=3x10" cap%02d.jpg` (move the crop to
   where the captions are) and look at the sheets. The narration starts at 0 s, so an opening title is spoken
   too.
2. Rewrite it in Japanese, lightly: the same story and facts in the same order of scenes, but our own sentences,
   more gripping. Open with one hook line printed big (`"quote": true`, e.g. 「夫の葬儀にさえ、参列を許されなかった
   妃がいる。」), keep the rhythm tight, end with a line that stays. You may cut repetition and add a few true,
   well-known details on the same subject (dates, ages, what became of a person); never make up an event or a
   quote of a real person and tell it as a fact (the telling may be dramatised, and a rumour is told plainly, its ※ note in the
   caption: common rules 9 and 10). Keep the quotes of the people as they are. Read it fast like the source:
   the pace of the kind (the table of "The rules of each kind of video": 1.25, 0.05, 0.15); estimate the length with `tools/readings.py` (common rule 23), not at about 6.5 kana-reading
   characters a second at speed 1.0 plus the pauses (common rules 2 and 3: 61–65 s). Tell the owner in the chat what you
   added. Example: `stories/2026-11-16-nobuko.json` and the four other stories of 16/11.
   How to write it (owner, 17/11/2026, after finding the scripts of that morning dull):
   - **The first line is the hook of common rules 12 and 12b** (one complete sentence a stranger understands:
     who, what happened, the one thing worth remembering; no length to aim at), so that the viewer
     remembers it and stays: 「離婚を申し出た雅子さまに、皇太子さまが返した答えは、『僕は、皇太子である前に、君の夫だ』。
     この話は、二人の愛の証として、長く語り継がれてきました。」, 「愛子さまは、母である皇后雅子さまと同じように、とても
     優しい方です。それがよく伝わるのが、…ある午餐会での出来事です。」 Then tell the story. The ending is free (owner,
     19/11/2026: "Tự do, miễn hay"; before: back to the opening, never a question): the line that ends this story
     best, by a new fact or turn, never by saying the opening again.
   - **A story, never an encyclopedia** (owner, 20/11/2026: "đừng viết như wikipedia… kịch bản mà không cuốn thì
     đừng viết còn hơn"). Tell it like a storyteller: a person, a moment, what they felt, what happened next, the
     turn. Every sentence pulls the viewer to the next one (tension, a question left open, a surprise). A date or a
     place only where it carries the drama (an age, a birthday, "25 years later"), a few in a whole script, never
     one per sentence; no report wording (「…でのことです」「医師の診断は…」「…と発表しました」「…と語られました」 as a
     list of events). Before showing a script, read it as a viewer scrolling past: if a sentence sounds like an
     encyclopedia entry, rewrite it; if the story itself is not gripping, say so and propose another story
     instead of sending a dull script.
   - **Every sentence says something new** (owner, 19/11/2026: "mỗi câu đều phải có ý nghĩa, không lặp đi lặp lại").
     No sentence repeats an idea already said: the body does not tell the hook again, the end does not sum up the
     hook, no filler such as 「だからこそ…わかったのでしょう」 or a line that only restates feelings. Before showing a
     script, read it sentence by sentence and cut or replace every sentence that adds no new fact or turn; if the
     script then falls under 61 s, add new true facts of the same story, never repetition.
   - **One flowing narration**: sentences linked by connectives (けれど, そんなある深夜, その言葉が本物だったことを…),
     the warm narrator's です/ます, no chopped fragments such as 「1993年。ハーバード、東大。」 or 「1993年6月、二人は結婚。」.
     **Show the owner a script the same way: one continuous text** (the Japanese in one piece, then its Vietnamese
     meaning in one piece), never cut into numbered scenes or bullet points (owner, 18/11/2026: "Kịch bản phải
     liền mạch, nói bao nhiêu lần rồi, đừng bao giờ chia đoạn ra như thế"). The scenes exist only for the pictures.
   - A story the sources do not confirm is told plainly, without hedging words; what is unconfirmed is said in
     the ※ note of the caption (common rule 10; until 24/11/2026 it was framed once in the narration).
   - Under 61 seconds: add scenes and feelings of the same story, never encyclopedic padding (number of trees,
     treaty years). Do not end every video with 「あなたはどう感じますか？」.
   - A source video too thin for a story (a few captions, no events): tell the owner before making it.
   - Owner, 17/11/2026: the love story (`masako-rikon`: a request for divorce, his answer, the proof, the two
     side by side in 2019) was the only video with views. When a source story has a love, couple or
     mother-and-child side, lead with it in the first line and build the story on it (true facts only). This is
     the rule of the imperial-family and star chats, not a common one (owner, 26/11/2026).
   - **The owner's model script** (24/11/2026, "học tập cách viết này", for the scripts Claude writes on its own
     as for the rest; it was about Takeuchi Yuko's widower): (1) the hook gives the time since the event, the
     person and the striking fact ("6 years since Takeuchi Yuko died, her husband Nakabayashi Taiki has not
     remarried"); (2) a teaser of something still going on that moves people ("what he keeps doing, as if keeping
     a promise to his wife, brings people to tears"); (3) the name again and the event in one plain line; (4) the
     decision or turn; (5) what people said on SNS, quoted in 「」 — only comments a press article reports, never
     made up; (6) a line that raises the stakes ("and his life after that refusal touched people even more"), then
     the payoff details. Short plain sentences, news-like but warm, about 65 seconds (owner, 24/11/2026: "video
     sau cũng chỉ làm 65s thôi"; `"pace": {"speed": 1.25, "line_pause": 0.05, "scene_pause": 0.15}`).
   Examples: `stories/2026-11-17-masako-rikon.json`, `stories/2026-11-17-aiko-kenya.json`.
3. Then as "When the owner pastes a script" above (the issue body holds the source words, the notes say they were
   rewritten), with the frame that fits the story and the voice 青山龍星 ("Frame and voice by content", 25/11/2026; `"story"` was used for every source video from 15/11 to 24/11) and a fitting `kicker` (e.g. `皇室の物語`
   for a story about the imperial family), a `wiki:` search for every person and place of the story, then `web:`
   searches (2–3 per scene, Japanese words; with a wish ` => …` where it helps), 2 pictures for a scene over
   6 seconds of words (1 is enough under that, common rule 17).
   **The pictures and the footage of a video the owner sends may be used, its voice and music too** (owner, 16/11/2026: "lấy cái nào
   đẹp"; 19/11/2026, for every repo: "nếu repo nào đc dựng bằng cách remix video hoặc tao có gửi video, có thể
   sử dụng hình ảnh/video trong video tao gửi"). The owner's video is a picture source like the searches:
   `python tools/video_frames.py <video> <story>` lays out one frame of every shot on a numbered sheet (look at
   it), `… --keep 3,7 [--crop x,y,w,h]` saves the chosen ones as `stories/media/<story>/v-<m>m<ss>s.jpg` and
   prints the `file:` searches to append (credited 元動画). Pick clean moments: a frame with the source's caption,
   logo or watermark over the picture is cropped clean (`--crop` also cuts an inset picture out of its blurred
   background) or left. Prefer a web copy of the same picture when it is larger. Moving footage (a clip inside a
   scene) is allowed by the owner too, but the frames of this engine show still pictures only: a clip needs new
   frame code and a trial the owner approves first; until then take stills. The source's voice and music are
   allowed since 19/11/2026 as well (common rule 20: the risk was told, and the engine cannot do it yet).
   Names the voice may misread get a `say` in kana.
4. Write the posting caption (every video has one, owner 16/11/2026), see "Posting caption" below. Push it with
   the story.
5. Send the owner the finished video file and its caption file in the chat (they want them there, not only as
   links) and the links. Send only the finished videos: no previews, stills or progress pictures (owner,
   18/11/2026: "gửi video cuối cùng đã xong thôi, không cần gửi nhiều").

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
     font, up to 3 lines), `lines` (a list: the script, in Japanese, sentence by sentence — the
     owner's script as improved, common rule 7), optional `value` (a big figure such as `0.5％`) and `evidence` (small text).
     Where they appear: on a picture scene, headline, then value, then evidence under each other below the picture
     (evidence only if it fits above the captions — the preview prints a warning when it does not); on a text card
     (no picture), headline, value, then evidence. A card shows nothing else: no title, so give a text card an
     `evidence` or a `value`. A line the voice may misread is written `{"text": "caption", "say": "reading in kana"}`.
   - Optional `style`: `"news"` (dark blue, default) or `"paper"` (pale yellow old newspaper, serif type), and
     `kicker`: the red tag at the top (default `日本のニュース`; e.g. `皇室の物語` for a story that is not news).
   - `"style": "story"` (trial of 15/11/2026, the owner compares it with `paper`): the old-newspaper page for a
     story told in pictures: the picture fills most of the page, the scene's `era` (`"1921年"`, `"昭和初期"`)
     stands at the top instead of the date, the headline lies on the foot of the picture, the captions are printed
     on the page. Also usable in any frame: a line `{"text": …, "quote": true}` is printed big on the foot of the
     picture, over a soft dark band, while it is spoken (instead of the caption); the faces above stay bright
     (owner, 17/11/2026, and again on 18/11/2026 against printing it on the paper under the picture: "kiểu này thì
     hợp lí hơn" about `masako-rikon`). Never darken the whole picture; a picture `"tone": "sepia"` / `"mono"` / `"color"`
     (sepia for the old years, colour as the story reaches today); `"music": {"pick": "<k>-<n>", "volume": 1}`
     from a search `music:<words>` (recordings on Wikimedia Commons with a free licence, e.g. `music:Gymnopédie
     Satie piano`; index.json gives title, `seconds` and licence; the piece loops, fades in and out, about 17 dB
     under the voice, credited on screen and in credits.txt); `"pace": {"speed": 0.92, "line_pause": 0.35,
     "scene_pause": 0.5}` (slower voice, silence after each line, more around a quote and at the end of a scene).
   - `"fx": {"motion": true, "depth": true, "text": true, "face": true, "enhance": true}`: the picture effects.
     **The owner switched the first four on for this channel on 17/11/2026 and the fifth on 26/11/2026 ("đẩy công
     cụ lên luôn, cho vào bước phù hợp"): every new story carries this line with all five**; stories made before
     are not changed (a story without `fx` renders exactly as before). What each one does:
     - `enhance` (`news/enhance.py`): before a picked picture goes into the frame, in the preview as in the
       render, a dull one gets its light back (a light stretch, the colours kept) and a small one (shorter side
       under 1100 px) is enlarged by Real-ESRGAN, mixed 60/40 with the plain enlargement so that skin keeps its
       grain (the model alone looked painted on faces). 5–7 seconds a small picture, about 40 seconds a video.
       The model is in the repository (`news/upscale_x4.onnx`, BSD 3-Clause); it needs numpy and onnxruntime, as
       `depth` does, and without them the run log says `warning: enhance effect off` and the picture is enlarged
       the plain way. A picture that must stay as it is gets `"enhance": false` in its picture entry. **It does
       not save a poor picture**: one that is blurred or under about 640 px is still changed for a better one;
     - `motion`: the camera has a light rhythm, a little quicker at first, and keeps moving to the end of the
       picture (owner, 19/11/2026: "nhiều ảnh trông như không chuyển động gì": the moves are now 25–45 % for
       `push-in`/`pull-back`, `close-up` keeps closing in, `hold` drifts; no picture may look still);
     - `depth`: a picture that fills the frame gets a light depth (things near the camera move a little more
       than things far away; a depth map by Depth Anything V2 Small, about a second a picture). A **flat picture
       (a document, a newspaper page, a collage, a chart, a screenshot) gets `"depth": false`** in its picture
       entry (`{"pick": "3-2", "depth": false}`): on it the depth map is wrong and the picture would bend. A
       picture with `"fit": "contain"` never gets it;
     - `text`: the tag, the headline and a quote come in piece by piece, and the caption is there from the start,
       paler, and darkens from left to right as the voice reads it — at the real moment of each character (the
       lengths of the sounds VOICEVOX gives: exact at every pause and for kana, kanji share the sounds of their
       phrase), and each caption starts when the voice reaches it;
     - `face`: the large text (headline, quote, year, captions) is set in Shippori Mincho B1 ExtraBold (SIL Open
       Font License; the workflow fetches it into `fonts/`, not kept in the repository).
     `motion` and `depth` act on pictures that carry a `move` (step 3), so give every picture one. On GitHub the
     render of a story with `fx` installs what the effects need (`.github/workflows/news-video.yml`, step "Hiệu
     ứng hình"); if that fails the video is still made, with flat pictures or the usual typeface, and the run log
     says `warning: depth effect off` or `warning: display font … not found`: say so in the closing comment. To
     preview with the effects here: `pip install numpy opencv-python-headless onnxruntime`, the typeface in
     `fonts/ShipporiMinchoB1-ExtraBold.ttf` (or `NEWS_DISPLAY_FONT=<file>`); the depth model is downloaded on
     first use (99 MB, or `DEPTH_MODEL=<file>`).
   - `searches`: Wikimedia Commons searches, numbered from 1 in order (English works best; `incategory:"…"` for a
     person, building or place). A search `web:<words>` is a free web image search
     (Yahoo! JAPAN, else Bing, else DuckDuckGo; Japanese words work; stock sites with watermarks are left out) and `url:<picture> [<page>]`
     takes one picture (`file:stories/media/…` a picture kept in the repository); their licence is unknown and the site is credited. Only append to the list later: the picks use the numbers, and a pick whose search
     text changed is refused.
   - **Wider search (owner, 19/11/2026: "có cách nào để tìm hình ảnh mở rộng ra ko" → all three):**
     - `web:` looks further: three result pages of Yahoo! JAPAN (about 55 candidates, 20 before), **20 pictures
       kept** (12 before; with a wish, the best 20 of 45). A picture its own site will not give (hotlink refused, a
       page instead of a picture) is taken from the search engine's own full-size copy, still credited to its
       site; a picture the engine says is under 400 px is not even loaded.
     - `page:<address of one article>`: **the pictures that article shows** (up to 20): the page's own picture
       first, then the pictures in the order of the page, each in its largest version, without the page's header,
       footer, menus, side columns and furniture. `"page:https://www.jprime.jp/articles/-/30126"`. For a press
       article or a photo page found by a `web:` search (the `page` of a result in `index.json`) that has more
       pictures of the same event. Credited to the site, licence unknown, as `web:`. A page the site refuses is
       `"unusable"`. Tried on eight press sites on GitHub: between 2 and 20 pictures a page.
     - `jps:<Japanese words>`: **Japan Search** (jpsearch.go.jp), the shared catalogue of Japan's archives,
       libraries and museums (the National Diet Library, city libraries and archives, university collections, the
       cultural-heritage sites): old prints, paintings, photographs, objects, the records catalogued as pictures
       first. Only records with a picture and rights that allow use (public domain, CC0, CC BY, CC BY-SA), up to
       12, credited to the holding site with the licence. `"jps:関東大震災"`, `"jps:土偶"`, `"jps:紫禁城"`. **Search a
       thing, a place or an event, not a person**: a name brings mostly books about that person, whose cover scans
       are left out. For history before about 1950. **A modest source**: tried on GitHub (19/11/2026), of six
       searches two brought 12 pictures (`関東大震災`, `土偶`), two brought 1–2 (`富士山 浮世絵`, `紫禁城`) and two
       names of people none (`西太后`, `明治天皇`). The pictures of ColBase (the national museums) and of the Tokyo
       museums cannot be loaded at present (their addresses in the catalogue answer 404 and 403; the ColBase
       pages are built by script), so those records are passed over. Use it beside `wiki:` and `web:`, not instead.
     A wish ` => …` works on `page:` and `jps:` as on `web:`.
   - Two more kinds of search (17/11/2026, `news/find.py`; the owner found the videos short of fitting pictures):
     - `wiki:<name or Wikidata item>`: every picture **about one thing** (a person, a place, a building, an
       event), through its Wikidata item: the item's own pictures, the pictures of its Japanese and English
       Wikipedia articles, its Commons category, photos taken at its coordinates. Up to 24, the most to the point
       first, free licences with author and licence for `credits.txt`. `"wiki:美空ひばり"`, `"wiki:日本銀行"`; the name
       is the title of its Wikipedia article (Japanese or English), or the item itself (`"wiki:Q17"`) when a name
       fits several things. `index.json` says which item was found (`"wikidata"`: id, label, description, `coord`):
       check it is the right one. **Write one `wiki:` search for every person and place of a story, before the
       `web:` searches.**
     - `geo:<lat>,<lon> <metres>`: Commons photos taken around a point, nearest first, whatever they are called
       (up to 12; 500 m when no distance is given): `"geo:35.6852,139.7528 400"`. The coordinates of a `wiki:`
       item are in `index.json`.
   - A wish (17/11/2026): ` => <what the picture must show, in English>` at the end of a `wiki:`, `geo:`, Commons
     or `web:` search, e.g. `"web:美空ひばり 東京ドーム 1988 => a woman singing on a large stage in a feathered dress"`,
     `"Tokyo residential houses => rows of small houses in a Japanese neighbourhood"`. The machine then looks at
     more pictures than it keeps (Commons 50, web 45, `wiki:` 60), scores each against the wish (CLIP) and keeps
     the best, best first (8, web 20, `wiki:` 24); pictures that do not show the wish (score under 0.18) or look
     unsuitable are left out, so a group can come back small or empty: then ask with other words. The score is
     `match` in `index.json` and `~0.31` on the contact sheet (about 0.30 and more: it shows the thing; near 0.20:
     doubtful). The wish is always English (CLIP does not read Japanese; `news.custom` refuses another script);
     the search words before it stay Japanese for `web:`. Use a wish when a search brings many pictures of the
     wrong moment or thing; a search without a wish keeps the order of its source, as before. When the ranking
     could not be installed on GitHub, the wish is ignored (`"ranked": false` in `index.json`). The wish is part
     of the search text: never add one to a search that was already run (append a new search instead).
   - Check before pushing: `python -m news.custom stories/<name>.json` lists every problem (unknown keys such as
     `photos`, `lines` not a list, bad `focus`/`fit`, missing fields) and the scenes without a picture.
2. The push runs the workflow (find stage, ~2 min). First check that the run for your commit succeeded (the
   session's GitHub tools `actions_list` / `actions_get`); then `git fetch --depth 1 origin +refs/heads/renders:refs/remotes/origin/renders` and check that
   `<name>/find/status.json` has your commit (`commit`) before trusting the folder. Look at
   `<name>/find/sheet_<k>.jpg` yourself. A search with no usable picture has no `sheet_<k>.jpg` (0 results in
   `index.json`). Two things can go wrong with a search, and they are not handled the same (19/11/2026):
   - **Its source did not answer** (network, Wikimedia refusing, no web search engine answering): `"error"` in
     `index.json`, the run is red and `status.json` says `"outcome": "partial"` — run it again (re-run the job, or
     Run workflow → `story` + the name) and only the failed searches are tried again.
   - **It cannot work as written**: a `wiki:` name that names nothing, a `url:` picture the site refuses (403,
     404), that is too small (under 400 px), is not a picture, or did not load in two tries. It has `"unusable"`
     (the reason) in `index.json`, is **never tried again**, and the run stays **green** (the issue comment and
     the run's summary name it): running the find again changes nothing. Append another search instead: the exact
     title of the Wikipedia article or the item `Q…`, a `web:` search, another address of the picture.
   A `url:` picture that another search already found is kept all the same (`"same_as": "<k>-<n>"` names the pick
   it repeats): they are the same picture. If a scene has no fitting picture, append searches
   and push again.
3. Put the picks in the scenes: `"photo": "<k>-<n>"`, or `{"pick": "<k>-<n>", "focus": [x, y]}` (the point kept in
   the frame, 0–1) or `{"pick": …, "fit": "contain"}` (whole picture: portraits, charts), or a list of 1–4 of these:
   the scene shows them one after the other. How a picture moves and how a scene arrives is your choice, by the
   meaning of the lines (owner, 14/11/2026): `"move": "<name>"` in a picture entry, `"cut": "<name>"` and `"why":
   "<one short Vietnamese sentence>"` in the scene, from the table "Bảng cách edit" in `AGENT_JNEWS.md` (moves:
   `push-in`, `pull-back`, `pan-right`, `pan-left`, `rise`, `fall`, `close-up`, `reveal`, `punch-in`, `hold`;
   cuts: `fade`, `page`, `hard`, `dip`). Without them the old automatic choice stays. The preview prints the list
   of edits and writes it to `edits.md`. Owner, 19/11/2026: a scene over 6 seconds of words gets 2 pictures, under
   that 1 is enough (14/11/2026: a new picture every 4–5 seconds; two a scene until 19/11); the video moves: pictures zoom or pan (a different way each), fade into each other, the scene text
   slides in, captions fade in, scenes change with a cross-fade (`news`) or a page turn plus film grain (`paper`). Preview before rendering:
   `python -m news --story stories/<name>.json --pictures <find folder> --stills <out>` and look at `sheet.jpg`
   (needs `sudo apt-get update -qq && sudo apt-get install -y fonts-noto-cjk` and `pip install -r requirements.txt` for budoux; `<find
   folder>`: `git archive origin/renders <name>/find | tar -x -C <dir>`). It also checks the picks against the
   find `index.json` and lists the scenes without a picture. Then **review the pictures** (owner, 18/11/2026):
   `python tools/review_picks.py stories/<name>.json <find folder> <stills folder>` puts every pick beside the
   words spoken while it is on screen and its source title; check each row as `AGENT_JNEWS.md` §2 step 5 says
   (right person, place, event and era for those words; the picture rules of the edit above: the first picture,
   faces whole and seen; clean and sharp),
   re-pick and review again until every row passes. Only then set `stage: "render"` and push.
4. The render (~3–6 min) replaces `renders/<name>/` (keeping `find/`): `video.mp4`, `subtitles.srt`,
   `sources.json` and `credits.txt` (picture credits; `credits.txt` is for the video description), `caption.txt`
   (the posting caption, see below), `stills/sheet.jpg`, `status.json`. Check the run succeeded and that
   `status.json` has your commit (an old video stays there when a render fails). Look at the stills and the
   subtitles, then give the owner the links
   `https://github.com/maihaianh2911-bit/japan-news-video-factory/blob/renders/<name>/video.mp4` (and
   `subtitles.srt`, `credits.txt`, `caption.txt`), and say which scenes have no picture and why. GitHub refuses a file over 100 MB, so the video is
   kept under about 88 MB: full quality up to about 1 min 50 s, a lower bitrate beyond (`news/render.py`). Old
   videos are deleted from `renders` every week (`renders-cleanup.yml`: issue closed for 2 days, or no activity
   for 14 days; `mau-boj` always stays), so tell the owner to download the video.

### Posting caption (owner, 16/11/2026: every video comes with its caption)
Each video has `captions/<name>.txt` beside the story (UTF-8, Japanese, ≤ 2000 characters; example `captions/2026-11-16-nobuko.txt`):
   line 1 a hook title (≤ 80 characters, true to the script), then 2–4 short sentences on the video, a blank line,
   one line of 5–8 hashtags (`#皇室 #昭和 #歴史 #shorts` as fitting), a blank line, and the credit line
   `画像出典: <元動画 when source-video pictures are used>、<main sites> ほか（写真・音楽の全出典は credits.txt）`.
   Only facts of the script. **A video that tells a rumour gets a correction note** (owner, 19/11/2026): 1–3 lines
   starting with ※, between the sentences and the hashtags, saying which part is a rumour and what is known, e.g.
   `※〇〇という話は、一部で噂として伝えられているもので、事実とは確認されていません。`
   `python -m news.captions captions/<name>.txt` checks it (`python -m news.custom` too).
The render publishes it as `renders/<name>/caption.txt` beside `video.mp4`. A push that changes only the caption
(the story file unchanged) does not voice, search or render again: the workflow only adds `caption.txt` to the
finished folder (`tools/publish.sh` with `PUBLISH_MODE=add`, which leaves `video.mp4` and the rest as they are).
Write the caption before the closing comment and link it there next to the video, subtitles and `credits.txt`.

Owner, 14/11/2026: pictures may come from anywhere on the web (`web:` searches), for the best pictures; the owner
was told about the copyright risk and accepted it. Owner, 12/11/2026: a video with only a few pictures is not acceptable. Give every scene its own fitting
picture: write a `wiki:` search for every person and place, 2–3 searches per scene from the start, and search again until each scene has one; a text card is
the exception (pure figures), and the owner is told which scenes have none and why. Wikimedia refuses requests from Claude's cloud session (429), which is why
the search runs on GitHub. The voice engine runs only on GitHub (Docker).

## Changing the pipeline
`python3 -m compileall -q news`, `python -m news.custom` on every story, `python tools/find_test.py` (the picture
search on made-up answers: no network, no torch), and a stills preview of
`stories/mau-boj.json` (look at the sheet), and after a change to the frames or the encoder
`python tools/encode_test.py stories/mau-boj.json <find folder> <out>` (3 seconds of real video in both frames,
needs ffmpeg) and `python tools/edits_test.py stories/mau-boj.json <find folder> <out>` (every move and cut of
the catalogue: look at `moves.jpg` and `cuts.jpg`) and `python tools/fx_test.py stories/mau-boj.json <find folder>
<out>` (the picture effects: the caption timing on a made-up voice answer, stills with the effects on, which must
differ from the plain ones; needs the libraries, the model and the typeface named under `fx` above; look at
`<out>/fx/sheet.jpg`). `stories/mau-boj.json` has no `move`/`cut` and no `fx` on purpose: its
stills must stay the same, which proves that old stories render as before. A push of code to `main` runs the same check on GitHub, offline (no voice, no live sources; the
stills are in the run's Artifacts), also when the same push carries a story. The live demo (`--demo`, boj.or.jp + VOICEVOX)
runs only from Run workflow → `demo`. `tools/publish.sh` replaces a folder of `renders` as a whole and writes
`status.json`. Never touch secrets. No pull requests unless asked.
