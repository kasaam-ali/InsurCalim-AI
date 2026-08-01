# InsurClaim AI Presentation

A self-contained **reveal.js** slide deck for the project presentation. It runs **fully offline**
in any modern browser reveal.js is vendored locally, so no internet is needed on the day.

## Two decks

- **`core.html`** a tight **5-slide** short cut (problem → four agents → architecture → demo →
  why it's robust + the ask). Use this when time is short.
- **`index.html`** the **full** deck (problem, market, validation, fraud, amount, explainability,
  architecture, tech stack, demo, cost/ROI, roadmap). Use this for a longer talk.

Both share the same theme and assets and both run fully offline.

## How to present

1. Double-click **`index.html`** (full) or **`core.html`** (5-slide), or drag it into Chrome/Edge.
2. Press **`F`** for fullscreen. Use **→ / Space** to advance, **← ** to go back.
3. Press **`Esc`** (or `O`) for the slide overview grid; **`.`** to pause/black the screen.

That's it no build step, no server.

## Export a PDF backup (recommended to carry)

1. Open **`index.html?print-pdf`** in Chrome (add `?print-pdf` to the URL).
2. `Ctrl+P` → Destination **Save as PDF** → Layout **Landscape** → Margins **None** →
   enable **Background graphics** → Save.

## Editing

- All slide text is in `index.html` (plain HTML `<section>` blocks one per slide).
- Colours, fonts and components are in `theme.css` (matched to the product's landing page).
- The title slide has an editable line for **presenter name / date** (see the comment in `index.html`).
- Screenshots and the architecture diagram live in `assets/`.

## Contents

Title · Problem · Problem size · Market · Validation · Solution · How it works · Fraud detection ·
Amount assessment · Explainability · Architecture · Tech stack · Demo (landing, dashboard, queue) ·
Cost &amp; ROI · What's built · Roadmap &amp; the ask · Conclusion.

All figures are drawn from `docs/business/insurclaim-ai-business-case.md` and are attributed to the
public sources cited there. Synthetic &amp; public data only no real customer information.
