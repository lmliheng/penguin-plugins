---
name: lesson-video-landscape
description: Turn a narration script into a long narrated landscape lesson video (1920x1080, 15 minutes, YouTube/Bilibili ready) plus a 16:9 cover and a 3:4 profile cover — an HTML slide deck driven purely by time with eleven scene layouts (text, code, one-dimensional array with two pointers, table, call stack, decision tree, graph, set merging, flow), edge-tts voice-over with word-level timing, Playwright frame capture, and an ffmpeg mux. Use whenever the task is a long landscape teaching or explainer episode with on-screen algorithm walkthroughs, or its cover and publishing copy, from a written script.
short_description: Narrated 1920x1080 lesson episodes from a script: HTML deck + edge-tts + ffmpeg.
short_description_zh: 讲稿一键成横屏长视频（1920×1080，一集十五分钟）：HTML 课件 + edge-tts + ffmpeg，含封面与发布文案。
version: 2026.10.06.1
---

# 横屏长视频：讲稿 → 配音 → 逐帧渲染 → 成片 + 封面

## 结论先行

一句话：**画面是时间 t 的纯函数**。先把话写清楚，每一句话都写进脚本；配音合成后拿到逐词时间，画面按这个时间去定格 —— 配音、字幕、画面天然咬合，不需要剪辑软件。

| 你要的东西 | 用哪一步 | 产物 |
| --- | --- | --- |
| 一份讲稿 | 手写 `lessons/<集>/script.json` | 分镜 + 旁白 + 出现时机（`cue`） |
| 配音 + 时间轴 | `python lib/tts.py lessons/<集>` | `audio/narration.wav`、`lesson.json` |
| 逐帧画面 | `node lib/render.mjs --dir lessons/<集>` | `frames/f_00000.jpg…` (30fps) |
| 成片 + 字幕 | `python lib/build.py lessons/<集>` | `out/<id>.mp4`、`<id>.srt` |
| 封面 | `node lib/cover.mjs --data covers/covers.json --out covers/out --template cover-light.html --sizes 1080,1440` | 1920×1080 与 1080×1440 两张 PNG |

写成一条链（纯 CPU、不占 GPU，**15 分钟的片子约 25 分钟出片**）：

```bash
python lib/tts.py lessons/ep05          && \
node   lib/render.mjs --dir lessons/ep05 && \
python lib/build.py lessons/ep05
```

**动手前先跑自检**（一集十几秒，不出帧）：

```bash
node lib/render.mjs --dir lessons/ep05 --check
```

它报三件事：内容有没有越过 y=820 的字幕安全线、代码行有没有被卡片裁掉、标题折行有没有剩下孤字。三项全过再花二十几分钟渲染。

另有 `python tools/check_script.py lessons/ep05` 做**写稿自检**（幕型、字数、每一步的下标、cue 有没有写错），写完稿先跑它，比渲染早发现问题的代价小得多。

## 一、把工具包放进项目

技能目录里的 `kit/` 就是整个项目的骨架，**按目录结构整体复制**（`kit/` 里已经分好 `lib/` 与 `tools/`，脚本之间靠这个相对位置互相找）：

```bash
mkdir -p <项目>/lessons <项目>/covers
cp -r <技能目录>/kit/. <项目>/
```

复制完 `<项目>/lib/` 六个文件、`<项目>/tools/` 六个文件：

| 文件 | 作用 |
| --- | --- |
| `lib/tts.py` | edge-tts 逐幕配音，拿逐词边界，写出 `lesson.json`（时间轴 + 字幕）+ `narration.wav` |
| `lib/render.mjs` | Playwright 逐帧截图；`--check` 只自检；`--scale 0.5` 低清预览 |
| `lib/build.py` | ffmpeg 合成 H.264/AAC、响度归一、`+faststart`，顺带写 SRT |
| `lib/deck-light.html` | 课件本体，**1920×1080 白底演讲版**，十一种幕型（见第三节） |
| `lib/cover.mjs` / `lib/cover-light.html` | 封面图（1920×1080 视频首图 + 1080×1440 主页 3:4） |
| `tools/check_script.py` | 写稿自检：幕型清单、字数、下标越界、cue 是否出现在旁白里 |
| `tools/peek.mjs` | 按秒抽帧目视检查，不跑整条渲染 |
| `tools/probe_dump.mjs` | 打印某一幕的 DOM 状态，查可视化幕型哪里没按预期渲染 |
| `tools/dump_script.py` | 把 `script.json` 摊平成可读讲稿，给人看内容 |
| `tools/voice_ab.py` | 同一段旁白多个候选音色各出一份试听小样，用来挑配音 |
| `tools/fonts.mjs` | 探测本机有哪些字体族 |

