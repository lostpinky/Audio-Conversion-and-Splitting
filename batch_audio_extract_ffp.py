
#!/usr/bin/env python3
"""batch_audio_extract_ffp.py

Convert every .m4s and .mp4 inside a folder to .m4a audio using the
ffmpeg‑python wrapper (https://github.com/kkroening/ffmpeg‑python).

Usage:
    python batch_audio_extract_ffp.py /path/to/folder [-r]

Options:
    -r, --recursive     Search sub‑folders recursively.

Dependencies:
    pip install ffmpeg-python
    System ffmpeg binary must be accessible via PATH.
"""

import argparse, shutil, sys
from pathlib import Path
import ffmpeg

def ffmpeg_binary_ok() -> bool:
    return shutil.which('ffmpeg') is not None

def copy_aac(src: Path, dst: Path) -> None:
    """Copy existing AAC/Audio bitstream without re‑encoding."""
    (
        ffmpeg
        .input(str(src))
        .output(str(dst), **{'c:a': 'copy'}, vn=None, loglevel='error')
        .run(overwrite_output=True)
    )

def reencode_aac(src: Path, dst: Path) -> None:
    """Fallback: re‑encode to 192 k AAC when stream copy fails."""
    (
        ffmpeg
        .input(str(src))
        .output(
            str(dst),
            **{
                'vn': None,
                'c:a': 'aac',
                'b:a': '192k'
            },
            loglevel='error'
        )
        .run(overwrite_output=True)
    )

def process_one(src: Path) -> None:
    dst = src.with_suffix('.m4a')
    try:
        if src.suffix.lower() == '.m4s':
            # .m4s assumed audio‑only, just copy
            copy_aac(src, dst)
        else:  # .mp4
            copy_aac(src, dst)
    except ffmpeg.Error:
        if src.suffix.lower() == '.mp4':
            # Try re‑encode when copy fails
            reencode_aac(src, dst)
        else:
            raise

def main() -> None:
    ap = argparse.ArgumentParser(description='Batch convert .m4s/.mp4 to .m4a with ffmpeg‑python.')
    ap.add_argument('folder', type=Path, help='Target directory')
    ap.add_argument('-r', '--recursive', action='store_true', help='Recurse into sub‑dirs')
    args = ap.parse_args()

    if not ffmpeg_binary_ok():
        sys.exit('ffmpeg executable not found in PATH.')

    folder: Path = args.folder.expanduser().resolve()
    if not folder.is_dir():
        sys.exit(f'{folder} is not a directory.')

    pattern = '**/*' if args.recursive else '*'
    targets = [p for p in folder.glob(pattern) if p.suffix.lower() in ('.m4s', '.mp4')]

    if not targets:
        print('No .m4s or .mp4 files detected.')
        return

    for f in targets:
        print(f'Processing {f.name} ...', end=' ', flush=True)
        try:
            process_one(f)
            print('OK')
        except Exception as e:
            print('FAILED')
            print(f'  ↳ {e}')

if __name__ == '__main__':
    main()
