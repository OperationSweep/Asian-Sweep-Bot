# Ops Conversion Studio: Design System

## 1. Design signature

The visual signature is **warm industrial minimalism**. It feels like a refined operations product and a senior consultancy at once: quiet, specific and confident. Build the composition around text, evidence and original interface artefacts, not ornamental art direction.

## 2. Tokens

Use the following as practical starting values. Adjust only to preserve contrast, brand fit and responsive legibility.

```css
:root {
  --ocs-canvas: #141412;
  --ocs-surface: #232320;
  --ocs-surface-raised: #2a2a26;
  --ocs-text: #fafaf7;
  --ocs-text-muted: #a7a7a0;
  --ocs-text-faint: #74746e;
  --ocs-line: rgb(250 250 247 / 8%);
  --ocs-line-strong: rgb(250 250 247 / 14%);
  --ocs-accent: #c14a2c;
  --ocs-accent-hover: #d55a39;
  --ocs-focus: #f2a27e;
  --ocs-radius-card: 16px;
  --ocs-radius-control: 10px;
  --ocs-radius-pill: 999px;
  --ocs-content-max: 1240px;
  --ocs-gutter: clamp(20px, 4vw, 56px);
  --ocs-section-y: clamp(72px, 10vw, 152px);
}
```

> Do not use pure black or pure white. The small warmth in the canvas and text is fundamental to the tone.

## 3. Typography and hierarchy

Use **Instrument Sans** when possible. Fall back to `Inter`, `Arial`, or the platform system UI stack. The type should feel roomy rather than compressed, with dense headings and easy-to-scan supporting copy.

| Level | Desktop rule | Mobile rule | Purpose |
|---|---:|---:|---|
| Display hero | `clamp(44px, 6.2vw, 72px)`, 500, 0.98–1.05 line-height, -0.025em tracking | Minimum 42px | One compact commercial transformation. |
| Section title | `clamp(32px, 3.4vw, 48px)`, 500, 1.1–1.15 line-height, -0.02em tracking | Minimum 30px | Section-level outcome or mechanism. |
| Card/title | 18–24px, 550–600, 1.2 line-height | 18–22px | Scannable component anchor. |
| Body | 15–17px, 400, 1.55–1.7 line-height | 15–16px | Direct and compact explanation. |
| Eyebrow/label | 10–12px, 650–700, uppercase, 0.10–0.14em tracking | Same | Orient the reader without competing with the heading. |
| Metric value | 28–40px, 550, -0.03em tracking | 26–32px | The visual proof, never decorative filler. |

Set the muted emphasis portion of a display heading in `--ocs-text-muted`. Do not rely on italics alone to establish contrast. Keep headings narrow enough to form intentional 2–4 line blocks, rather than spanning the entire screen.

## 4. Layout geometry

Centre the content within `--ocs-content-max` and use a consistent side gutter. Let the hero hold a tighter readable measure, usually 760–880px for headline and 520–650px for its supporting paragraph. Let detailed product/UI frames use the full content width only when they need the space.

Use large section separation. Within sections, pair spacious top-level rhythm with compact local groupings. Grid lines, card edges and aligned baselines should make the site feel engineered.

| Breakpoint | Layout expectation |
|---|---|
| `>= 1180px` | 3-column editorial grids, wide asymmetric proof layouts, mega menus, dense product scenes with secondary panels. |
| `768–1179px` | Two-column grids, simplified visual scenes, navigation may begin to collapse. |
| `< 768px` | One-column reading order, 20–24px gutters, mobile drawer/disclosures, stack CTAs where needed, suppress non-essential floating proof panels. |

## 5. Essential components

### Navigation and mega menu

Keep global navigation shallow: wordmark, 4–6 top-level links, a single high-priority CTA. Use small uppercase links with generous hit areas. Desktop mega menus should be triggered by click or keyboard, dismiss on `Escape`, and contain a short grid of destinations with a bold title and one-line explanation. Make the disclosure state clear with an arrow or plus/minus transition.

