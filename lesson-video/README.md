# lesson-video

Narrated **lesson videos** from a written script — plus the cover art and the publishing copy that goes with them. Two formats, one idea.

| Skill | Format | What it is for |
| --- | --- | --- |
| `lesson-video` | 1080×1920, 3–5 min | Vertical shorts, Douyin / Reels ready: sides and top stay empty for the phone app buttons; four core scene types |
| `lesson-video-landscape` | 1920×1080, ~15 min | Landscape episodes: eleven scene layouts, including algorithm walkthroughs (see below); a 16:9 video cover and a 3:4 profile cover |

Both rest on the same principle: **the picture is a pure function of time `t`**. You write what is said, edge-tts speaks it and hands back word-level timings, and every frame is then *computed* from that timeline. Voice, subtitles and slides line up by construction, so there is nothing to edit afterwards.

```
script.json  ──tts.py──▶  narration.wav + lesson.json  ──render.mjs──▶  30fps JPEG frames  ──build.py──▶  mp4 + srt
covers.json  ──cover.mjs──▶  video cover + profile cover
```

## Why it exists

- **A pre-render self-check.** `render.mjs --check` fails *before* spending minutes on frames: content past the subtitle safe line, code lines clipped by the card, and titles left with a one-character orphan line.
- **A writing self-check.** `tools/check_script.py` measures the script itself — allowed scene types, word counts, out-of-range indices, and every `cue` that does not appear verbatim in its own narration (that element would simply never appear).
- **No editing software, no GPU.** Headless Chrome + `imageio-ffmpeg`. A three-minute short renders in about five minutes on CPU, a fifteen-minute episode in about twenty-five.
- **No baked-in branding.** Watermark, brand mark, CTA and every caption come from the data files — the templates ship with nothing of anyone's hard-coded.

## The landscape scene layouts

`deck-light.html` implements eleven scene types: `title`, `points`, `code`, `array` (one-dimensional array with two pointers, reading chips, source-cell highlighting), `grid` (a DP table filled cell by cell), `stack`, `tree` (with pruning), `graph` (visited / current node, highlighted edge, queue bar), `groups` (set merging), `flow`, `outro`. At least six visualisation scenes per episode are enforced by the writing check.

## What's inside

| Path | What it is |
| --- | --- |
| `skills/lesson-video/SKILL.md` | The vertical skill: script schema, the three commands, layout rules, pitfalls |
| `skills/lesson-video/kit/` | Vertical toolkit — `tts.py`, `render.mjs`, `build.py`, `deck.html`, `cover.mjs`, `cover.html`; copy it into a project as `lib/` |
| `skills/lesson-video/example/` | A skeleton `script.json` (four scene types) and `covers.json` |
| `skills/lesson-video-landscape/SKILL.md` | The landscape skill: the three commands, the eleven scene types, layout limits, the pitfalls of the visualisation layouts |
| `skills/lesson-video-landscape/kit/lib/` | `tts.py`, `render.mjs`, `build.py`, `deck-light.html`, `cover.mjs`, `cover-light.html` — copy the kit over a project root |
| `skills/lesson-video-landscape/kit/tools/` | `check_script.py`, `peek.mjs`, `probe_dump.mjs`, `dump_script.py`, `voice_ab.py`, `fonts.mjs` |
| `skills/lesson-video-landscape/spec/SPEC-for-writers.md` | The full script schema and the rules a writer (human or subagent) must follow |
| `skills/lesson-video-landscape/example/` | A runnable `script.json` with all eleven scene types, and `covers.json` |

## Requirements

| Need | Install |
| --- | --- |
| Python packages | `pip install edge-tts imageio-ffmpeg` (the ffmpeg binary comes with the second one) |
| Playwright core | any usable `playwright-core`; point `PLAYWRIGHT_MODULE` at it |
| A browser | any Chrome / Chromium; point `CHROME_PATH` at it |

## Quick start — vertical

```bash
cp -r <skill>/kit/* <project>/lib/
mkdir -p <project>/lessons/ep01

# 1. write <project>/lessons/ep01/script.json   (see the skill for the schema)

PYTHONUTF8=1 python lib/tts.py lessons/ep01
node lib/render.mjs --dir lessons/ep01 --check          # 10s: safe area, clipped code, orphan titles
PLAYWRIGHT_MODULE=… CHROME_PATH=… node lib/render.mjs --dir lessons/ep01
PYTHONUTF8=1 python lib/build.py lessons/ep01           # out/ep01.mp4 + out/ep01.srt
```

## Quick start — landscape

```bash
cp -r <skill>/kit/. <project>/
mkdir -p <project>/lessons/ep05

# 1. write <project>/lessons/ep05/script.json   — must carry "size": "1920x1080" and "deck": "deck-light.html"
PYTHONUTF8=1 python tools/check_script.py lessons/ep05  # writing check, before anything expensive

PYTHONUTF8=1 python lib/tts.py lessons/ep05
node lib/render.mjs --dir lessons/ep05 --check          # safe area, clipped code, orphan titles
PLAYWRIGHT_MODULE=… CHROME_PATH=… node lib/render.mjs --dir lessons/ep05
PYTHONUTF8=1 python lib/build.py lessons/ep05           # out/ep05.mp4 + out/ep05.srt

PLAYWRIGHT_MODULE=… CHROME_PATH=… \
  node lib/cover.mjs --data covers/covers.json --out covers/out \
    --template cover-light.html --sizes 1080,1440        # 1920x1080 + 1080x1440 covers
```

`kit/` keeps the project layout (`lib/` next to `tools/`) on purpose: the tools find the toolkit by that relative position.

## License

Apache-2.0
