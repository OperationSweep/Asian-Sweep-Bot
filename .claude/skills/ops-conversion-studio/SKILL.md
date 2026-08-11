---
name: ops-conversion-studio
description: Design and build premium dark-mode B2B websites for agencies, SaaS products and operations-heavy businesses. Use when the user wants a metric-led, conversion-focused, product-native web presence, with editorial warm-white typography, restrained burnt-orange accents, dashboard-style proof and structured service or industry pages.
---

# Ops Conversion Studio

Create a **premium conversion website** that makes a complex B2B offer feel concrete, credible and ready to buy. The style is deliberately product-native: show the operating reality through bespoke interface scenes, proof metrics and clear workflow, rather than generic stock imagery or decorative gradients.

Use this skill for original work. Borrow the **visual language and information-design principles**, never a source brand’s name, logo, copy, claims, customer list, images, proprietary screens or code.

## Read first

Read the following references before designing or implementing a page:

- `references/design-system.md` for visual tokens, components and responsive constraints.
- `references/page-recipes.md` for the appropriate page architecture.

## Core design intent

Build toward these outcomes:

| Principle | Required expression |
|---|---|
| Operational credibility | Make the work visible through accurate dashboard, workflow, pipeline, document, scheduling or product-architecture scenes. |
| Conversion clarity | Give each page one primary action. Use a secondary action only when it reduces commitment, such as viewing the process or examples. |
| Measured confidence | Use relevant, verifiable metrics and plain-language proof. Use placeholders or omit the metric when proof is unavailable. |
| Senior restraint | Use a quiet dark canvas, warm off-white text, compact spacing rhythm and one controlled accent. Avoid visual noise. |
| Editorial hierarchy | Pair a concise, oversized headline with a softened emphasis phrase, then earn attention through progressively specific sections. |

## Mandatory workflow

### 1. Establish the message and evidence

Identify the audience, the commercial outcome, the primary conversion action and the evidence available. Write the hero around one concrete transformation, not an inventory of services. Prefer language such as “turn enquiries into scheduled work” over “full-service solutions”.

Do not invent ratings, metric improvements, customer logos, testimonials, case studies, accreditations, clients or integration claims. If evidence is limited, use process proof, clearly marked placeholders or specific capability descriptions.

### 2. Choose a page recipe

Select the closest architecture from `references/page-recipes.md`. Use the service recipe for a focussed offer, the industry operating-system recipe for complex, multi-step vertical solutions, the index recipe for a capability or resource overview, and the compact recipe for contact or legal pages.

Do not force every section onto every page. Preserve the sequence of: claim, proof, mechanism, capability, delivery method, reassurance, conversion.

### 3. Establish the design system before the first component

Implement the tokens in `references/design-system.md` first. The interface must have a warm near-black canvas, warm-white type, muted grey body copy, a single burnt-orange action colour, charcoal cards, fine low-contrast borders and a tight radius family. Use a neutral grotesk such as Instrument Sans when available; otherwise use a close system sans.

Use the accent colour sparingly. It belongs on the primary CTA, eyebrow labels, selected status markers and small portions of metric proof. It must not become the background of entire sections or large blocks of copy.

### 4. Create product-native proof

Build an original, domain-specific proof scene for the hero or first mechanism section. Base it on the user’s real offer. Examples include:

| Domain | Suitable proof scene |
|---|---|
| SaaS platform | Tenant architecture, onboarding funnel, billing state or usage dashboard. |
| Trade service | Booking, dispatch, technician mobile job view or paid invoice flow. |
| Professional service | Intake queue, client portal, document checklist or timeline. |
| Operations product | Queue console, workflow board, asset record, approval path or live reporting view. |
| Marketing offer | Traffic-to-revenue funnel, scorecard, experiment feed or search-result composition. |

Use semantically accurate labels and realistic information density. Mark sample data where a viewer could mistake it for a factual claim. Keep the proof scene legible on mobile by prioritising one key panel and progressively simplifying peripheral panels.

### 5. Build reusable components

Create the following components as a coherent family, using the reference guidance:

- A compact global navigation with a clear primary action.
- Rich desktop mega menus for related service or industry destinations, with an accessible mobile disclosure alternative.
- Primary pill CTA, secondary text-arrow action and muted text link.
- Eyebrow label, split-emphasis display headline and compact body-copy block.
- Outcome metric cards, capability cards and a product-proof frame.
- Numbered feature rows with a visual counterpart.
- Delivery timeline, FAQ disclosure list and conversion footer.
- A structured multi-column footer with email capture only where consent language and a lawful handling process exist.

Use semantic HTML: `nav`, `main`, `section`, `article`, heading hierarchy, buttons for controls, real links for navigation, and native `details/summary` or accessible accordion semantics for FAQs.

### 6. Make the layout responsive by design

Design desktop and mobile deliberately rather than shrinking a desktop grid. At medium widths, collapse complex 3–4 column layouts into 2 columns. At small widths, use a single column with fewer competing panel layers, full-width primary actions where appropriate, readable body text and no horizontal overflow.

Preserve headline presence with `clamp()` sizing, typically between 42px and 72px for a hero display. Do not reduce primary interactions below a comfortable touch target. Ensure every contrast pair remains legible, especially muted text and fine borders on the warm-black background.

### 7. Verify before delivery

Check the implementation at a wide desktop, tablet and narrow mobile size. Verify:

- The hero value proposition, primary action and first proof artifact are visible without excessive scrolling.
- Every CTA labels the destination or action clearly.
- The page has one visual priority per viewport rather than several equal-weight focal points.
- Navigation, menu disclosures and FAQ controls work with keyboard navigation and visible focus states.
- All motion is optional, subtle and respects reduced-motion preferences.
- Placeholders are not presented as facts and source-brand material has not leaked into the work.

## Non-negotiable quality bar

Do not use a white template with dark cards, glassmorphism, purple-blue neon, generic blob gradients, visual clutter, fake app screenshots, unexplained floating badges, or endless tiny feature cards. Do not hide key content behind animation. Do not overuse rounded pills.

Aim for **editorial clarity plus operational specificity**. Every visual object should either demonstrate the offer, support credibility or guide a conversion decision.
