"""写稿自检：把 script.json 里所有「上屏/上口」的硬约束量一遍。

用法: PYTHONUTF8=1 python tools/check_script.py lessons/ep01-two-pointers

横屏版式（1920x1080）下可用区 1560x624，字号是 spec 里定的那套，所以长度限制是硬限制：
超了不是「不太好看」，是会被卡片裁掉或折行折散。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CODE_MAX_CHARS = 84          # 代码卡内宽 1506px / 等宽 28px 字符宽 15.4px ≈ 97 字符，留余量按 84
CODE_MAX_LINES = 9
NARR_MIN, NARR_MAX = 180, 320      # 单幕旁白（20-26 幕 × 240 字 ≈ 5000 字）
TOTAL_MIN, TOTAL_MAX = 4400, 5400  # 全集旁白
SCENES_MIN, SCENES_MAX = 18, 28
ITEM_MAX = 46                # points 每行
NOTE_MAX = 42                # source 的 notes
FORMULA_MAX = 48
TITLE_WORD_MAX = 8           # title 幕大标题
SUB_MAX = 26
BAD_SYMBOLS = "→≤≥×÷%≈±·※①②③④⑤*"      # 旁白里不该出现的符号（TTS 会念不出来）
# 白底版（deck-light.html）实现了这 11 种幕型；写了别的（比如黑底老版的 math / source）渲染会直接崩
TYPES = {"title", "points", "code", "array", "grid", "stack", "tree", "graph", "groups", "flow", "outro"}
VIZ_TYPES = {"array", "grid", "stack", "tree", "graph", "groups", "flow"}
VIZ_MIN = 6                  # 每集至少这么多幕可视化（用户的硬意见：要有算法流程演示）
LATIN_TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9\.\[\]\(\)]*")

def chars(s: str) -> int:
    return len(re.sub(r"\s", "", s))

def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
    d = Path(args[0]).resolve() if args else Path("lessons/ep01-two-pointers").resolve()
    rng = lambda k, dv: tuple(int(x) for x in opt[k].split(",")) if k in opt else dv
    narr_min, narr_max = rng("--narr", (NARR_MIN, NARR_MAX))
    total_min, total_max = rng("--total", (TOTAL_MIN, TOTAL_MAX))
    scenes_min, scenes_max = rng("--scenes", (SCENES_MIN, SCENES_MAX))
    viz_min = int(opt.get("--viz", VIZ_MIN))
    script = json.loads((d / "script.json").read_text(encoding="utf-8"))
    scenes = script["scenes"]
    # 白底版才有的约束（幕型清单、可视化幕数）只对用 deck-light.html 的稿子生效
    light = "light" in str(script.get("deck", ""))
    bad: list[str] = []
    warn: list[str] = []

    total = 0
    viz = 0
    for i, sc in enumerate(scenes, 1):
        tag = f"第 {i} 幕 ({sc.get('id')}/{sc.get('type')})"
        narr = sc.get("narration", "")
        n = chars(narr)
        total += n
        if light and sc.get("type") not in TYPES:
            bad.append(f"{tag} 白底版没有这个幕型，渲染会崩（可用：{'/'.join(sorted(TYPES))}）")
        if sc.get("type") in VIZ_TYPES:
            viz += 1
        if sc.get("type") == "outro" and "关注抖音号" not in narr:
            bad.append(f"{tag} outro 旁白里没有念「关注抖音号 liheng」")
        if not (narr_min <= n <= narr_max):
            warn.append(f"{tag} 旁白 {n} 字（建议 {narr_min}-{narr_max}）")
        for ch in BAD_SYMBOLS:
            if ch in narr:
                bad.append(f"{tag} 旁白里有符号 {ch!r}")
        if sc.get("type") == "title":
            if chars(sc.get("title", "")) > TITLE_WORD_MAX:
                bad.append(f"{tag} 大标题过长：{sc.get('title')!r}")
            if len(sc.get("tags", [])) != 3:
                bad.append(f"{tag} tags 必须正好 3 个")
            if chars(sc.get("sub", "")) > SUB_MAX:
                warn.append(f"{tag} sub 偏长：{sc.get('sub')!r}")
        if sc.get("type") == "points":
            items = sc.get("items", [])
            if len(items) != 3:
                bad.append(f"{tag} items 必须正好 3 条，现在 {len(items)}")
            for it in items:
                plain = re.sub(r"<[^>]+>", "", it)
                if chars(plain) > ITEM_MAX:
                    bad.append(f"{tag} item 过长（{chars(plain)} 字）：{plain[:24]}…")
        if sc.get("type") == "math":
            steps = sc.get("steps", [])
            if not (2 <= len(steps) <= 3):
                bad.append(f"{tag} steps 应为 2-3 张，现在 {len(steps)}")
            for st in steps:
                plain = re.sub(r"<[^>]+>", "", st.get("formula", ""))
                if chars(plain) > FORMULA_MAX:
                    warn.append(f"{tag} formula 偏长：{plain[:24]}…")
        if sc.get("type") in ("code", "source"):
            code = sc.get("code", "")
            lines = code.split("\n")
            if len(lines) > CODE_MAX_LINES:
                bad.append(f"{tag} 代码 {len(lines)} 行，超过 {CODE_MAX_LINES} 行")
            for ln in lines:
                if len(ln) > CODE_MAX_CHARS:
                    bad.append(f"{tag} 代码行 {len(ln)} 字符（>{CODE_MAX_CHARS}）：{ln[:40]}…")
            if sc.get("type") == "source":
                notes = sc.get("notes", [])
                if len(notes) != 3:
                    bad.append(f"{tag} notes 必须正好 3 条，现在 {len(notes)}")
                for nt in notes:
                    plain = re.sub(r"<[^>]+>", "", nt if isinstance(nt, str) else nt.get("text", ""))
                    if chars(plain) > NOTE_MAX:
                        bad.append(f"{tag} note 过长（{chars(plain)} 字）：{plain[:24]}…")
        if sc.get("type") == "array":
            vals = sc.get("values", [])
            if not (2 <= len(vals) <= 13):
                bad.append(f"{tag} values 应为 2-13 格（1560px 宽），现在 {len(vals)}")
            chips = sc.get("chips")
            ks = []
            if chips:
                if not (2 <= len(chips) <= 5):
                    bad.append(f"{tag} chips 应为 2-5 个，现在 {len(chips)}")
                ks = [c.get("k") for c in chips]
                for c in chips:
                    if not c.get("k") or not c.get("label"):
                        bad.append(f"{tag} chip 缺 k/label：{c}")
            steps = sc.get("steps", [])
            if len(steps) < 5:
                warn.append(f"{tag} 只有 {len(steps)} 步，动画会长时间不动（建议 8-14 步）")
            for st in steps:
                for key in ("l", "r"):
                    if not isinstance(st.get(key), (int, float)):
                        bad.append(f"{tag} step 缺 {key}：{str(st)[:40]}…")
                if st.get("l") is not None and st.get("r") is not None and st["l"] > st["r"]:
                    bad.append(f"{tag} step 的 l > r：l={st['l']} r={st['r']}")
                if chips:
                    for k in ks:
                        if k not in (st.get("vals") or {}):
                            bad.append(f"{tag} step 的 vals 缺芯片 {k!r}：{str(st)[:40]}…")
                elif not isinstance(st.get("sum"), (int, float)):
                    bad.append(f"{tag} step 既没写 chips 又缺 sum：{str(st)[:40]}…")
                for ix in st.get("from") or []:
                    if not isinstance(ix, int) or not (0 <= ix < len(vals)):
                        bad.append(f"{tag} from 里的下标越界：{ix}")
        if sc.get("type") == "grid":
            rows, cols = sc.get("rows", []), sc.get("cols", [])
            if not (2 <= len(rows) <= 6) or not (2 <= len(cols) <= 6):
                bad.append(f"{tag} rows/cols 应为 2-6 个，现在 {len(rows)}x{len(cols)}")
            steps = sc.get("steps", [])
            if len(steps) < 5:
                warn.append(f"{tag} 只有 {len(steps)} 步，表格填不满（建议 8-14 步）")
            for st in steps:
                if not isinstance(st.get("r"), int) or not isinstance(st.get("c"), int):
                    bad.append(f"{tag} step 缺 r/c：{str(st)[:40]}…")
                elif not (0 <= st["r"] < len(rows)) or not (0 <= st["c"] < len(cols)):
                    bad.append(f"{tag} step 的 r/c 越界：r={st['r']} c={st['c']}")
                if not (st.get("vals") or {}):
                    bad.append(f"{tag} step 缺 vals：{str(st)[:40]}…")
                for f in st.get("from") or []:
                    if (not isinstance(f, list) or len(f) != 2
                            or not (0 <= f[0] < len(rows)) or not (0 <= f[1] < len(cols))):
                        bad.append(f"{tag} from 的坐标越界：{f}")
        if sc.get("type") == "stack":
            frames = sc.get("frames", [])
            if not (3 <= len(frames) <= 8):
                bad.append(f"{tag} frames 应为 3-8 帧，现在 {len(frames)}")
            steps = sc.get("steps", [])
            if len(steps) < 3:
                warn.append(f"{tag} 只有 {len(steps)} 步（建议 5-10 步）")
            for st in steps:
                d = st.get("d")
                if not isinstance(d, int) or not (0 <= d < len(frames)):
                    bad.append(f"{tag} step 的 d 越界：{d}")
        if sc.get("type") == "tree":
            nodes = sc.get("nodes", [])
            if not (2 <= len(nodes) <= 15):
                bad.append(f"{tag} nodes 应为 2-15 个，现在 {len(nodes)}")
            ids = [n.get("id") for n in nodes]
            if len(set(ids)) != len(ids):
                bad.append(f"{tag} 节点 id 有重复")
            for n in nodes:
                if n.get("p") is not None and n["p"] not in ids:
                    bad.append(f"{tag} 节点的父指针指向不存在的节点：{n.get('p')}")
            by_id = {x.get("id"): x for x in nodes}
            levels = {}
            for n in nodes:
                d, p, guard = 0, n.get("p"), 0
                while p is not None and guard < 20:
                    d += 1
                    p = by_id.get(p, {}).get("p")
                    guard += 1
                if guard >= 20:
                    bad.append(f"{tag} 父指针成环：{n.get('id')}")
                levels[n.get("id")] = d
            if max(levels.values(), default=0) + 1 > 4:
                bad.append(f"{tag} 树有 {max(levels.values())+1} 层，超过 4 层（画面放不下）")
            for st in sc.get("steps", []):
                for key in ("open", "prune"):
                    for nid in st.get(key) or []:
                        if nid not in ids:
                            bad.append(f"{tag} {key} 里有不存在的节点：{nid}")
        if sc.get("type") == "graph":
            nodes, edges = sc.get("nodes", []), sc.get("edges", [])
            if not (2 <= len(nodes) <= 10):
                bad.append(f"{tag} nodes 应为 2-10 个，现在 {len(nodes)}")
            ids = [n.get("id") for n in nodes]
            for n in nodes:
                if not isinstance(n.get("x"), (int, float)) or not isinstance(n.get("y"), (int, float)):
                    bad.append(f"{tag} 节点缺 x/y：{n.get('id')}")
                elif not (0 <= n["x"] <= 100) or not (0 <= n["y"] <= 100):
                    bad.append(f"{tag} 节点 x/y 超出 0-100：{n.get('id')}")
            for e in edges:
                if len(e) != 2 or e[0] not in ids or e[1] not in ids:
                    bad.append(f"{tag} 边指向不存在的节点：{e}")
            for st in sc.get("steps", []):
                for nid in st.get("visit") or []:
                    if nid not in ids:
                        bad.append(f"{tag} visit 里有不存在的节点：{nid}")
                if st.get("cur") is not None and st["cur"] not in ids:
                    bad.append(f"{tag} cur 不是已定义的节点：{st['cur']}")
                if len(st.get("queue") or []) > 8:
                    bad.append(f"{tag} queue 超过 8 项")
        if sc.get("type") == "groups":
            for st in sc.get("steps", []):
                gs = st.get("groups") or []
                if not (2 <= len(gs) <= 6):
                    bad.append(f"{tag} 每一步的 groups 应为 2-6 个，现在 {len(gs)}")
                for ix in (st.get("hi") or []) + (st.get("merge") or []):
                    if not isinstance(ix, int) or not (0 <= ix < len(gs)):
                        bad.append(f"{tag} hi/merge 的下标越界：{ix}")
        if sc.get("type") in ("grid", "stack", "tree", "graph", "groups") and sc.get("takeaway") \
                and chars(sc["takeaway"]) > 24:
            warn.append(f"{tag} takeaway 偏长（会挤在读数行）：{sc['takeaway'][:20]}…")

        if sc.get("type") == "flow":
            nodes = sc.get("nodes", [])
            if not (2 <= len(nodes) <= 4):
                bad.append(f"{tag} nodes 应为 2-4 个，现在 {len(nodes)}")
            for st in sc.get("steps", []):
                if not isinstance(st.get("i"), int):
                    bad.append(f"{tag} flow step 缺 i：{str(st)[:40]}…")
        # cue 必须原样出现在同一幕旁白里
        for key, val in _cues(sc):
            if re.sub(r"\s", "", val) not in re.sub(r"\s", "", narr):
                bad.append(f"{tag} cue {val!r} 没有出现在旁白里（该元素永远不会出现）")

    if not (scenes_min <= len(scenes) <= scenes_max):
        warn.append(f"幕数 {len(scenes)}（建议 {scenes_min}-{scenes_max}）")
    if viz < viz_min and (light or viz_min != VIZ_MIN):
        bad.append(f"可视化幕只有 {viz} 幕，要求至少 {viz_min} 幕（array/grid/stack/tree/graph/groups/flow）")
    if not (total_min <= total <= total_max):
        bad.append(f"旁白总字数 {total}（要求 {total_min}-{total_max}，约 5.8 字/秒 → {total/5.8/60:.1f} 分钟）")

    print(f"《{script.get('episode')}》 幕数 {len(scenes)}  可视化 {viz} 幕  旁白 {total} 字  ≈ {total/5.8/60:.1f} 分钟")
    for w in warn:
        print("  ~ " + w)
    for b in bad:
        print("  ! " + b)
    if not bad:
        print("  自检通过")
    return 1 if bad else 0


def _cues(node, out=None):
    """收集所有 <名>_cue / cue 的值。"""
    out = [] if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and (k == "cue" or k.endswith("_cue")):
                out.append((k, v))
            else:
                _cues(v, out)
    elif isinstance(node, list):
        for v in node:
            _cues(v, out)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
