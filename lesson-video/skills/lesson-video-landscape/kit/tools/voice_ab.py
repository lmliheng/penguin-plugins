"""同一段旁白，多个候选音色，各出一份「试听小样」——用来挑配音。

产出的每组文件都取自同一段文字、同一个语速，唯一变量就是音色：

  <out>/<标签>.mp3          每个音色一段完整小样（默认 30 秒，在词边界上收尾）
  <out>/对比-<clip>秒.mp3    每个音色取开头 clip 秒，首尾相接，一次听完

用法:
  python tools/voice_ab.py --text-file lessons/demo-window/ab-text.txt \
      --out lessons/demo-window/out/voice-ab --rate +18% \
      --voice "A-云健=zh-CN-YunjianNeural" \
      --voice "B-云扬=zh-CN-YunyangNeural" \
      --voice "C-云希=zh-CN-YunxiNeural"
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.tts import FFMPEG, synth_retry, to_wav, wav_duration  # noqa: E402

# 与 lib/build.py 成片时用的响度一致，试听听到的就是最终音量
NORM = "loudnorm=I=-14:TP=-1.5:LRA=11"


def run(*args: str) -> None:
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def cut_on_word(wav: Path, words: list[dict], limit: float, out: Path) -> float:
    """在不超过 limit 的最后一个词尾收尾，留一点呼吸，避免把字切掉。"""
    ends = [w["start"] + w["dur"] for w in words if w["start"] + w["dur"] <= limit]
    end = (max(ends) if ends else limit) + 0.12
    run("-i", str(wav), "-t", f"{end:.3f}",
        "-af", f"afade=t=out:st={max(0.0, end - 0.15):.3f}:d=0.15,{NORM}",
        "-ar", "48000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(out))
    return end


def clip_head(wav: Path, clip: float, out: Path) -> float:
    """取开头 clip 秒，尾部淡出，几段之间听起来互不粘连。"""
    run("-i", str(wav), "-t", f"{clip:.3f}",
        "-af", f"afade=t=out:st={max(0.0, clip - 0.15):.3f}:d=0.15,{NORM}",
        "-ar", "48000", "-ac", "1", str(out))
    return clip


def silence(path: Path, seconds: float) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000)
        w.writeframes(b"\x00" * int(48000 * 2 * seconds))


def concat(parts: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in parts) + "\n", encoding="utf-8")
    run("-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:a", "libmp3lame", "-b:a", "128k", str(out))
    lst.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", action="append", required=True,
                    help='每个音色写一次，形如 "标签=zh-CN-YunxiNeural"')
    ap.add_argument("--rate", default="+18%")
    ap.add_argument("--seconds", type=float, default=30.0, help="每个音色的小样长度上限")
    ap.add_argument("--clip", type=float, default=10.0, help="对比文件里每个音色取多长")
    args = ap.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8").strip().replace("\n", "")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_tmp"
    tmp.mkdir(exist_ok=True)

    rows, clips = [], []
    for spec in args.voice:
        label, _, rest = spec.partition("=")
        label, rest = label.strip(), rest.strip() or label.strip()
        voice, _, rate = rest.partition("@")      # "标签=音色@语速"，不写语速就用 --rate
        voice, rate = voice.strip(), rate.strip() or args.rate
        wav = tmp / f"{label}.wav"
        words = synth_retry(text, voice, rate, tmp / f"{label}.mp3")
        to_wav(tmp / f"{label}.mp3", wav)

        full = out_dir / f"{label}.mp3"
        dur = cut_on_word(wav, words, args.seconds, full)
        rows.append((label, f"{voice} {rate}", dur, wav_duration(wav)))

        c = tmp / f"{label}-clip.wav"
        clips.append(c)
        clip_head(wav, args.clip, c)

    gap = tmp / "_gap.wav"
    silence(gap, 0.35)
    sep: list[Path] = []
    for c in clips:
        sep += [c, gap]
    joined = out_dir / f"compare-{int(args.clip)}s-x{len(clips)}.mp3"
    concat(sep[:-1], joined)

    print(f"\n对比文件 -> {joined}")
    for label, voice, dur, raw in rows:
        print(f"  {label:<10} {voice:<28} 小样 {dur:5.2f}s  (原声 {raw:5.2f}s)")
    print(f"\n小样目录 -> {out_dir}   [文本 {len(text)} 字，语速 {args.rate}]")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
