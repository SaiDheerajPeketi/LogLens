---
format: 1920x1080
duration: 60s
message: "LogLens turns anomaly scores into an auditable, evidence-linked incident hypothesis"
arc: Demo Loop — pain → source → diagnosis → evidence → measured proof → repository
audience: engineering recruiters, hiring managers, and SRE practitioners
mode: autonomous
music: none
---

## Video direction

- palette system: Use only the `frame.md` two-register system: ink-black ground with cream type and fire-orange emphasis, or a full fire-orange field with ink type. Cyan/green may appear only inside the unchanged product screenshots. Inter display is lowercase and weight-led; mono labels are uppercase chrome. No gradients, shadows, rounded decorative cards, or extra accent hues.
- motion grammar: Silent, cue-paced reveals replace voiceover pacing. Every phrase, crop, citation, and metric arrives on its own visual reading beat across the full shot, with smooth long-tail settles and a locked camera after each focal move. Use explicit deterministic `fromTo` states, transform/opacity/paint motion only, and velocity-matched internal seams. No element enters at time zero; leave a 0.15–0.25s visual breath first.
- reveal model: Preserve the captured UI rather than rebuilding or beautifying it. Treat screenshots as full-bleed surfaces inside hard-edged crop windows with 1px hairlines. Move the crop or a parent camera, never animate screenshot layout properties. Keep all load-bearing text and evidence above the bottom 17% keep-out.
- rhythm: precise hook → exploratory workflow → deliberate diagnosis → fastest evidence traversal → compact metric proof → calm architectural resolve. Frame 3 holds the cause/confidence lockup; Frame 5 holds all four measured results together; Frame 6 reserves its final 3.2 seconds for a dead-static repository lockup.
- silence: No narration, music, or sound effects. `SCRIPT.md` must remain absent.
- negative list: No slideshow front-load, no screensaver drift, no lazy breathing, no bounce/elastic entrances, no particle decoration, no fake browser chrome, no invented UI states, no public-live badge, no public URL claim, no aspirational metrics, and no motion continuing after a held read has settled.

## Frame 1 — The missing why

- scene: An alert-like trace races past until one database-timeout incident arrests the frame and resolves into the LogLens promise.
- voiceover: ""
- duration: 6s
- poster: 4.8s
- transition_in: cut
- status: animated
- src: compositions/frames/01-missing-why.html
- type: hook
- persuasion: Pain validation
- beat: tension → curiosity
- blueprint: typewriter-reveal (Adapt)
- focal: assets/console-desktop.png
- roles: console-desktop = background, dimmed and cropped to its redacted transcript rows
- sfx: none
- asset_candidates: assets/console-desktop.png — completed incident console with a database-timeout diagnosis and cited evidence

narrativeRole: Establish that an anomaly score alone does not explain a failure, then name the evidence-first promise.
keyMessage: Detection is useful only when a reviewer can inspect why.

Adapt: Keep the blueprint's type → edit → collapse → product reveal engine; place the finished real console behind the final lockup instead of inventing a logo animation.

Scene 1 (0.0–2.1s): After a 0.2s dark hold, a faint full-bleed transcript crop fades to 18% opacity. A cream caret types `anomaly found.` character by character in the upper-left reading zone (`discrete-text-sequence` + `context-sensitive-cursor`); a mono `incident / checkout` label anchors the opposite corner. Camera locked, headline dominant, bottom keep-out clear.
Scene 2 (2.1–3.7s): The caret backspaces `found.` and retypes the fire-orange word `explained?` in the same line (`discrete-text-sequence`). The edit is the only motion; the completed question holds for 0.45s.
Scene 3 (3.7–6.0s): The typed line collapses horizontally into a short orange rule and the real console crop scales into the right two-thirds from the same anchor (`scale-swap-transition`). `LogLens` resolves large at left, followed at 4.7s by `evidence before inference.` The interface, wordmark, and promise hold dead still from 5.2s.

## Frame 2 — Replay the incident

- scene: The real console arrives full frame; source controls activate and the camera moves from scenario selection into the anomaly timeline.
- voiceover: ""
- duration: 12s
- poster: 8.5s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/02-replay-incident.html
- type: product_intro
- persuasion: Show-don't-tell proof
- beat: curiosity → control
- blueprint: compose
- focal: assets/console-desktop.png
- roles: console-desktop = cutout, shown as the authentic full product surface with two spotlight crops
- sfx: none
- asset_candidates: assets/console-desktop.png — source controls, replayable anomaly timeline, and synchronized analysis console

narrativeRole: Introduce LogLens by showing the operator's first two actions: select a source and inspect the suspicious window.
keyMessage: A reviewer can move from input to the anomalous moment in one coherent surface.

Compose: Use one custom-cursor action and one camera move across the authentic completed capture; honest spotlight overlays reveal the workflow without fabricating UI mutations.

