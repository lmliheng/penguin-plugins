"""把 script.json 摊成能读的讲稿（幕型 / 标题 / 旁白 / 要点 / 代码），给用户看内容用。

用法: python tools/dump_script.py lessons/ep05-window-prefix [lessons/ep06-dp ...] --out 第二季讲稿.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def render(d: Path) -> str:
    s = json.loads((d / "script.json").read_text(encoding="utf-8"))
    total = sum(len(re.sub(r"\s", "", sc.get("narration", ""))) for sc in s["scenes"])
    lines = [f"# {s['episode']}", "",
             f"- id：`{s['id']}`　幕数 {len(s['scenes'])}　旁白 {total} 字（约 {total/5.8/60:.1f} 分钟）",
             f"- 音色 {s['voice']}　语速 {s['rate']}　版式 {s.get('deck', 'deck.html')}", ""]
    for i, sc in enumerate(s["scenes"], 1):
        t = sc["type"]
        head = f"### {i:02d} · {t}　{sc.get('title') or sc.get('kicker','')}"
        lines.append(head)
        if t == "title":
            lines.append(f"- {sc.get('sub','')}　标签：{' / '.join(sc.get('tags', []))}")
        if t == "points":
            lines += [f"- {x}" for x in sc.get("items", [])]
            if sc.get("takeaway"):
                lines.append(f"- 结论：{sc['takeaway']}")
        if t in ("code",):
            lines.append("```python")
            lines += sc.get("code", "").split("\n")
            lines.append("```")
        if t == "array":
            lines.append(f"- 数组 {sc.get('values')}　步数 {len(sc.get('steps', []))}"
                         + (f"　目标 {sc['target']}" if "target" in sc else ""))
        if t == "grid":
            lines.append(f"- 表格 {len(sc.get('rows', []))}×{len(sc.get('cols', []))}　步数 {len(sc.get('steps', []))}")
        if t == "stack":
            lines.append(f"- 栈 {len(sc.get('frames', []))} 层　步数 {len(sc.get('steps', []))}")
        if t == "tree":
            lines.append(f"- 决策树 {len(sc.get('nodes', []))} 个节点　步数 {len(sc.get('steps', []))}")
        if t == "graph":
            lines.append(f"- 图 {len(sc.get('nodes', []))} 点 {len(sc.get('edges', []))} 边　步数 {len(sc.get('steps', []))}")
        if t == "groups":
            lines.append(f"- 集合合并　步数 {len(sc.get('steps', []))}")
        if t == "flow":
            lines.append("- 流程：" + " → ".join(n.get("t", "") for n in sc.get("nodes", [])))
        if sc.get("takeaway"):
            lines.append(f"- 结论：{sc['takeaway']}")
        lines += ["", "**旁白**", "", sc.get("narration", ""), ""]
    return "\n".join(lines)


def main() -> None:
    argv = sys.argv[1:]
    out = Path("第二季讲稿.md")
    dirs: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--out":
            out = Path(argv[i + 1]); i += 2; continue
        dirs.append(argv[i]); i += 1
    parts = [render((ROOT / a).resolve()) for a in dirs]
    out.write_text("\n\n---\n\n".join(parts), encoding="utf-8")
    print(f"OK {out}  ({out.stat().st_size} 字节)")


if __name__ == "__main__":
    main()