**依赖**（缺哪个装哪个）：

| 依赖 | 装法 | 备注 |
| --- | --- | --- |
| Python 包 | `pip install edge-tts imageio-ffmpeg` | `imageio-ffmpeg` 自带 ffmpeg 二进制，不用单独装 ffmpeg |
| Node 包 | 任意可用的 `playwright-core` | 用 `PLAYWRIGHT_MODULE` 指到它的路径即可，不必装进本项目 |
| 浏览器 | 任意 Chrome / Chromium 可执行文件 | 用 `CHROME_PATH` 指过去 |

两个环境变量（Windows / Linux 一样，`render.mjs`、`cover.mjs`、`peek.mjs`、`probe_dump.mjs`、`fonts.mjs` 都认）：

```bash
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright-core \
CHROME_PATH=/path/to/chrome.exe \
  node lib/render.mjs --dir lessons/ep05
```

Windows 上**每个 Python 调用前加 `PYTHONUTF8=1`**（控制台是 GBK，不加会 `UnicodeEncodeError`）。

## 二、脚本 `script.json` 怎么写

顶层字段：

| 字段 | 含义 |
| --- | --- |
| `id` | 集目录名与成片名（`out/<id>.mp4`），如 `ep05-window-prefix` |
| `series` / `episode` | 系列名 / 集标题（只在日志里用） |
| `size` | **必须写 `1920x1080`** —— 画布尺寸由它决定，`deck-light.html` 的 CSS 就按这个尺寸写死 |
| `deck` | **必须写 `deck-light.html`** —— 本工具包只发这一份版式；不写会去找不存在的 `lib/deck.html` |
| `brand` / `mark` | 画面左上台标文字 / 台标方块的字母（不给取 `brand` 首字） |
| `wm` | 画面右上角水印文字；不给就整块隐藏 |
| `voice` / `rate` | edge-tts 音色与语速，如 `zh-CN-YunxiNeural` / `+18%` |
| `gap` | 每幕之间的静音秒数，默认 0.35；一口气讲完的系列用 0.3 |
| `scenes` | 幕数组，见下 |

每一幕：`id`（幕内短名，用来命名音频）、`type`（版式）、`narration`（**这一集真正要讲的话**，200–300 字），其余字段按 `type` 取。

`deck-light.html` **只实现了这 11 种幕型**：`title` / `points` / `code` / `array` / `grid` / `stack` / `tree` / `graph` / `groups` / `flow` / `outro`。写了别的（例如老黑底版的 `math` / `source`）**渲染直接崩**，`check_script.py` 会拦下来。要讲「公式 / 不变量」用 `flow` 或 `points`，要「代码 + 三条观察」用两幕（`code` + `points`）。

| `type` | 特有字段 | 用途 |
| --- | --- | --- |
| `title` | `kicker` `title` `sub` `tags[]` | 开场：大标题 + 一句副标题 + 三两个标签 |
| `points` | `kicker` `title` `items[]` `takeaway` | 要点幕，**正好 3 条**、每条 ≤ 44 字，`<em>` 标蓝关键词 |
| `code` | `kicker` `title` `file` `code` `code_reveal` | 代码卡，`code` 用 `\n` 分行、逐行出现 |
| `array` | `values[]` `l`/`r` `lblL`/`lblR` `hideWin` `chips[]` `steps[]` `target`/`best` | **一维数组 + 两个指针 + 读数芯片**，最常用的可视化 |
| `grid` | `rows[]` `cols[]` `chips[]` `steps[]` | 二维表格逐格填（DP 表） |
| `stack` | `frames[]` `steps[]` | 调用栈 / 递归栈，逐层压入弹出 |
| `tree` | `nodes[]`（`id`/`p`/`t`） `steps[]` | 递归树 / 决策树，可展开可剪枝 |
| `graph` | `nodes[]`（`id`/`t`/`x`/`y`） `edges[]` `steps[]` | 图 / 网格图，BFS/DFS 走一遍 |
| `groups` | `steps[]` | 并查集：集合合并 |
| `flow` | `nodes[]`（`t`/`s`） `steps[]` | 流程卡片，讲「为什么慢 / 为什么不亏」 |
| `outro` | `kicker` `title` `sub` `cta` | 结尾 + CTA 按钮 |