On mobile, turn navigation groups into accordions. Do not require hover. Provide visible focus states and do not trap keyboard focus incorrectly.

### CTAs and links

The **primary CTA** is a compact accent pill, white text, medium semibold type, 12–14px vertical padding and 20–24px horizontal padding. Use it once in each key viewport. The **secondary action** is transparent, usually a text label with arrow, optionally with a low-contrast outline on sparse backgrounds. Links should use purposeful verbs: “Book a call”, “See the workflow”, “Review capabilities”.

### Metric cards

Build metric cards as raised charcoal rectangles with a 16px radius, 1px low-contrast border and 20–24px padding. Use one large metric followed by a precise label. Aim for 3–4 metrics per proof group. On a service hero, add a sentence of commercial friction alongside the metrics rather than more cards.

### Product-proof frames

Use a charcoal bordered frame, shallow shadows if any, and hierarchy that resembles a real interface. Combine a tiny monospaced or uppercase system label, a primary record/status, concise rows and a controlled status colour. Do not attempt to recreate a full application. Construct a representative operational moment.

Use distinct objects for distinct claims: a pipeline for lead flow, a calendar for scheduling, a checklist for document collection, a table for reporting, an architecture diagram for SaaS. Let the artefact earn the claim.

### Feature rows

Pair a number such as `01` through `05` or `01` through `09` with a short concrete feature name, a customer-facing implication and 2–3 micro-tags. Use a two-column desktop grid with the proof frame taking visual priority. On mobile, place the proof frame before or after the features according to reading logic, never side-by-side.

### Capability and library sections

Use 3-card grids for high-level capability pillars. For complex vertical products, group modules into 3–6 numbered clusters with a short status or build-state tag. The output should read like a product map, not a generic feature matrix.

### Timeline and FAQ

Build a 4-step timeline around real calendar cadence, deliverables and tangible checkpoints. Mark time as “Week 1”, “Weeks 2–4”, or “Ongoing”, not as vague phases. For FAQs, use quiet full-width disclosure rows, a subtle divider, a large readable question, a plus/minus cue, and one concise answer.

### Newsletter/listing cards

Use a 3-column desktop grid. Each linked article card has a distinctive 3:2 or 4:3 visual, category chip, title, excerpt and text-arrow. Keep image treatment crisp and meaningful. Avoid stock-phone mock-ups, unnecessary gradients and unrelated AI-generated art.

### Conversion footer

End substantive pages with an editorial call-to-action band: eyebrow, split-emphasis headline, 1–2 sentence supporting copy and two actions. Follow it with a structured footer containing brand context, grouped links and legal links. Add email capture only with a clear consent statement and known handling process.

## 6. Motion and states

Use motion to clarify state, not to decorate. Limit hover motion to a 150–220ms colour, border, opacity or small translate change. Allow product scenes to have small ambient activity only when it does not distract from reading. Honour `prefers-reduced-motion: reduce` by removing animation and transitions.

On hover, cards may lift 2–4px, brighten their border and reveal a muted arrow. On focus, use a visible `--ocs-focus` outline with sufficient offset. Never hide focus rings without an equally clear replacement.

## 7. Accessibility and content rules

Meet WCAG AA contrast intent, especially for `--ocs-text-muted` against the canvas. Do not use accent colour alone to indicate state. Ensure all icon-only controls have accessible names. Avoid visual text embedded inside images when it must be read or translated.

Use real proof only. When the visual needs representative numbers, write “Example data” or use obviously illustrative labels. Replace every source-derived name, brand, claim, illustration and image with original project material.

## 8. Anti-patterns

Avoid bright blue-purple gradients, glass panels, white sections between dark ones, overly rounded UI, emoji/icon overload, abstract 3D chrome, fake badges, vague marketing superlatives, long feature walls and generic stock photos. A component must show how the business works, establish proof, or help the visitor decide.
