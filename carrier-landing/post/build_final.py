"""Cut the three ElevenLabs/Veo shots into the final clip, add the film finish and mix the ElevenLabs audio."""
import subprocess
import sys

# Usage: python build_final.py OUT.mp4 [master_gain_db]   (the final used -4.0)
# MEDIA must hold video/shotA.mp4, video/shotB.mp4, video/shotC.mp4 (the three Veo 3.1 generations)
# and audio/{music_1,wind_1,jet_1,buffet_2,jet_3,slam_4,cable_2,spool_1}.mp3 (the picked ElevenLabs takes),
# all downloadable from the ElevenLabs flow.
import os
MEDIA = os.environ.get("MEDIA", "media")
V = f"{MEDIA}/video"
A = f"{MEDIA}/audio"
OUT = sys.argv[1] if len(sys.argv) > 1 else "final.mp4"

# ---- edit decision list (seconds) ----
SEG = [  # (input index, in, out, letterbox ratio)
    (0, 0.0, 2.6, 2.39),   # A  helicopter chase
    (1, 0.0, 4.0, 2.39),   # B  spine-mounted cam
    (2, 0.0, 2.3, 1.90),   # C1 deck level: approach + touchdown   (aspect opens up, IMAX style)
    (2, 4.2, 8.0, 1.90),   # C2 jet decelerates and stops
]
HOLD = 1.3                 # hold the final frame while the score rings out
T_C1 = 2.6 + 4.0
TD = T_C1 + 1.50           # touchdown in the cut = 8.10 s
T_C2 = T_C1 + 2.3          # 8.90 s
TOTAL = T_C2 + 3.8 + HOLD  # 14.0 s

# ---- picture finish ----
GRADE = ("eq=contrast=1.05:saturation=0.9:gamma=0.98,"
         "colorbalance=rs=-0.03:bs=0.035:rh=0.03:gh=0.01:bh=-0.025,"
         "curves=all='0/0.02 0.12/0.095 0.5/0.49 0.86/0.87 1/0.97'")
WEAVE = ("crop=w=iw-8:h=ih-8:x=4+1.4*sin(t*2.1)+0.6*sin(t*6.7):y=4+1.1*sin(t*1.6)+0.5*sin(t*5.9),"
         "scale=1920:1080:flags=bicubic")
GRAIN = "noise=c0s=8:c0f=t+u:c1s=3:c1f=t+u:c2s=3:c2f=t+u"
VIG = "vignette=angle=PI/5.5"


def letterbox(r):
    h = int(round(1920 / r / 2)) * 2
    y = (1080 - h) // 2
    return f"crop=1920:{h}:0:{y},pad=1920:1080:0:{y}:black"


fc = []
used_c = 0
fc.append("[2:v]split=2[c_a][c_b]")
for i, (idx, a, b, r) in enumerate(SEG):
    src = f"[{idx}:v]" if idx != 2 else ("[c_a]" if used_c == 0 else "[c_b]")
    if idx == 2:
        used_c += 1
    tp = f",tpad=stop_mode=clone:stop_duration={HOLD}" if i == len(SEG) - 1 else ""
    fc.append(f"{src}trim=start={a}:end={b},setpts=PTS-STARTPTS{tp},scale=1920:1080:flags=bicubic,fps=24,"
              f"{GRADE},split[s{i}a][s{i}b]")
    fc.append(f"[s{i}b]curves=all='0/0 0.74/0 1/1',gblur=sigma=14,"
              f"colorchannelmixer=rr=1.0:gg=0.35:bb=0.12[h{i}]")
    fc.append(f"[s{i}a][h{i}]blend=all_mode=screen:all_opacity=0.25,{WEAVE},{GRAIN},{VIG},{letterbox(r)},"
              f"setsar=1[v{i}]")
fc.append("".join(f"[v{i}]" for i in range(len(SEG))) +
          f"concat=n={len(SEG)}:v=1:a=0,fade=t=in:st=0:d=0.6,fade=t=out:st={TOTAL - 1.1:.2f}:d=1.1,format=yuv420p[vout]")

# ---- sound: ElevenLabs score + SFX layers ----
def place(label, idx, start, gain_db, trim_from=0.0, length=None, fin=0.0, fout=0.0, extra=""):
    chain = f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={trim_from}"
    if length:
        chain += f":duration={length}"
    chain += ",asetpts=PTS-STARTPTS"
    if fin:
        chain += f",afade=t=in:st=0:d={fin}"
    if fout and length:
        chain += f",afade=t=out:st={length - fout:.3f}:d={fout}"
    chain += f",volume={gain_db}dB{extra}"
    ms = int(round(start * 1000))
    chain += f",adelay=delays={ms}:all=1[{label}]"
    fc.append(chain)
    return f"[{label}]"


MUSIC_HIT = 11.725
MASTER_GAIN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
layers = [
    # score: its big hit lands on the touchdown; long tail rings over the stopped jet
    place("mus", 3, 0.0, 4.0, trim_from=MUSIC_HIT - TD, length=TOTAL, fout=1.6),
    # ocean wind bed for the whole clip, ducked under the spine-cam roar
    place("wind", 4, 0.0, -12, length=TOTAL, fin=0.8, fout=1.2,
          extra=f",volume='if(between(t,2.6,6.6),0.35,1)':eval=frame"),
    # shot A: jet roar receding toward the ship
    place("jetA", 5, 0.0, -7, trim_from=0.9, length=3.0, fin=0.4, fout=0.5),
    # shot B: buffeting on the airframe
    place("buf", 6, 2.6, -10, length=4.0, fin=0.03, fout=0.18),
    # shot C1: approach roar peaking just before touchdown
    place("jetC", 7, TD - 1.935 - 0.15, -6, length=4.2, fout=1.2),
    # touchdown slam, hook/cable screech bridging the cut, engines winding down
    place("slam", 8, TD - 0.06 - 0.03, 3.0),
    place("cab", 9, TD + 0.25 - 0.685, -1.0, length=3.0, fout=0.6),
    place("spool", 10, T_C2 + 1.3, -7, length=5.0, fout=1.5),
]
fc.append("".join(layers) + f"amix=inputs={len(layers)}:normalize=0:duration=longest,"
          f"atrim=duration={TOTAL},volume={MASTER_GAIN}dB,alimiter=limit=0.89:attack=2:release=80:level=false,aresample=48000[aout]")

inputs = [f"{V}/shotA.mp4", f"{V}/shotB.mp4", f"{V}/shotC.mp4", f"{A}/music_1.mp3"]
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for p in inputs:
    cmd += ["-i", p]
cmd += ["-stream_loop", "2", "-i", f"{A}/wind_1.mp3"]
for p in ["jet_1", "buffet_2", "jet_3", "slam_4", "cable_2", "spool_1"]:
    cmd += ["-i", f"{A}/{p}.mp3"]
cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-t", f"{TOTAL}", OUT]
print(f"cut: A 0-2.6 | B 2.6-6.6 | C1 6.6-8.9 (touchdown {TD:.2f}) | C2 8.9-12.7 | hold to {TOTAL:.1f}s")
r = subprocess.run(cmd)
sys.exit(r.returncode)