Scene 1 (0.0–3.2s): After a 0.2s orange-field hold, the real console pushes in as a hard-edged window occupying roughly 78% of the frame (`motion-blur-streak` into a smooth settle). The rest of the screen is dimmed except the left source column. A custom orange cursor glides to `Checkout database timeout` and presses once (`cursor-click-ripple`); a mono rail reads `01 / select a source` in the upper safe area.
Scene 2 (3.2–7.6s): A single camera pan/focus-lock moves from the left controls to the center anomaly timeline (`viewport-change`), with the crop staying sharp and all non-target regions selectively dimmed (`depth-of-field-blur`). At 5.0s the cursor tracks along the coral anomaly peak; an orange vertical locator and `02 / replay the suspicious window` label draw in, one after the other.
Scene 3 (7.6–10.0s): The view pulls back once to reveal the left-control / central-timeline / right-summary composition together. Three mono labels arrive sequentially in the top band — `source`, `window`, `diagnosis` — with explicit `fromTo` states, each pointing to a real region with a short anchored hairline.
Scene 4 (10.0–12.0s): The cursor rests on the selected anomaly and the composition locks. A large lower-left statement above the keep-out reads `replay the failure.` then, 0.45s later, `inspect the evidence.` No camera drift during the final read.

## Frame 3 — A supported hypothesis

- scene: The view isolates the selected anomaly, then the probable cause and calibrated confidence take over as one linked diagnosis.
- voiceover: ""
- duration: 14s
- poster: 9.5s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/03-supported-hypothesis.html
- type: feature_showcase
- persuasion: Feature-to-benefit translation
- beat: clarity + confidence
- blueprint: video-text-pivot (Adapt)
- focal: assets/console-desktop.png
- roles: console-desktop = cutout, cropped first to the selected anomaly and then to the diagnosis panel
- sfx: none
- asset_candidates: assets/console-desktop.png — selected timeline window, database-timeout cause, 98% confidence, and five cited lines

narrativeRole: Turn the selected anomaly into an explicit, bounded incident hypothesis rather than an unexplained score.
keyMessage: LogLens states what it thinks happened and how confident the classifier is.

Adapt: Keep the signature weight-transfer from product surface to hero stat; substitute a real screenshot crop for the blueprint's video clip and use the captured diagnosis values unchanged.

Scene 1 (0.0–3.4s): The selected timeline crop arrives as a full-width strip across the upper two-thirds, settling from a slight x offset with no rounded container. A mono label `selected anomaly / 00:02:10–00:02:15` appears at 1.0s; the highlighted peak receives a single marker-circle draw (`css-marker-patterns`) at 2.1s.
Scene 2 (3.4–7.4s): Signature move — the timeline strip slides left and scales to the 40% supporting column while the real right-side diagnosis crop expands into the vacated 60% (`scale-swap-transition`). `database timeout` is rebuilt as the dominant lowercase display phrase above the crop; the cause label lands first, then `probable cause` in mono above it.
Scene 3 (7.4–10.8s): The diagnosis crop yields visual weight to `98%` in fire-orange, which counts from 0 to the captured value (`counting-dynamic-scale`) while a thin confidence bar fills to the same endpoint (`stat-bars-and-fills`). `classifier confidence` types beneath it in cream; the real five-citation summary remains visible at the right edge as proof context.
Scene 4 (10.8–14.0s): The surface and metric settle into an asymmetric 40/60 split. A final cream line arrives word-by-word at 11.2s: `a hypothesis, not a verdict.` The number, cause, and caveat hold completely still from 12.4s.

## Frame 4 — Evidence before inference

- scene: Five citation markers travel into their exact redacted transcript rows; the deterministic-fallback badge closes the loop.
- voiceover: ""
- duration: 12s
- poster: 8.5s
- transition_in: crossfade
- status: animated
- src: compositions/frames/04-evidence-before-inference.html
- type: feature_showcase
- persuasion: Verifiability and risk reduction
- beat: trust + control
- blueprint: transcript-scroll-artifact-reveal (Adapt)
- focal: assets/console-desktop.png
- roles: console-desktop = background, enlarged to a transcript-and-evidence traversal with a final full-console receipt
- sfx: none
- asset_candidates: assets/console-desktop.png — five evidence links, deterministic-fallback status, and redacted transcript rows

narrativeRole: Prove that the explanation is inspectable and that failure of the optional prose adapter does not remove citations.
keyMessage: Every explanation points to supplied redacted evidence, including the deterministic fallback.

Adapt: Keep the blueprint's traverse → hinge → artifact structure; the long surface is the captured transcript, the hinge is a citation focus, and the artifact is the cited deterministic explanation in the same console.

