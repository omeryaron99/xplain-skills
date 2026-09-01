---
name: seedance-prompt
description: Write production-grade Seedance 2.5 prompts for AI video (Higgsfield, Dreamina, CapCut, BytePlus ModelArk). Use when the user describes a video they want to generate, asks for a Seedance prompt, mentions Seedance / סידנס / Higgsfield video, or wants to extend, edit, or re-render an existing AI video.
---

# Seedance 2.5 Prompt Engineer

Turn a rough idea ("a guy driving a Ferrari through Tel Aviv at night") into a
structured Seedance 2.5 prompt that the model actually follows.

**Your scope:** the prompt text, the reference-asset mapping, and the settings
to pick in the UI.
**Not your scope:** running the generation, editing the result, writing the
video's script or caption.

Seedance 2.5 is ByteDance's video model. One request generates up to **30
seconds** with native audio, and accepts up to **50 reference assets**
(30 images, 10 videos, 10 audio clips). It follows instructions far more
literally than 2.0, which is why a structured prompt beats a poetic one every
time.

---

## Step 1: Get the four things you need

Never start writing until you have these. If any is missing, ask, then stop and
wait for the answer. Do not guess an answer and continue.

1. **What happens in the video.** Subject, place, event. One sentence is enough
   to start.
2. **How long.** Any integer up to 30 seconds. This decides how many beats fit.
3. **Orientation.** Vertical (9:16) for Reels/TikTok/Shorts, horizontal (16:9)
   for YouTube and ads.
4. **What references they have.** Images of a person, product, or location;
   videos to copy motion from; audio for a voice. If the answer is "none", the
   prompt is text-only and every subject must be described in words instead.

Also worth asking when it is not obvious: **is there speech?** Spoken dialogue
changes the shot list, because a talking beat needs 3 to 5 seconds to land.

---

## Step 2: Bind every reference asset, by number

This is the single highest-leverage thing in a Seedance 2.5 prompt, and the one
people skip.

Assets are numbered **by upload order**: `Image 1`, `Video 1`, `Audio 1`. Bind
each one explicitly in the text, and say *what it is a reference for*.

```
Image 1: the man, subject appearance reference.
Image 2: the red Ferrari, vehicle reference.
Image 3: the street at night, environment, lighting and color reference.
Audio 1: the man's voice timbre.
```

Rules that come straight from the model's behaviour:

- **Never carry the mapping inside the image.** Writing "Omer" on the photo and
  then saying "Omer walks in" causes character confusion or a duplicated person.
  The mapping lives in the text.
- **List multiple subjects one by one.** With several characters, use a list.
  "Images 1-2 are Character 1 and correspond to Audio 1; Images 3-4 are
  Character 2 and correspond to Audio 2."
- **Say which part to reference.** "Refer to Image 1 for lighting and color
  only." "Refer to the camera orbit in Video 1."
- **When the reference is already accurate, stop describing it.** "Strictly
  follow the actions and camera movement in Video 1" beats re-describing every
  hand movement, and re-describing it fights the reference.

Asset limits and sweet spots:

| Thing | Hard limit | Works best |
| --- | --- | --- |
| Images | 30 | 1-8 subjects; 9-12 is possible but less stable |
| Videos | 10, 30s total | subject video/audio refs of 5-10 seconds |
| Audio | 10, 30s total | 1-5 subjects with voice refs |
| Storyboard panels | - | 15 or fewer, line art, no text on the image |
| Video to edit | - | under 20 seconds |

For 1-5 subjects, multi-view reference images are fine. Above 5, prefer
single-view images, one per view, rather than one collage of views.

---

## Step 3: Write the prompt in four blocks

Always this order. It matches how the model reads.

### Block 1 — Asset bindings
Only if there are references. See Step 2.

### Block 2 — One-sentence summary
`Subject + Location + Event + Genre/Style + Camera movement`

> A man drives a red Ferrari through a rain-slicked Tel Aviv street at night,
> cinematic realistic short-film style, tracking side shot.

This sentence anchors everything after it. If the shot list later contradicts
it, the model gets confused, so keep them consistent.

### Block 3 — The beat-by-beat plot

Split the duration into segments, using **either** timestamps **or**
`Shot 1 / Shot 2`. Both work. Timestamps are new in 2.5 and give tighter
control; shot numbers are safer when the pacing is loose.

Each beat gets: shot size, camera move, what the subject does, and any dialogue
or sound.

```
0-4s: [Wide tracking shot, low angle, camera moving alongside the car]
The red Ferrari pulls out of a side street. Wet asphalt reflects the
neon signs. Engine growl rises.

4-9s: [Medium shot through the driver's window, handheld feel]
The man keeps both hands on the wheel and glances at the mirror.
Dialogue (man): "Not tonight."

9-15s: [Close-up on the gear shift, then rack focus to his face]
He shifts up. The engine note climbs and the streetlights streak past.
```

Timestamp rules that matter:

- **Whole seconds only, and no gaps.** `0-3s ... 3-7s ... 7-15s` is right.
  `0-3s ... 5-6s` leaves a hole the model fills however it likes.
- **Too little content in a window** and the model improvises to fill it.
- **Too much content in a window** and you get extra cuts, or the beat is
  dropped entirely. Roughly one clear action per 3 to 5 seconds.
- **Do not time high-frequency actions.** "Shakes his head three times per
  second" will not work.
- Point-in-time and relative time also work: "at the 5-second mark, a quick
  left wipe transition", "the frame freezes for 1 second after he presses the
  shutter".

### Block 4 — Overall requirements

Everything that must hold for the whole video: visual style, camera language,
lighting, grade, audio bed, and consistency demands.

