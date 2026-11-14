# Carrier landing: Blender previz → ElevenLabs cinematic

A rough 3D previz of a navy jet trapping aboard an aircraft carrier, turned into a 14-second
film-look sequence with ElevenLabs (image, video, music and sound effects).

| File | What it is |
|---|---|
| `final/carrier_landing_cinematic.mp4` | **The finished clip.** 1080p24, 16 s, stereo mix |
| `previz/carrier_landing_previz.mp4` | The rough Blender animation (3 shots, 12 s, no audio) |
| `previz/reference_frames/*.jpg` | 1080p screenshots from the previz, used as references in ElevenLabs |
| `elevenlabs/film_frame_*.jpg` | The restyled film frames used as video start/end frames |
| `elevenlabs/previz_vs_film_frames.jpg` | Side-by-side: previz screenshot vs. film frame |
| `blender/carrier_landing.py` | Scene, animation and render script (Blender 5.x, Cycles) |
| `blender/carrier_landing.blend` | The saved scene; open it and press F12 / Ctrl+F12 |
| `post/build_final.py` | The edit, film finish and audio mix (ffmpeg) |

ElevenLabs flow with every node and generation:
https://elevenlabs.io/app/flows/1X1eIUi99FMNSI2tdbne

## Pipeline

1. **Previz (Blender 5.3, Cycles CPU).** A procedurally built carrier with an angled deck, island,
   four arresting wires and landing lights. A generic twin-tail navy jet with gear and tailhook.
   An animated ocean with wake, a low-sun sky with a cloud deck, and aerial haze. The motion is
   physically timed: a 3.5° glide slope at 65 m/s, touchdown, the hook rides the deck and catches
   the 3-wire, then a 2.4 s arrestment and a small roll-back. The wire is pulled into a V. Three
   cameras: a helicopter chase (45 mm), a spine-mounted camera over the canopy (22 mm) and a
   deck-level operator (40 mm).
2. **Reference frames.** Seven 1080p screenshots of the animation, attached to an ElevenLabs flow.
3. **Film frames (Nano Banana Pro, 2K).** The shot C end frame was restyled first and became the
   look reference. Each start frame was then restyled from two references: its previz screenshot,
   for composition, and that look frame, for aircraft design and grade.
4. **Video (Seedance 2.5, 1080p, audio off).** Each shot starts from its approved film frame.
   All three frames came from the same hero look reference, which keeps the jet, carrier and
   grade consistent across shots.
   - Shot A: helicopter chase, 5 s.
   - Shot B: spine cam, 4 s.
   - Shot C: the trap, 8 s, as one continuous take.

   A first pass with Veo 3.1 used start and end frames for shot C. Veo made the jet pitch up and
   roll off the deck to reach the end pose, so the shots were redone in Seedance without end frames.
5. **Sound (ElevenLabs).** The score is from Music v2.5: a ticking pulse, an organ drone and
   rising strings that build to one huge hit. Six SFX layers come from Sound Effects v2: ocean wind
   bed, jet approach, airframe buffeting, touchdown slam, arresting cable and engine spool-down.
6. **Edit and finish (ffmpeg).**
   - The cut is A 0–3.8 s, B 3.8–7.8 s and C 7.8–15.0 s, then the last frame is held to 16 s.
   - The score's hit is synced to the touchdown at 9.32 s.
   - The finish adds visible film grain, a light grade, halation, gate weave and vignette.
   - The aspect ratio opens from 2.39:1 to 1.90:1 on the deck shot, like an IMAX cut.
   - The master is about −13 LUFS with a −1 dBTP peak.

## Re-rendering the previz

```bash
pip install bpy==5.3.0        # or run inside Blender 5.x with: blender -b -P carrier_landing.py -- ...
python blender/carrier_landing.py --shot all --res 960x540 --samples 16 --out renders
python blender/carrier_landing.py --frames 1,100,170,288 --res 1920x1080 --samples 64 --out stills
```

In `carrier_landing.blend`, timeline markers switch between the three cameras, so Ctrl+F12
renders the whole edit. Leave Cycles' *Persistent Data* off. On Blender 5.3 with the animated
ocean, it made the sea render black after about 8 frames, so the script only enables it with
`--persistent`.