Scene 1 (0.0–5.0s): Open tightly on the redacted transcript crop, full-bleed behind a dark edge-fade. Five cited rows travel upward in reading order by one continuous element scroll (`3d-page-scroll`, flat variant); each row's line number switches from cream to fire-orange only when it crosses the focal rail. A mono counter steps `01 / 05` through `05 / 05` in the upper-right, never inventing new log text.
Scene 2 (5.0–7.2s): The traversal stops on one cited row. A fire-orange citation bracket draws from its line number to the evidence summary (`css-marker-patterns`); this is the shot's single hinge. The words `exact line. redacted first.` appear in two discrete reading beats above the keep-out.
Scene 3 (7.2–10.1s): One fast decelerating zoom-out (`coordinate-target-zoom`) reveals the complete console with transcript below and explanation above. The `Deterministic fallback` badge receives a precise one-shot underline while a three-part receipt cascades beside it: `5 cited lines` / `0 raw uploads retained` / `fallback still cited`.
Scene 4 (10.1–12.0s): Everything except the actual cited rows dims. The statement `every claim stays inspectable.` lands in the upper-left, then the camera and all elements lock for the final 1.2s. No cursor and no further motion.

## Frame 5 — Measured, not implied

- scene: The evaluation page locks in place while four held-out metrics count on and the split boundary remains visible.
- voiceover: ""
- duration: 8s
- poster: 5.5s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/05-measured-results.html
- type: social_proof
- persuasion: Statistical proof with disclosed boundaries
- beat: credibility
- blueprint: dataviz-countup (Adapt)
- focal: assets/evaluation.png
- roles: evaluation = background, held as the authentic evaluation surface behind four extracted metric instruments
- sfx: none
- asset_candidates: assets/evaluation.png — held-out HDFS and synthetic RCA results, split methodology, confusion counts, and limitations

narrativeRole: Separate product demonstration from model evidence and show the actual evaluation boundary.
keyMessage: HDFS PR-AUC is 0.9994, HDFS F1 is 0.9956, false-positive rate is 0.0002, and synthetic RCA macro-F1 is 1.0000 on the documented held-out splits.

Adapt: Keep the blueprint's count-up instruments and final held metric field; replace the camera push-through with a restrained row build so all four related results remain comparable in one visual space.

Scene 1 (0.0–1.8s): The real evaluation page settles as a full-height background crop at 26% opacity. `measured on held-out data` wipes in across the upper-left at 0.35s; a mono `evaluation / test splits untouched` tag arrives beneath it. Camera remains static.
Scene 2 (1.8–5.5s): Four top-border-only stat blocks assemble left-to-right in one shared row (`waterfall-entry`), then their values count to the exact measured figures in staggered pairs (`counting-dynamic-scale`): `0.9994` HDFS PR-AUC, `0.9956` HDFS F1, `0.0002` false-positive rate, `1.0000` synthetic RCA macro-F1. Each number is paired with a thin fill/bar instrument (`stat-bars-and-fills`) and a mono dataset label; no pie, gridline, or legend.
Scene 3 (5.5–8.0s): The four metrics stay co-resident and the underlying split-methodology heading sharpens while the rest of the screenshot remains dim. A bottom-safe cream line arrives at 5.9s: `strong benchmarks. bounded claims.` The metric row holds dead static from 6.7s through the transition.

## Frame 6 — Inspect the whole system

- scene: The pipeline assembles from redaction through cited explanation, then contracts into the repository name and an honest local-demo status.
- voiceover: ""
- duration: 8s
- poster: 6.5s
- transition_in: blur-crossfade
- status: animated
- src: compositions/frames/06-inspect-system.html
- type: cta
- persuasion: Transparency and low-friction next step
- beat: confidence → motivation
- blueprint: logo-assemble-lockup (Adapt)
- focal: none — typographic architecture and repository lockup
- roles: none — intentionally asset-free closing frame
- sfx: none
- asset_candidates:

narrativeRole: Close on architecture, source availability, and the measured result without implying a public hosted deployment.
keyMessage: Inspect the MIT-licensed implementation at github.com/SaiDheerajPeketi/LogLens; the verified demo runs locally with Docker and public hosting is deferred.

Adapt: Keep the blueprint's parts-arrive build and long static repository lockup; the arriving parts are named architecture stages, which assemble into the LogLens identity instead of a decorative logo mark.

Scene 1 (0.0–2.3s): On ink-black, seven sharp pipeline labels arrive from alternating edges into one left-to-right rail — `redact` → `parse` → `features` → `anomaly` → `cause` → `evidence` → `explain` — via a restrained `waterfall-entry`. Hairline connectors draw only between adjacent named stages (`svg-path-draw`), and a mono caption reads `privacy boundary first` above the first node.
Scene 2 (2.3–4.8s): The pipeline compresses toward center in one unbroken scale-swap (`scale-swap-transition`) and resolves into `LogLens` on a full fire-orange register. Three ink proof lines assemble below it in sequence: `MIT licensed` / `verified local Docker demo` / `public hosting deferred`. No public-live badge appears.
Scene 3 (4.8–8.0s): The wordmark shifts left just enough for `github.com/SaiDheerajPeketi/LogLens` to wipe in beside it. A final mono line `evidence before inference` draws on below. The complete repository lockup holds dead static from 5.3s to the exact 60.0s endpoint.
