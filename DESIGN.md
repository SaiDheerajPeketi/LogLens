# LogLens Design System

## Product character

LogLens should feel like a flight recorder opened after an incident: dense, calm, exact, and built for scrutiny. It is an operating surface, not a marketing dashboard. The interface foregrounds time, confidence, and evidence while keeping uncertainty visible.

## Information architecture

The desktop console has four stable regions:

1. **Source rail:** choose a safe scenario or upload a text log.
2. **Anomaly timeline:** replay windows and compare anomaly scores.
3. **Diagnosis rail:** read the proposed cause, confidence, explanation mode, evidence, and caveats.
4. **Transcript:** inspect the synchronized redacted lines and focus exact citations.

At mobile widths the order becomes source, timeline, diagnosis, transcript. No analytical step is removed; the timeline becomes horizontally replayable and transcript rows become labeled blocks.

## Visual language

The canvas is near-black blue rather than neutral black. One-pixel borders establish hierarchy instead of elevated cards. Corners stay nearly square to preserve an instrument-panel character. There are no decorative gradients, glass cards, or ornamental charts.

### Color tokens

| Token | Value | Use |
| --- | --- | --- |
| Background | `#071015` | Page canvas |
| Panel | `#0a171d` | Primary work surfaces |
| Strong panel | `#0d1c23` | Selected and anchored regions |
| Border | `#1a3741` | Structure and row separation |
| Bright border | `#2a5964` | Interactive boundaries |
| Primary text | `#e9eee9` | Headings and essential values |
| Muted text | `#8fa4aa` | Supporting copy |
| Quiet text | `#60777d` | Metadata and secondary labels |
| Cyan | `#59c6c7` | Normal signals, navigation, evidence affordances |
| Amber | `#f1a33c` | Selected windows and primary action |
| Coral | `#ef7066` | Peak anomaly and error severity |
| Green | `#3ed99c` | Healthy and privacy-safe states |
| Focus | `#fff2bd` | Keyboard focus ring |

Color never acts alone. Status also appears as text, icon, position, line style, or severity label.

## Typography

- Interface and document text: `Inter`, followed by the native system sans-serif stack.
- Measurements, timestamps, line IDs, labels, and status metadata: `SFMono-Regular`, Consolas, or Liberation Mono.
- Large headings use tight negative tracking; technical labels use uppercase mono with wide tracking.
- Body copy remains sentence case and avoids all-caps paragraphs.

## Components

- **Primary action:** amber fill, dark text, compact label, visible focus.
- **Scenario option:** numbered, left-ruled selected state, one-line metadata.
- **Signal strip:** equal-width vertical samples; cyan is nominal, amber is suspicious, coral marks the strongest interval.
- **Window cell:** always names the state, line range, and score so color is supplementary.
- **Evidence link:** numbered line reference with severity and a truncated excerpt; activation moves focus to the transcript row.
- **Transcript row:** fixed-width data, explicit `CITED` marker, amber inset rule, and a stronger focused state.
- **Document metric band:** four equally weighted measurements with context directly beneath each value.

## Motion

Motion exists only to communicate work or navigation: the active pipeline spinner, smooth evidence focus, and small state transitions. `prefers-reduced-motion` removes smooth scrolling and effectively disables animation.

## Accessibility contract

- Meet WCAG AA contrast for readable content and controls.
- Preserve logical heading order and landmark regions.
- Support keyboard selection of adjacent timeline windows with Left and Right Arrow.
- Announce lifecycle and error states through a polite live region.
- Show a high-contrast focus ring on every interactive or programmatically focused element.
- Keep native button, input, select, progress, table, and list semantics.
- Maintain a complete reading and interaction path from 320 pixels upward.

## Reference captures

- [Desktop incident console](docs/screenshots/console-desktop.png)
- [Evaluation page](docs/screenshots/evaluation.png)
- [Mobile incident flow](docs/screenshots/console-mobile.png)