**每个幕型的完整字段、取值范围与写法**，见技能目录里的 `spec/SPEC-for-writers.md`（写手必读）；`example/script.json` 是一份**十一种幕型各跑一幕**的可运行样稿，照着改最快 —— 它只有 806 字旁白，自检要放宽参数才过：

```bash
python tools/check_script.py lessons/demo-light --narr=40,200 --total=700,1400 --scenes=5,12 --viz=5
```

（正式一集不加这些参数，用的就是 4800–5200 字 / 20–26 幕的默认门槛。）

### 出现时机：写 `cue`，不写秒数

任何元素上写 `"cue": "关键词"`，`tts.py` 会在**配音的逐词时间**里找这个关键词，把元素出现的时刻标成 `at`（相对本幕秒数，比人声早 0.15s）。

- 关键词必须**真的出现在同一幕的 `narration` 里**（按去掉空白的字符流做子串匹配），否则静默失败、元素永不出现；`check_script.py` 会替你查；
- 想要 CTA 晚点出，就写 `"cta_cue": "关注"` —— 任何 `<名>_cue` 都会解析成 `<名>_at`；
- 已经手写了 `at` 的不会被覆盖，两种写法可以混用；
- 中文数字按念法写关键词：旁白念「负二点三四」，cue 就写 `负二点三四`，别写 `-2.34`。

### 字数与节奏（实测）

中文旁白约 **5.8 字/秒**（`rate` 为 `+18%`、`zh-CN-YunxiNeural`）——**一集 15 分钟 ≈ 4800–5200 字，幕数 20–26**，每幕 200–300 字，按这个数分配。写完先估一遍，别等合成完才发现超时。

## 三、画面规矩（都在 `lib/deck-light.html` 里，改一处全片生效）

**安全区**：横屏上下留白、字幕压在下沿，内容不能越过字幕带。

| 位置 | 数值 |
| --- | --- |
| 场景内边距 | `padding: 132px 240px 260px 120px`（上 / 右 / 下 / 左） |
| 内容可用区 | 宽 **1560px**、高 **680px**（y=140 → y=820） |
| 自检安全线 | **820**（`render.mjs --check` 量的就是这条） |
| 字幕带 | y=830 起，两行居中 1920px 宽 |

由此推出几条硬约束，`check_script.py` 与 `render.mjs --check` 会替你量：

1. **内容底边 < 820**，否则盖住字幕；
2. **代码行 ≤ 84 个西文字符、最多 9 行** —— `.card-bd` 是 `overflow:hidden`，超了会被**悄悄裁掉**；
3. `array.values` 最多 **13 格**（一行放得下 13 格）；
4. `grid.rows` / `cols` 各 **2–6 个**；`stack.frames` **3–8 帧**；
5. `tree` 节点 **≤ 15 个、层数 ≤ 4**；`graph` 节点 **≤ 10 个**、`queue` **≤ 8 项**；`groups` 每步 **2–6 个集合**。

另外两点：

- `kicker` 会被 CSS `text-transform:uppercase`，别在里面写敏感字形；
- 标题用了 `text-wrap:balance`，折行时左右均衡，避免最后一行只剩一两个字。

## 四、封面 `covers.json` + `covers/out/`

```bash
PLAYWRIGHT_MODULE=… CHROME_PATH=… \
  node lib/cover.mjs --data covers/covers.json --out covers/out \
    --template cover-light.html --sizes 1080,1440
```

**`--template` 默认是深色模板；横屏白底系列要显式给 `cover-light.html`**，`--sizes` 用 `1080,1440`（横屏没有竖屏的 1920 档）。

每条封面一个对象：`id`（文件名前缀）`no`（集号，右上角大数字）`brand` `wm` `cta` `titleLines[]`（**自己写好断行**，最后一行自动标蓝）`subLines[]`（每行别超过约 20 字）`pills[]`（三个标签）`tag`（可选，接在「第 N 集」后面）`foot`（左下角一行）。

一次出两张：`<id>-16x9.png`（1920×1080，视频首图）和 `<id>-1080x1440.png`（1080×1440，主页封面）。

## 五、发布物料

