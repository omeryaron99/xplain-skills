# Prompt anatomy, in full

The four blocks from SKILL.md, expanded, with a complete worked example at the
end.

---

## Block 1 — Asset bindings

Only present when references are uploaded. One line per asset, numbered by
upload order, saying what the asset is a reference **for**.

```
Image 1: subject appearance reference, the man.
Image 2: vehicle reference, the red Ferrari.
Image 3: environment, lighting and color-grade reference.
Video 1: camera movement and motion reference only. Do not reference its
         visual content.
Audio 1: the man's voice timbre.
```

Patterns worth copying verbatim:

- `The knight in Image 1`
- `Images 1-2 are Character 1 and correspond to Audio 1; Images 3-4 are Character 2 and correspond to Audio 2.`
- `Image 1 depicts the protagonist and uses the voice timbre from Audio 1.`
- `Refer to the spell-casting action in Video 1 and the orbiting camera move in Video 2.`
- `Refer to Image 1 for lighting and filters.`
- `Image 3 is the first frame, and Image 5 is the last frame.`
- `Use Images 1 to 7 in order as keyframes.`

When the reference is accurate, do not re-describe it. `Strictly follow the
actions and camera movement in Video 1, keeping the same order` outperforms a
paragraph re-narrating each gesture, because the paragraph competes with the
reference.

---

## Block 2 — One-sentence summary

The formula:

```
Subject + Location + Event + Genre/Style + Camera movement
```

It gives the model the shape of the whole thing before the details arrive.
Everything downstream should be consistent with it. Contradictions here are the
most common cause of a result that feels like two different videos glued
together.

---

## Block 3 — Beat-by-beat plot

Two formats, both supported. Pick one and stay in it.

**Timestamps** (new in 2.5, ignored by 2.0):

```
0-3s: ...
3-8s: ...
8-15s: ...
```
or
```
[1s-4s] ... [4s-8s] ... [8s-12s]
```

**Shot numbers** (works in both versions):

```
Shot 1: [Wide shot, locked-off camera, eye level] ...
Shot 2: [Medium shot, over the shoulder] ...
```

Per beat, cover:

| Slot | Example |
| --- | --- |
| Shot size | medium close-up |
| Camera move | slow push in |
| Angle / composition | low angle, rule of thirds |
| Subject action | he shifts gear and glances at the mirror |
| Dialogue | Dialogue (man): "Not tonight." |
| Sound | the engine note climbs |

Timing rules:

- Whole-second boundaries, continuous, no gaps.
- One clear action per 3 to 5 seconds. A beat with dialogue needs at least 3.
- Sparse beat → the model invents. Overstuffed beat → extra cuts or dropped
  content.
- No high-frequency timing ("three times per second").
- Point-in-time control works: `At the 2-second mark, a burst of golden
  lightning descends from the top of the frame.`
- Relative time works: `After 3 seconds, everyone around him shakes their head.`

A 30-second video comfortably holds 6 to 9 beats. Nine shots in thirty seconds
is about the ceiling before it starts feeling like a trailer.

---

## Block 4 — Overall requirements

Anything that must hold across the whole video. Group it:

**Visual style.** Reference a real look rather than an adjective. "Shot on Arri
Alexa Mini LF, 35mm cinema lens, cinematic realistic lighting, film grain,
authentic skin texture, no excessive beautification or skin smoothing" gives a
far more specific result than "high quality, beautiful".

**Camera.** Handheld with breathing shake, shallow depth of field, wide
aperture, slight Dutch angle, continuous and smooth movement, one-shot flow.

**Light and color.** Direction, source, and contrast. "Warm golden sunset light
from the upper left against cool twilight blue, strong contrast."

**Audio.** `Environmental and action sounds only, no BGM.` or `Cinematic
orchestral score synchronized to the action beats.` Say it explicitly, silence
here means the model chooses.

**Consistency.** The one nobody writes and everybody needs: "The character's
appearance must strictly follow Image 1, remain consistent throughout, and must
not drift or change identity. Stable motion, no flickering, no stuttering."

**Subtitles.** `No subtitles.` unless you want them. The model adds them
otherwise more often than you would like.

---

## Vocabulary lists

**Shot size:** extreme wide, wide, medium wide, medium, medium close-up,
close-up, extreme close-up, insert.

**Camera movement:** push in, pull out, pan left/right, tilt up/down, track,
follow, side-follow, orbit, arc, crane up, dive, pull back, handheld shake,
locked-off, whip pan.

**Angle:** low angle, ultra-low near the ground, eye level, high angle,
overhead, bird's eye, over-the-shoulder, first-person / POV, Dutch angle.

**Composition:** rule of thirds, central composition, diagonal composition,
symmetrical, foreground framing, negative space.

**Technique:** one-shot / long take, dolly zoom (Hitchcock zoom), rack focus,
speed ramp, bullet time, FPV, aerial, macro, slow motion, freeze frame.

**Lighting:** natural daylight, golden hour, blue hour, practical neon, hard
key with deep shadow, soft diffused, backlit rim light, dappled light through
trees, lens flare, volumetric haze.

**Texture and grade:** film grain, 35mm color film look, IMAX large-format
feel, shallow depth of field, cinematic color grading, realistic skin pores,
cool metallic reflections, subtle atmospheric fog.

**Transitions:** cut, match cut, wipe left/right, dissolve, whip pan
transition, camera-move transition (fly up, turn back, dive down into the next
scene).

---

## Worked example

A 15-second vertical Reel. References: a photo of the man (Image 1), a photo of
the car (Image 2), a photo of the street (Image 3).

```
Image 1: subject appearance reference, the man.
Image 2: vehicle reference, the red Ferrari.
Image 3: environment reference, the street, plus lighting and color grade.

A man drives a red Ferrari through a rain-slicked city street at night,
cinematic realistic short-film style, tracking side shot.

0-4s: [Wide tracking shot, low angle, camera moving alongside the car]
The red Ferrari from Image 2 pulls out of a side street into the wet
main road from Image 3. Neon signs reflect off the asphalt. The engine
growl rises under the rain.

4-9s: [Medium shot through the open driver's window, slight handheld feel]
The man from Image 1 keeps both hands on the wheel, glances once at the
side mirror, and looks back at the road.
Dialogue (man): "Not tonight."

9-15s: [Close-up on the gear shift, rack focus to his face, then a slow
push in] He shifts up. The engine note climbs and the streetlights streak
past behind him. The frame settles on his face and holds.

Overall requirements: Cinematic realistic style, 35mm cinema lens, shallow
depth of field, practical neon lighting against deep night blue, fine film
grain, authentic skin texture with no over-smoothing. The man's face must
strictly follow Image 1 and stay consistent throughout with no identity
drift. Camera movement smooth and continuous, no stuttering or flickering.
Engine, tyre and rain sound only, no background music. No subtitles.
9:16 vertical frame.
```

Settings: 9:16, 720p, 15 seconds, high bitrate on, audio on. Upscale 2x after.