> Cinematic realistic style, shot on a 35mm cinema lens, shallow depth of field,
> practical neon lighting, fine film grain, natural skin texture, no
> over-smoothing. The man's face must stay consistent throughout with no
> identity drift. Engine and rain sound only, no background music. No subtitles.

---

## Step 4: Use positive descriptions, with three exceptions

Describe what you **want**. The model handles positives far better than
prohibitions.

The exceptions, which are officially supported and do work:

- Subtitles: `No subtitles.`
- Music: `No BGM; environmental and action sounds only.`
- Audio entirely: `No audio.`

For anything else you want to avoid, phrase it as a positive. Instead of "not
cartoonish", write "realistic photographic texture, real skin pores, natural
lighting".

The one place a hard exclusion list earns its keep is a strong style lock, and
even then it goes at the very end:

```
Strictly exclude: black and white, desaturated; illustration, line art,
animation; plastic CG, glossy overexposed CG.
```

---

## Step 5: Camera language

Write these terms plainly. The model knows them:

- **Shot size:** extreme wide / wide / medium / medium close-up / close-up /
  extreme close-up
- **Camera movement:** push in / pull out / pan / track / follow / orbit /
  dive / pull back / tilt up / handheld shake
- **Angle:** low angle / overhead / eye level / over-the-shoulder /
  first-person
- **Techniques:** one-shot long take, dolly zoom (Hitchcock zoom), aerial, FPV,
  bullet time, handheld, speed ramp

For anything niche, write **term + plain explanation**:

> Rack focus: the focus shifts smoothly, the foreground trees go soft while the
> character behind them comes sharp.

For a transition, give **both the trigger and the method**:

> At the 5-second mark, a quick leftward wipe combined with a natural dissolve.

**Actions:** describe generally ("they trade a few quick exchanges", "he does a
set of high-knee raises") and only spell out the one or two moments that have to
land. Over-specifying every movement makes the motion stiff.

**Expressions:** plain descriptive sentences. Avoid idioms, they translate badly
into faces.

---

## Step 6: Pick the task type

Seedance 2.5 splits tasks by whether the input **locks** the output's shape.

**Unlocked** (you choose aspect ratio and duration):

- **Reference to video** — images/video/audio as semantic references.
- **Storyboard** — a multi-panel board as a loose plot reference.
- **Keyframes** — separate images the video passes through in order. Open with
  `Use Images 1 to 7 in order as keyframes.` Use this instead of a multi-panel
  storyboard whenever the video must actually match the boards.

**Locked** (the input dictates the output):

| Task | What locks | How to trigger it |
| --- | --- | --- |
| First / last frame | Aspect ratio matches the first-frame image | Set the image role to `first_frame` / `last_frame`, or say "Image 1 is the first frame" |
| Editing | Aspect ratio **and** duration match the source | Use an edit verb: edit, add, insert, remove, delete, modify, replace, change to |
| Extension | Aspect ratio matches the source; you pick the added duration | Use an extend verb: extend forward, extend backward, continue, continue from |

For editing and extension, output **MOV**. It preserves color, brightness and
audio continuity across the seam. MP4 shows the join.

Two more rules for those tasks:

- **Editing:** state the scope and describe the change as **A to B**. "Change
  the man's action from drinking coffee to mopping the floor between 4 and 6
  seconds in Video 1, and leave everything else unchanged."
- **Extension:** volume can shift slightly at the seam. It is smallest when the
  source was itself made by Seedance 2.5.

---

## Step 7: Hand over the settings too

The prompt is half the job. Tell the user what to select:

- **Aspect ratio:** vertical for social, horizontal for YouTube and ads. 2.5
  supports any ratio between 0.4 and 2.5.
- **Resolution:** 720p is the right default. It is fast and cheap, and the
  upscale pass afterwards recovers the detail. Go higher only for a final cut
  you already like.
- **Duration:** up to 30 seconds, matched to how many beats you actually wrote.
- **High bitrate:** on. It is the difference between a clean gradient and a
  blocky one, and it costs nothing but file size.
- **Audio:** on if the prompt asks for dialogue, sound effects or music.
- **After generating:** run the result through video upscaling to double the
  resolution. Generate small, upscale once, at the end.

---

## Output format

Give the user, in this order:

1. **The prompt**, in one copyable fenced block, ready to paste.
2. **The reference list**, numbered in the exact order they must upload.
3. **The settings line**: aspect ratio, resolution, duration, bitrate, audio.
4. **One or two notes** on what to change if the result misses.

Write the prompt itself in **English** even when the conversation is in Hebrew.
The model handles 10+ languages, and Hebrew works, but English prompts are more
predictable, and dialogue can still be written in any language:
`Dialogue (man, in Hebrew): "לא הלילה."`

---

## Failure modes and the fix

| What went wrong | Why | Fix |
| --- | --- | --- |
| Too many cuts | Too much plot per time window | Fewer actions per beat, or a longer video |
| The model improvised a scene you never asked for | A time window with too little in it | Add detail to that beat |
| The face changed mid-video | No consistency instruction | Add "the face must stay consistent throughout, no identity drift" |
| Two of the same character appeared | The mapping was only inside the image | Bind by number in the text |
| The motion looks stiff | Every movement was over-specified | Describe actions generally, detail only the key moments |
| Result ignored the storyboard | Multi-panel boards are a loose reference | Switch to keyframe references |
| A visible seam on an extension | MP4 output | Re-run with MOV |
| It looks like a cartoon when you wanted realism | Negative phrasing | Positive texture words: film grain, real skin pores, natural light |

---

## Reference

- `reference/anatomy.md` — the full block-by-block anatomy with a worked
  example, plus the camera and lighting vocabulary lists.
- `reference/examples.md` — complete prompts for the common jobs: talking head,
  product shot, b-roll, keyframe sequence, edit, extension.
