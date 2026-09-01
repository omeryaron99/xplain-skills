# Worked prompts by job

Six complete prompts, one per common job. Copy the shape, swap the content.

---

## 1. Talking head with a real face and voice

References: Image 1 (photo of the person), Audio 1 (10 seconds of their voice).

```
Image 1: subject appearance reference. Audio 1: the speaker's voice timbre.

A woman speaks directly to camera in a bright modern office, realistic
corporate video style, locked-off medium close-up with a slow push in.

0-5s: [Medium close-up, eye level, centered] The woman from Image 1 looks
into the lens and begins speaking, with small natural head movements and
relaxed shoulders.
Dialogue (woman, in Hebrew, using the voice from Audio 1):
"רוב האנשים עושים את זה הפוך."

5-12s: [Same framing, very slow push in] She gestures once with an open
hand and keeps speaking, her expression warming into a small smile.
Dialogue (woman, in Hebrew): "והתוצאה נראית בדיוק כמו כולם."

Overall requirements: Realistic photographic look, 50mm lens, soft window
light from camera left, shallow depth of field with a softly blurred
office behind her. Authentic skin texture, natural micro-expressions, no
beautification or skin smoothing. Her face must strictly follow Image 1
and stay consistent throughout with no identity drift. Lip movements must
match the spoken words precisely. Quiet room tone only, no background
music. No subtitles. 9:16 vertical frame.
```

Note the lip-sync line. Without it, mouth and audio drift on longer takes.

---

## 2. Product hero shot

Reference: Image 1 (the product on white).

```
Image 1: product reference. Match its shape, proportions, label and colors
exactly.

A glass bottle stands on wet dark stone as water sheets around it, premium
commercial style, slow orbiting camera.

0-4s: [Extreme close-up on the base, camera orbiting slowly to the right]
Water runs across the stone and beads on the glass. Backlight catches the
liquid inside.

4-10s: [Camera cranes up into a medium shot, still orbiting] The full
bottle from Image 1 comes into frame, condensation on the surface, the
label facing camera and fully legible.

10-12s: [Locked-off medium shot] The camera settles. A single drop runs
down the label and the frame holds.

Overall requirements: Premium commercial product cinematography, macro
lens, hard rim light from behind against a deep charcoal background,
strong specular highlights, shallow depth of field. The product must match
Image 1 exactly in shape, proportion, label artwork and color, with no
distortion of the text on the label. Water sounds only, no music. No
subtitles. 16:9 horizontal frame.
```

Label text is where product shots break. Naming it as a constraint helps.

---

## 3. B-roll from text only, no references

```
A courier cycles through a narrow market lane at dusk, realistic
documentary style, handheld follow shot.

0-5s: [Wide shot, handheld, following from behind] A courier in a yellow
jacket rides slowly past fruit stalls. Hanging bulbs come on overhead as
the light drops. Market chatter and bicycle chain noise.

5-11s: [Medium side shot, camera tracking alongside] She slows, hears a
bell, and turns her head toward a narrow side lane.

11-18s: [Wide shot, camera pushing in] She crosses to a blue flower stall
while pedestrians pass behind her, slightly out of focus.

18-24s: [Medium close-up, camera settling to a stop] She lifts a small
brass tube from her bag, places it on the counter, and holds still.

Overall requirements: Realistic documentary cinematography, 35mm lens,
handheld with natural breathing movement, practical warm bulb light
against cool dusk blue, fine film grain, natural skin texture. Consistent
wardrobe and appearance throughout. Ambient market sound, bicycle and
footsteps only, no background music. No subtitles. 16:9 horizontal frame.
```

With no references, every subject has to be described in words. Wardrobe and
appearance details do the work the reference image would have done.

---

## 4. Keyframe sequence

When the video must actually pass through images you already made. Seven images
uploaded in order.

```
Use Images 1 to 7 in order as keyframes.

A paper boat travels from a kitchen sink out into an open ocean and back
to a child's hands, hand-drawn 2D animation style, continuous flowing
camera.

The boat leaves the sink and slips down a gutter in the rain. It reaches a
storm drain and drops into dark water. It emerges into a wide grey sea
under heavy clouds. The sun breaks through and the water turns turquoise.
The boat drifts toward a beach. A child crouches and lifts it from the
shallows. The final frame holds on the boat in their hands.

Overall requirements: Hand-drawn 2D animation, warm watercolor palette,
visible paper texture, gentle continuous camera movement between keyframes
with smooth transitions and no jump cuts. All visuals should follow the
corresponding keyframes. Soft piano score with water and rain sounds. No
subtitles. 16:9 horizontal frame.
```

Keyframes beat a multi-panel storyboard whenever alignment matters. A
multi-panel board is a loose plot reference, not a spec.

---

## 5. Editing an existing video

Locks aspect ratio and duration to the source. Set the ratio parameter to
`adaptive`, duration to `-1`, and output MOV.

```
Editing task. Preserve the composition, camera position, lighting and
performance rhythm of Video 1 exactly.

Only change the man's jacket from black leather to a beige canvas work
jacket, from the first frame to the last. Everything else in the frame
stays unchanged, including his face, hands, the background and the
lighting.

The result must be a continuous take with no jump cuts and no flickering.
Keep the original audio unchanged.
```

The shape that works: **state the scope, then describe the change as A to B,
then say what stays.** Include an edit verb (edit, add, insert, remove, delete,
modify, replace, change to) so the model routes it as an edit task.

---

## 6. Extending an existing video

Locks aspect ratio to the source; you choose how much to add. Output MOV.

```
Extend Video 1 forward by 6 seconds.

The car continues down the road and the camera stays alongside it. It
slows and pulls into a lit petrol station on the right. The driver steps
out, stretches, and looks back the way he came.

Match the grade, grain, lighting and camera behaviour of Video 1 exactly
so the join is invisible. Continue the existing engine and ambient audio
with no change in level. No music. No subtitles.
```

Include an extension trigger: extend forward, extend backward, continue,
continue from. The seam is cleanest when the source was itself generated by
Seedance 2.5, and MOV on both sides is what keeps the color and audio matched.

---

## Quick sanity check before handing a prompt over

- Every reference asset is bound by number and given a job.
- The one-sentence summary does not contradict the shot list.
- Timestamps are continuous whole seconds with no gaps.
- Each beat has a shot size and a camera instruction.
- There is a consistency line for any recurring face or product.
- Audio is stated explicitly, including "no BGM" if that is what is wanted.
- Subtitles are turned off unless they are wanted.
- The aspect ratio is named in the prompt as well as set in the UI.
