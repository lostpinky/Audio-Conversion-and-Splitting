#!/usr/bin/env python3
"""
clip_audio.py  ——  Lossless audio trimming with ffmpeg-python
--------------------------------------------------------------
用法:
    python clip_audio.py input.m4a 00:01:30 00:02:45 output.m4a
    python clip_audio.py input.flac 45 75 out.flac          # 秒数
    python clip_audio.py -h                                 # 查看帮助

依赖:
    pip install ffmpeg-python
    系统已安装 ffmpeg (ffmpeg -version 能输出版本)
"""

import argparse
import re
import shutil
import sys
import ffmpeg
from pathlib import Path
from datetime import timedelta

TIME_PAT = re.compile(r"^(?:(\d+):)?(?:(\d{1,2}):)?(\d{1,2})(\.\d+)?$")

def str_to_seconds(timestr: str) -> float:
    """支持 hh:mm:ss(.xxx) / mm:ss(.xxx) / ss(.xxx) ——> 秒(float)"""
    if timestr.isdigit() or re.fullmatch(r"\d+\.\d+", timestr):
        return float(timestr)          # 纯秒数
    m = TIME_PAT.match(timestr)
    if not m:
        raise ValueError(f"非法时间格式: {timestr}")
    h, mnt, s, frac = m.groups()
    h = int(h or 0)
    mnt = int(mnt or 0)
    s = int(s)
    frac = float(frac or 0)
    return h * 3600 + mnt * 60 + s + frac

def human(seconds: float) -> str:
    return str(timedelta(seconds=seconds)).lstrip("0:")

def main() -> None:
    ap = argparse.ArgumentParser(
        description="使用 ffmpeg 无损裁剪音频"
    )
    ap.add_argument("infile", help="输入音频文件")
    ap.add_argument("start",  help="起始时间 (HH:MM:SS / MM:SS / 秒)")
    ap.add_argument("end"  ,  help="结束时间 (同格式)")
    ap.add_argument("outfile", help="输出文件 (建议 .m4a / .flac 等)")
    args = ap.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("❌  系统找不到 ffmpeg，可执行文件未写入 PATH")

    start_sec = str_to_seconds(args.start)
    end_sec   = str_to_seconds(args.end)
    if end_sec <= start_sec:
        sys.exit("❌  结束时间必须大于开始时间")

    duration = end_sec - start_sec
    print(f"⚙️  裁剪区间: {human(start_sec)}  →  {human(end_sec)} ({duration:.3f}s)")

    try:
        (
            ffmpeg
            .input(args.infile, ss=start_sec)
            .output(
                args.outfile,
                **{"c": "copy"},    # = -c copy
                t=duration          # 输出时长
            )
            .overwrite_output()
            .global_args("-loglevel", "error")
            .run()
        )
        print("✅ 裁剪完成:", Path(args.outfile).resolve())
    except ffmpeg.Error as e:
        print("❌  ffmpeg 运行出错：", e.stderr.decode() if e.stderr else e)
        sys.exit(1)

if __name__ == "__main__":
    main()
