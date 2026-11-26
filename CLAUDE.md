# japan-news-video-factory — notes for Claude

## Iron rules (owner, 16/11/2026) — they come before everything else in this file
1. **The video is in the channel's language: Japanese (tiếng Nhật).** The voice is a Japanese VOICEVOX voice (青山龍星 by default; since 25/11/2026 a male or female voice chosen per video, see "Frame and voice by content"), and the script lines, subtitles and
   on-screen text are in Japanese (tiếng Nhật). A script that arrives in another language is translated faithfully into Japanese (tiếng Nhật)
   first. Never a voice or text of another language: check the language of `lines` and the voice before the voice
   step, and again on the finished video. A video in the wrong language is not delivered: fix it and render again.
2. **No video under 60 seconds.** Before the voice step, estimate the length from the script (use the seconds per
   line of this channel's earlier videos); after the voice step, read the real length of the speech (the machine
   comment gives it). If the video would be under 60 seconds, **write the script longer** (more true facts and
   detail on the same subject, in the owner's tone, nothing invented) until it passes 60 seconds, tell the owner on
   the issue what was added, and only then go on (a script may be changed for this as for any improvement, see the
   rule changes of 19/11/2026). Never render or deliver a video under 60 seconds. Only exception: a trial or sample video — the owner says so,
   or the issue title or notes say `thử`, `mẫu`, `test` or `demo`.
3. **Every video is vertical (1080×1920), longer than 61 seconds and at most 160 seconds** (owner, 18/11/2026:
   "tất cả các kênh đều làm dạng dọc, 80-160s thôi"; changed by the owner on 19/11/2026: "không cần ép 80s, chỉ cần
   trên 61s"). Do not lengthen a script only to reach 80 s: a script the owner cut stays cut as long as it passes
   61 s. Under 61 s add true scenes and details of the same story (never padding); over 160 s cut repetition.
   Trial or sample videos are the exception, as in rule 2.

## The owner's rule changes of 19/11/2026 — they win over any older sentence in this file or in `AGENT_JNEWS.md`
The owner read the list of the hard rules and said of six of them "mấy cái này ko hợp lí", then chose what replaces
each (the same in every repo of the owner's Japanese channels):
1. **A script the owner sends may be improved** (owner: "Sửa cả kịch bản tao gửi"): Claude may cut, add and rewrite
   it so that it is better and more gripping (the writing rules of "When the owner sends an original video" apply
   to it too), keeping the owner's story and main idea. It is no longer translated sentence by sentence and left
   as it is. Say in the chat or on the issue what was changed.
2. **Rumours and unconfirmed details may be told on every channel** (owner: "Dùng tin đồn ở mọi kênh"), and the
   posting caption says so in a ※ note (which part is a rumour, what is known). **No hedging words in the
   narration** (owner, 24/11/2026: "phần đính chính sẽ ghi ở caption, đừng ghi vào video"; 25/11/2026: "Tao đéo thích
   từ nghe nói với hình như cc gì cả"): no 「…といいます」「…と噂されています」「…らしい」「…ようです」; a fact or a
   quote a press article reports is told plainly, and only the ※ note of the caption says what is unconfirmed.
3. **The telling may be dramatised** (owner: "Thêm thắt cho kịch tính"): feelings, a narrator's lead-in, suspense,
   the order of the telling. The one line that stays: an event or a quote of a real person is never made up and
   told as a fact.
4. **The ending is free** (owner: "Tự do, miễn hay"): whatever ends this story best — a line that stays, a last
   surprising detail, a return to the opening, a question to the viewer, a lead to the next video. No fixed form,
   and not the same one on every video.
5. **The voice and the music of a video the owner sends may be used**, as its pictures and footage are (owner:
   "Được dùng cả nhạc và giọng"). The owner was told the risk: music under copyright is recognised by YouTube
   (a muted video, lost revenue, a strike), and the more of the source a video carries, the more it counts as
   reused content. The engine cannot put a sound of the source into a video yet (its music comes from a `music:`
   search, its voice from VOICEVOX): like moving footage, that needs new code and a trial the owner approves.
6. **Pictures a scene** (owner: "nếu nội dung quá 6s thì phải tìm 2 ảnh, dưới 6s thì 1 ảnh cũng đc, tự do"): a
   scene whose words last over 6 seconds has at least two pictures; under 6 seconds one is enough; more is free
   (before: two a scene). About 6.5 kana-reading characters a second at speed 1.0, so about 47 at speed 1.2.

## Frame and voice by content (owner, 25/11/2026) — for every channel of this repo
Asked whether one frame for every video makes TikTok see "mass-produced content", the owner decided: "M tự đổi
luân phiên, xem nội dung hợp với khung nào thì làm với khung đó, voice thì có thể tùy biến nam nữ ở voicevox, hợp là
đc". (What was explained to the owner: the frame alone is not the main risk; a slideshow of still pictures with a
machine voice and press photos, barely changed, is what gets flagged as unoriginal; TikTok publishes no exact rule.)
- **The frame fits the story, and changes from video to video**: never the same frame for every video of a day or
  of a channel in a row. The five frames that turn (owner, 25/11/2026: "M có thể tự làm vài khung nữa, t nghĩ
  khoảng 5 khung đổi liên thiên là ổn"; `"album"` and `"magazine"` made that day): `"story"` (old newspaper: Showa
  and old photographs, a story told in the past), `"full"` (the picture fills the screen: tall, sharp modern photos,
  a person's face), `"band"` (blurred picture behind a wide band: landscape press photos and TV stills, history),
  `"album"` (a family photo album: the picture as a print in a white mat on cream paper, the era written under it —
  love, couple, mother-and-child, a life looked back on), `"magazine"` (a clean white weekly-magazine page: the
  picture across the top, a red rule, a bold black headline — today's news, a statement, a controversy, a press
  conference). `"paper"` and `"history"` stay for their own uses. In `album` and `magazine` no text lies on the
  picture (the quote stands under it, like `band`), and no credits are printed (they are in `credits.txt`). The same story may not suit `full` if its pictures are small or wide: then `band` or
  `story`. Say in the issue which frame and why (one line).
- **The voice fits the story**: a story key `"speaker"` names the VOICEVOX voice, `"<name>"` (its ノーマル style)
  or `"<name>/<style>"`; without it the voice is 青山龍星. A gentle female voice for a mother-and-daughter or a
  princess's story, a calm male one for an emperor, war or history, a lively one for a light story — and vary it
  across videos too. Calm voices that suit narration: female 冥鳴ひまり, 四国めたん, 春日部つむぎ, No.7
  (`No.7/アナウンス` or `/読み聞かせ`); male 青山龍星, 玄野武宏, 白上虎太郎, 剣崎雌雄, 雀松朱司. The render
  credits it as `VOICEVOX:<name>` on screen and in `credits.txt` (VOICEVOX asks for that credit; keep it in the
  video description). A name the engine does not have stops the voice step with the list of the voices it has:
  copy the exact name from it. Listen to the first video in a new voice before using it again. A scene may have its
  own `"speaker"` too (a sampler of voices, a quote in another voice); the credit then names every voice used.
  Owner, 25/11/2026, after two trials (冥鳴ひまり with a classical shakuhachi, No.7 読み聞かせ with a modern one):
  "ko hay, cả 2 giọng lẫn sáo đều ko, dùng sáo tao gửi này, còn giọng thì tìm lại" — those two voices and those two
  Commons flute pieces are not used; the owner's own flute is `stories/media/music/owner-flute-1.mp3` (58.7 s,
  `"music:file:stories/media/music/owner-flute-1.mp3"` as a search, credited 提供音源), and the voice is chosen
  from a sampler video of 13 voices (`stories/2026-11-25-test-voice-samples.json`) by the owner.
- **The voice and the music of the imperial-family and star videos (`[Tin Nhật]`), from 25/11/2026** — the owner
  heard the sampler (an mp3 of the 13 voices over the flute) and chose: "giọng nữ số 1" = **もち子さん**. Every new
  story of this channel carries `"speaker": "もち子さん"` and the owner's flute: the search
  `"music:file:stories/media/music/owner-flute-1-long.mp3"` (the 58.7-second piece joined three times with 4-second
  cross-fades, 168 s, so that it never jumps where it would loop) and `"music": {"pick": "<k>-1", "volume": 0.7}`.
  The gentle piano and 青山龍星 stay for the other channels (history, `ts`, …) until the owner says otherwise. When
  the owner wants voices compared, send an **mp3** (the owner, 25/11/2026: "làm file mp3 trc, chốt voice đã") with
  the time each voice starts, not a video.

## The growth plan (owner, 25/11/2026: the latest videos got no views; "Ok từ ngày mai hãy cải thiện")
Claude gave the owner the likely causes (weak first two seconds; a machine voice; 65–80-second Shorts on a new
channel; one channel mixing every topic; a mass-produced look) and a two-week plan, which the owner accepted. From
26/11/2026, for every new video of **the stars channel** (the chat that makes videos of famous people — Showa
stars, actors, singers, athletes — whose issues are titled `[Tin Nhật]` too; the imperial-family chat has its own
rule below; the voice and the flute are already new, see above):
- **The first two seconds decide.** The opening quote tells the whole idea, as the hook rule below says (the
  three videos over 100k views of the imperial channel had hooks of 44–48 characters on 4 rows), and with `fx` the engine shows
  it **from the very first frame**, larger when it is short (`draw_quote(…, hook=True)`, all frames). The first
  picture is the most striking face of the story and moves from the first frame (`push-in` or `punch-in`, never
  `hold`).
- **No length test**: Claude had proposed alternating 30–40-second videos; the owner refused (25/11/2026, angry: "Sao
  lại 36s. Video k đc dưới 60s cơ mà"). Every video stays over 61 s, about 65 s (iron rules 2 and 3).
- **One theme for this channel**: the love and married life of famous people (couples, a marriage, a loss, a
  promise kept), the kind of story that has drawn views on these channels (`masako-rikon`); no beauty tips or
  gossip lists on it (another channel, if the owner opens one).
- **Posting is the owner's side** (told in the chat): one or two videos a day at 19–21 h Japan time, about 20
  videos before judging, never delete a video.
- After a week, ask the owner for the YouTube Studio numbers of 3–5 videos (views, viewed vs swiped away, average %
  viewed): 0–50 views each points at the channel (settings, re-uploads, VPN), a few hundred that stop at the videos.

## Two new kinds of content in the narrator frame (owner, 26/11/2026) — being set up, no video made yet
The owner showed a Vietnamese short (a masked presenter at the foot, the pictures above, a big title between them:
"Cha đẻ của TĐ Phú Cường") and said: "Tao định đẻ thêm 2 loại nội dung cho video này, 1 loại sẽ dành cho doanh nhân,
chính trị gia v...v, 1 loại sẽ là phim/truyện". Both use the `band` frame with a narrator (`"host"`).
- **The chat of the film and story channel** (owner, 26/11/2026, in the chat where these kinds were set up: "Ở chat
  này mình sẽ chỉ làm riêng nội dung về phim hoặc là chuyện. Như tao đã nói, mày chỉ cần để ý đến luật chung và luật
  riêng của kênh này, còn những luật của kênh khác thì không cần quan tâm"): that chat makes film and story videos
  only (the business and politician kind is for another chat), and follows the rules for every channel (the iron
  rules with this channel's own length, the rule changes of 19/11/2026, the picture rules of the edit, every picture
  moves, nothing built before the script is approved, the script shown as one continuous text, a caption for every
  video, only the finished video sent) and this channel's own rules below. The rules of the other channels do not
  apply to it: the imperial-family and star rules (もち子さん and the flute, the love theme, about 65 s), the `ts`
  rules (80 s, read fast), the history rules (drama stills, the samurai).
- **Business people, politicians and the like**: the "father of …" angle of the sample (「ユニクロを作った男」), people the
  Japanese audience knows. Not the whole life from childhood (that is the `ts` channel): one feat, one decision.
- **Films and stories = film reviews.** Claude warned that in Japan a video telling a whole film with its footage is
  ファスト映画 (arrests in 2021, 500 million yen of damages) and proposed behind-the-scenes stories instead; the owner
  answered "TikTok vẫn cho làm review phim mà". So reviews are made, in our own words with our own comment (the
  film's dialogue is not read out at length). The angle is a question about a film, the owner's example: "vì sao khi
  xem mộ đom đóm những người cứng rắn nhất cũng sẽ khóc".
- **How a video of these two kinds is made** (owner: "tao sẽ gửi cho mày một video khá dài khoảng 10 phút, hoặc là
  tao sẽ gửi cho mày một kịch bản dài. Sau đó mày sẽ dựa vào đó để dựng lại một kịch bản mới khoảng 3 phút, 2 đến 3
  phút thôi. Sau đó thì phần hình ảnh thì có thể lấy ở video tao gửi, nhưng mà mình sẽ chỉ làm khoảng 5 giây đầu hook
  là video, còn đoạn sau mình sẽ dùng hình ảnh"): the owner sends a long source (a video of about 10 minutes, or a
  long script); Claude writes a new script of **2–3 minutes** from it, shown in the chat and approved before anything
  is built; **the first about 5 seconds (the hook) are moving footage** from the owner's video, everything after is
  still pictures (frames of the owner's video, `tools/video_frames.py`, and the searches).
- **Length**: 2–3 minutes are the owner's words for these two kinds, so up to 180 s here (the owner was told that
  iron rule 3 says 160 s and that Claude reads this as "these two kinds only"; the other kinds keep 160 s).
- **Not settled yet** (Claude's proposals, the owner has not answered): the seals `成功者の物語` and `映画の裏話`; the
  issue titles `[Doanh nhân] …` and `[Phim] …`; a narrator character for each kind (the samurai is for history;
  proposed for films: a cinema attendant in uniform holding popcorn), drawn by ChatGPT on green like the samurai.
- **What the engine lacks for it**: a clip comes from Commons or from an https address only (`video:` in
  `news/find.py`): the hook clip of the owner's video needs `video:file:stories/media/<story>/<name>.mp4`, to be
  added and tried on the first source video (the owner approves the trial). The cloud session has no speech-to-text
  (the model's host is refused by the network): the words of a source video are read from its burnt-in captions;
  when it has none, ask the owner for the script as text.
- **Claude writes scripts on its own too** (owner, 26/11/2026: "khả năng m cũng sẽ phải tự viết kịch bản"): when
  the owner sends no source, Claude researches the film (facts a press article reports, checked by a search), writes
  the 2–3 minute script itself and shows it for approval. Such a video has no source video for the 5-second hook:
  ask the owner for a short clip of the film, else the hook is a still that moves.
- First script: 火垂るの墓, "why even the toughest people cry" (about 2 min 30 s at speed 1.2; a 70-second draft came
  before the owner gave the length), shown in the chat of 26/11/2026, waiting for the owner's yes.

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
every one before the render): the first picture under 900 px on one side, or shown whole / marked flat (rules 1 and
4); a face cut by the frame or leaving it during the move, with the `"focus"` that keeps it when there is one
(rule 6); a face under the headline or the hook line, or in the lower half of the first picture (rules 5 and 7).
The faces are found by `news/faces.py` (YuNet of OpenCV Zoo, the model is `news/face_yunet.onnx`); it needs
`pip install opencv-python-headless numpy`, and without it the preview says `note: faces not checked`: then look
at every face yourself. The machine does not see rules 2, 3, 8 and 9: those are for your eyes, at the review.

## The history frame and the new kinds of content (owner, 20–21/11/2026)
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
- `"style": "band"` — **the frame of the history videos from 24/11/2026** (owner, showing a short he liked:
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
- **Drama stills first** (owner, 24/11/2026: "nên dùng nhiều hình ảnh phim ảnh hơn"): the people of a history story
  are shown mostly by stills of one taiga drama (one face per person for the whole video: Nobunaga = Oguri Shun in
  `豊臣兄弟！`, Yukimura = Sakai Masato in `真田丸`), found through the press galleries of the episode (`page:` of a
  cinematoday / thetv gallery, `web:<drama> <episode> 場面写真`); two or three real pictures (the place today, the
  real portrait) keep it true. **The hook is a drama still or a fine photograph, never an old painting** (owner,
  24/11/2026, angry: "cái hook mở đầu quan trọng nhất mà lại để cái tranh cổ rõ xấu").
- The kinds of content so far and their seal: history `戦国の物語` / `江戸の物語` (by the period of the story);
  "Luật ngầm & Đời sống truyền thống Nhật Bản" (hidden rules and traditional life) `日本の掟`; "Sự thật đằng sau
  những địa danh & bức ảnh thật gây ám ảnh" (the truth behind places and haunting real photographs)
  `あの場所の真実`. Their issues are titled `[Lịch sử] …`, `[Luật ngầm] …`, `[Địa danh] …` with the label
  `lich-su` (not `[Tin Nhật]` and not `jnews`: the workflow's issue steps and the Claude task do not act on them;
  Claude in the chat opens the issue, comments the links and sets `jnews-busy` while working, `jnews-done` after).
- **The channel "Tiểu sử nhân vật nổi tiếng"** (biographies of famous people), short name **`ts`** (owner,
  24/11/2026: "Cho cái này vào 1 kênh riêng nhé, đặt tên là tiểu sử nhân vật nổi tiếng đi, viết tắt kênh ts"): the
  life of one person from childhood to fame, real pictures of every age, in the `"style": "full"` frame (owner, same
  day: "Làm kiểu để ảnh full màn hình"), seal `人物伝`, `"voice": 2.4` (as the other kinds above), gentle piano at 0.7. **At most about
  80 seconds** (owner, of the first cut at 133 s: "Bình thường chỉ 80s là cao thôi mà"): about 400 written
  characters of script; and **read fast**: `"pace": {"speed": 1.3, "line_pause": 0.05, "scene_pause": 0.15}`
  (owner: "ban nãy đọc nghe rề rà quá, đọc nhanh như mấy thể loại khác"; 1.2 with pauses was too slow). Its issues are titled
  `[TS] <Japanese headline> — <Vietnamese idea>` with the label `ts` (not `jnews`; handled in the chat like the
  `lich-su` kinds above). The format came from a source video the owner sent (a short on Putin's life); the owner
  agreed that a person the Japanese audience loves fits better than a foreign politician they dislike. First video:
  `2026-11-24-naruhito-oyamoto` (issue #66).
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
  The music does not come up with it. **Every video of these new kinds carries `"voice": 2.4`.**
- **Music** (owner, 21/11/2026: "nhạc nền rít quá, cho nhẹ thôi"): a gentle piano piece at `"volume": 0.7`
  (`music:Gymnopédie Satie piano`, `music:Chopin Nocturne piano`, `music:Debussy Clair de lune piano`); no
  shakuhachi or other shrill solo instrument.
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
- Before a render, check every pick against the title and page of its source in `index.json`, not only by eye: on
  the first videos a portrait found by `wiki:` was another man of the same battle, a print was another scene, and a
  web portrait came from the page of the shogun before (`tools/review_picks.py` prints the source beside each).

The owner is Vietnamese and not technical: answer in short, simple Vietnamese, no jargon. They write "tao" (I) and
"mày" (you); answer the same way, "tao" for yourself and "mày" for them. Their standing decisions
are in `maihaianh2911-bit/japan-video-factory` → `docs/HANDOVER.md` (real pictures only, Claude looks at every
picture, quality is not traded for usage; a script the owner sends was translated faithfully and never cut or
rewritten until 19/11/2026: it may now be improved, rule change 1 above).

**The chat of the `[Tin Nhật]` channel makes videos of the Japanese imperial family only** (owner, 25/11/2026: "Chat
này vẫn chỉ làm hoàng gia nhật"; before, angry at a story of a singer: "mày làm hoàng gia nhật cơ mà"): stories
Claude proposes or writes there are about the Japanese imperial family (天皇家, 秋篠宮家, the princesses who left
it, the emperors and empresses of the past), never a foreign royal family or a star.

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
   quote of a real person and tell it as a fact (the telling may be dramatised, a rumour told as one: rule
   changes 2 and 3 above). Keep the quotes of the people as they are. Read it fast like the source:
   `"pace": {"speed": 1.2, "line_pause": 0.1, "scene_pause": 0.2}`; estimate the length at about 6.5 kana-reading
   characters a second at speed 1.0 plus the pauses (iron rule 3: over 61 s, at most 160 s). Tell the owner in the chat what you
   added. Example: `stories/2026-11-16-nobuko.json` and the four other stories of 16/11.
   How to write it (owner, 17/11/2026, after finding the scripts of that morning dull):
   - **The first line (about 5 seconds) says the whole story and what it means, plainly**, so that the viewer
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
   - A story the sources do not confirm is framed **once** (e.g. 「長く語り継がれてきた話です」, 「…と口にしたといいます」
     at the key line), not on every line.
   - Under 60 seconds: add scenes and feelings of the same story, never encyclopedic padding (number of trees,
     treaty years). Do not end every video with 「あなたはどう感じますか？」.
   - A source video too thin for a story (a few captions, no events): tell the owner before making it.
   - Owner, 17/11/2026: the love story (`masako-rikon`: a request for divorce, his answer, the proof, the two
     side by side in 2019) was the only video with views. When a source story has a love, couple or
     mother-and-child side, lead with it in the first line and build the story on it (true facts only).
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
   rewritten), with the frame and the voice that fit the story ("Frame and voice by content", 25/11/2026; `"story"` was used for every source video from 15/11 to 24/11) and a fitting `kicker` (e.g. `皇室の物語`
   for a story about the imperial family), a `wiki:` search for every person and place of the story, then `web:`
   searches (2–3 per scene, Japanese words; with a wish ` => …` where it helps), 2 pictures for a scene over
   6 seconds of words (1 is enough under that, rule change 6).
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
   allowed since 19/11/2026 as well (rule change 5: the risk was told, and the engine cannot do it yet).
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
     owner's script as improved, rule change 1), optional `value` (a big figure such as `0.5％`) and `evidence` (small text).
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
   - `"fx": {"motion": true, "depth": true, "text": true, "face": true}`: the picture effects. **The owner
     switched them on for this channel on 17/11/2026: every new story carries this line with all four**; stories
     made before are not changed (a story without `fx` renders exactly as before). What each one does:
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