写进项目的 `covers/copy.md`，一集一段：**标题**（一句话，最好带一个真实数字）、**文案**（三行要点 + 每行一句解释）、**标签**。

- 抖音描述**标签最多 5 个**，多了不显示；
- 文案里的数字**必须是片子里真跑出来的**，不要编 —— 这一条比排版重要得多。

## 六、写手子代理怎么分工

一集 5000 字，值得派子代理并行写。分工边界（照做，否则渲染会互相踩）：

- 子代理**只写** `lessons/<集>/script.json`、实跑验证脚本 `facts/<集>.py` + 输出 `facts/<集>.json`、以及 `lessons/<集>/NOTES.md`；
- 子代理**不许跑** `tts.py` / `render.mjs` / `build.py`（`frames/` 目录只有一份，两个进程同时渲染会互相删帧）；自检只跑 `tools/check_script.py`，通过才算交稿；
- 主 agent 统一配音、渲染、合成与交付。

**所有上屏的数字必须真跑**：`facts/<集>.py` 用题目给的样例跑一遍片中每段代码并 `assert` 结果，复杂度声称要么计数量级、要么用 `time.perf_counter()` 实测两个写法的真实耗时比；`array`/`grid` 的每一步还要用真实代码重算轨迹、逐字段比对。

## 七、踩过的坑

1. **`data-r` / `data-at` 是课件的保留属性**（数据里表示「第几步」「第几秒」），自定义元素千万不要用这两个名字当属性 —— 会被当成渐入动画的时机，曾经把整张表除第一行外全变成不可见。用 `data-row` 之类的别的名字。
2. **高的可视化幕（grid / stack / tree / graph / groups）要把结论条并进读数行**（`.tkinline`），`takeaway` 另起一行会顶到字幕安全线，自检直接报越线。
3. **grid / stack 会量一次自然尺寸再等比 `scale` 到容器**（小表格也会放大，上限 1.5 倍）；tree / graph 用固定 viewBox + 较小的显示高度自动缩放。改样式时别把 `transform` 覆盖掉。
4. **Windows 控制台是 GBK**：一切 Python 调用加 `PYTHONUTF8=1`。
5. **`frames/` 很占地方**：一集 3–4 GB，且 `render.mjs` **每次运行（含 `--check`）都会先清空该目录**。确认成片没问题后删 `lessons/<集>/frames/`，要重渲再跑一次。
6. **渲染速度实测 29ms/帧**：15 分钟一集 27000 帧 ≈ 13 分钟渲染，加上配音合成，一集 30–40 分钟。
7. **成片响度是 `loudnorm=I=-14:TP=-1.5:LRA=11`**：给用户试听的小样要对齐同一响度，否则「成片比试听小」会被当成 bug。
8. **邮件发大附件有硬上限**：IMAP「已发送」的硬上限是 20,971,520 字节，60MB 级的邮件投递能成功但不会留底 —— 交付成片别指望邮箱留档。
9. **名人音色不可克隆**（合规）：只能从 edge-tts 的中文音色里挑，用 `tools/voice_ab.py` 做 A/B 试听再定。
10. **`edge-tts` 偶尔空手而归**（`NoAudioReceived`）：`tts.py` 里已带 4 次重试，别自己再包一层；必须显式要 `boundary="WordBoundary"`，否则拿不到逐词时间。
11. **`PLAYWRIGHT_MODULE` 指的必须是 playwright-core 的目录**（含 `package.json` 那层），不是 `playwright`。
12. **Python 写回的 JSON 是 CRLF**：要改已经生成过的 `lesson.json`，别用文本替换，改用 Python 脚本读写。

## 八、边界

- 画面是**时间 t 的纯函数**，没有 CSS 过渡、没有随机数：同一份 `script.json` 每次渲染结果一致，改一句话重渲即可。
- 本工具包只做 **1920×1080 横屏**（`deck-light.html` 的宽高与内边距是硬编码的）；竖屏短视频用同一个插件里的 `lesson-video` 技能。
- 配音只走 edge-tts（免费、无需密钥）。要换别的 TTS，替换 `tts.py` 里的 `synth()` 即可，其余步骤不用动。
- 字幕有两个出口：`deck-light.html` 把「上一句 + 当前句」画在 y=830 的字幕带上（**跟着帧烧进画面**），`build.py` 同时写出 `<id>.srt`。两份都来自 `tts.py` 按词边界切的短行，不要手改。
