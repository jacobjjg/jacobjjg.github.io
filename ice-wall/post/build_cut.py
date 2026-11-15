"""Cut the three ElevenLabs/Seedance ice-wall shots into one silent clip with the grainy film finish.

Usage: VIDEO=dir python build_cut.py OUT.mp4
VIDEO must hold wide.mp4, ots.mp4 and ext.mp4 (the three Seedance 2.5 generations in the ElevenLabs flow).
"""
import os
import subprocess
import sys

V = os.environ.get("VIDEO", "media/video")
OUT = sys.argv[1] if len(sys.argv) > 1 else "ice_wall_cinematic.mp4"

SEG = [  # (file, in, out, letterbox ratio)
    ("wide.mp4", 0.0, 5.5, 2.39),   # crew on the bridge staring out (Veo 3.1 retry)
    ("ots.mp4", 0.0, 5.0, 2.39),    # over the officer's shoulder toward the entrance
    ("ext.mp4", 0.0, 6.0, 1.90),    # the reveal: the ship dwarfed by the wall (frame opens up, IMAX style)
]
SEG = [sg for sg in SEG if os.path.exists(os.path.join(V, sg[0]))]   # cut whatever shots are present
HOLD = 0.8
TOTAL = sum(b - a for _, a, b, _ in SEG) + HOLD

GRADE = ("eq=contrast=1.02:saturation=0.96,"
         "colorbalance=rs=-0.015:bs=0.015:rh=0.015:bh=-0.012,"
         "curves=all='0/0.012 0.5/0.5 1/0.985'")
WEAVE = ("crop=w=iw-8:h=ih-8:x=4+1.4*sin(t*2.1)+0.6*sin(t*6.7):y=4+1.1*sin(t*1.6)+0.5*sin(t*5.9),"
         "scale=1920:1080:flags=bicubic")
GRAIN = "noise=c0s=14:c0f=t+u:c1s=5:c1f=t+u:c2s=5:c2f=t+u"
VIG = "vignette=angle=PI/5.5"


def letterbox(r):
    h = int(round(1920 / r / 2)) * 2
    y = (1080 - h) // 2
    return f"crop=1920:{h}:0:{y},pad=1920:1080:0:{y}:black"


fc = []
for i, (_, a, b, r) in enumerate(SEG):
    tp = f",tpad=stop_mode=clone:stop_duration={HOLD}" if i == len(SEG) - 1 else ""
    fc.append(f"[{i}:v]trim=start={a}:end={b},setpts=PTS-STARTPTS{tp},scale=1920:1080:flags=bicubic,fps=24,"
              f"{GRADE},split[s{i}a][s{i}b]")
    fc.append(f"[s{i}b]curves=all='0/0 0.74/0 1/1',gblur=sigma=14,colorchannelmixer=rr=1.0:gg=0.35:bb=0.12[h{i}]")
    fc.append(f"[s{i}a][h{i}]blend=all_mode=screen:all_opacity=0.18,{WEAVE},{GRAIN},{VIG},{letterbox(r)},setsar=1[v{i}]")
fc.append("".join(f"[v{i}]" for i in range(len(SEG))) +
          f"concat=n={len(SEG)}:v=1:a=0,fade=t=in:st=0:d=0.8,fade=t=out:st={TOTAL - 1.2:.2f}:d=1.2,format=yuv420p[vout]")

cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for f, *_ in SEG:
    cmd += ["-i", os.path.join(V, f)]
cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-an",
        "-c:v", "libx264", "-b:v", "19M", "-maxrate", "26M", "-bufsize", "38M", "-preset", "slow", "-tune", "grain",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", f"{TOTAL}", OUT]
print("cut:", " | ".join(f[:-4] for f, *_ in SEG), f"| {TOTAL:.1f}s silent")
sys.exit(subprocess.run(cmd).returncode)
