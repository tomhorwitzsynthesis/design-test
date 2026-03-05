# SYNTHESIS DESIGN REFERENCE
### A Design System for LLM-Generated Dashboards & Visualizations

> **HOW TO USE THIS FILE**  
> Paste the contents of this file at the top of any prompt to Claude, GPT, Gemini or other LLMs when requesting dashboards, data visualizations, reports, or any UI output. Instruction: *"All output must strictly follow the Synthesis Design Reference below."*

---

## 1. BRAND DNA

**Company:** Synthesis (synthesiscg.com) — strategy, brand and data consultancy  
**Aesthetic:** Swiss Editorial Precision. Confident negative space. Data that breathes.  
**Feel:** A premium consulting firm that treats data the way an art director treats a magazine spread. Not flashy — authoritative. Not corporate — considered.

**In one sentence for the LLM:** *Think Neue Zürcher Zeitung meets a strategy deck — clean grids, editorial typography, black and white as the primary language, with a single electric green used sparingly as a signal.*

---

## 2. DESIGN PRINCIPLES

1. **White space is content.** Never fill every pixel. Generous padding communicates confidence.
2. **One accent, used once.** Green (`#2FCC6E`) appears only where it needs to: a key number, a primary CTA, a status indicator. Never decoratively.
3. **Typography does the heavy lifting.** Size contrast and weight contrast replace color contrast. Big numbers, small labels.
4. **Grids are visible infrastructure.** Thin 1px column/row guides are a design element, not an error. Use them intentionally.
5. **Labels are uppercase, small, tracked.** Section identifiers, chart axes, and metadata always use `text-transform: uppercase; letter-spacing: 0.08em; font-size: 11px`.
6. **No rounded corners on data.** Cards and chart containers use `border-radius: 4px` maximum. Data is precise — geometry should be too.
7. **Borders over shadows.** Prefer `1px solid #E8E8E8` over box-shadows for card separation.
8. **Hierarchy in 3 levels only:** Display (large headline), Label (uppercase small), Body (regular reading). Do not invent additional levels.

---

## 3. COLOR TOKENS

```css
:root {
  /* Core Palette */
  --color-bg:           #FFFFFF;   /* Page background */
  --color-surface:      #F7F7F7;   /* Card / panel background */
  --color-surface-2:    #F0F0F0;   /* Nested surface, table zebra */
  --color-border:       #E2E2E2;   /* All dividers and card borders */
  --color-border-strong:#C0C0C0;   /* Emphasized dividers, axis lines */

  /* Text */
  --color-text-primary: #0A0A0A;   /* Headlines, key numbers */
  --color-text-body:    #1A1A1A;   /* Body copy */
  --color-text-muted:   #888888;   /* Secondary labels, captions, metadata */
  --color-text-faint:   #BBBBBB;   /* Disabled, placeholder */

  /* Accent — use sparingly */
  --color-accent:       #2FCC6E;   /* Primary CTA, key highlight, positive delta */
  --color-accent-dim:   #D4F5E3;   /* Accent background tint (badges only) */

  /* Data Visualization Palette */
  --color-data-1:       #0A0A0A;   /* Primary series */
  --color-data-2:       #888888;   /* Secondary series */
  --color-data-3:       #C0C0C0;   /* Tertiary / reference series */
  --color-data-4:       #2FCC6E;   /* Highlighted / selected series */
  --color-data-5:       #E2E2E2;   /* Background bars, baselines */

  /* Semantic */
  --color-positive:     #2FCC6E;
  --color-negative:     #0A0A0A;   /* Use bold weight, not red */
  --color-neutral:      #888888;
  --color-warning:      #D4A017;   /* Use only when critical */
}
```

**Color rules for LLMs:**
- Do NOT use blue, purple, teal, orange, or multi-hue rainbow palettes.
- Charts default to black/gray scale. Only one series may use green (`--color-accent`).
- No gradient fills on charts or cards. Flat only.
- Background is always white or `#F7F7F7`. Never dark mode unless explicitly requested.

---

## 4. TYPOGRAPHY TOKENS

```css
:root {
  /* Font Stack */
  --font-display: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  --font-body:    'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  /* Load from Google Fonts: https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,700;0,9..40,900&display=swap */

  /* Scale */
  --text-display:    clamp(2.5rem, 5vw, 5rem);   /* Hero numbers, section titles */
  --text-heading-1:  clamp(1.5rem, 3vw, 2.5rem); /* Card headlines, chart titles */
  --text-heading-2:  1.125rem;                    /* Sub-section headers */
  --text-body:       0.875rem;                    /* Default body text (14px) */
  --text-label:      0.6875rem;                   /* Uppercase labels (11px) */

  /* Weights */
  --weight-black:  900;
  --weight-bold:   700;
  --weight-medium: 500;
  --weight-regular:400;
  --weight-light:  300;

  /* Leading */
  --leading-tight:  1.1;   /* Display text */
  --leading-body:   1.5;   /* Body text */
  --leading-loose:  1.8;   /* Small captions */

  /* Label style (applied as utility class .label) */
  /* font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-text-muted) */
}
```

**Typography rules for LLMs:**
- Headlines should be large and confident. A stat dashboard card headline should be `font-size: var(--text-display); font-weight: var(--weight-black)`.
- Section identifiers (e.g. "OVERVIEW", "TREND ANALYSIS") always use the label style: uppercase, 11px, medium weight, muted color, letter-spaced.
- Never center-align body text or labels. Left-align only (or right-align for numbers in tables).
- Avoid italics except for footnotes.

---

## 5. SPACING & LAYOUT TOKENS

```css
:root {
  /* Base unit: 8px */
  --space-1:   4px;
  --space-2:   8px;
  --space-3:   12px;
  --space-4:   16px;
  --space-5:   24px;
  --space-6:   32px;
  --space-7:   48px;
  --space-8:   64px;
  --space-9:   96px;
  --space-10: 128px;

  /* Radius */
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 6px;   /* Maximum. Never use pill/rounded shapes on data UI */

  /* Layout */
  --layout-max-width: 1440px;
  --layout-padding:   clamp(24px, 4vw, 64px);
  --grid-gap:         24px;

  /* Dashboard grid: 12 columns */
  /* Cards: use 3, 4, 6, or 12 column spans */
}
```

---

## 6. COMPONENT PATTERNS

These are canonical patterns. LLMs must replicate structure and proportions, substituting real data.

### 6.1 — KPI / Stat Card

```html
<div class="stat-card">
  <span class="label">TOTAL REVENUE</span>
  <div class="stat-value">€2.4M</div>
  <div class="stat-delta positive">↑ 12.4% vs prior period</div>
</div>

<style>
.stat-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6) var(--space-6) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.label {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
}
.stat-value {
  font-size: clamp(2rem, 4vw, 3.5rem);
  font-weight: 900;
  color: var(--color-text-primary);
  line-height: 1.0;
  letter-spacing: -0.02em;
}
.stat-delta {
  font-size: 13px;
  color: var(--color-text-muted);
}
.stat-delta.positive { color: var(--color-accent); }
</style>
```

### 6.2 — Section Header (Dashboard)

```html
<header class="section-header">
  <div class="section-meta">
    <span class="label">≡ COMPETITIVE LANDSCAPE</span>
  </div>
  <h2 class="section-title">Market Share by Segment</h2>
  <hr class="divider">
</header>

<style>
.section-header { margin-bottom: var(--space-7); }
.section-meta { margin-bottom: var(--space-3); }
.section-title {
  font-size: var(--text-heading-1);
  font-weight: var(--weight-bold);
  color: var(--color-text-primary);
  line-height: var(--leading-tight);
  margin: 0 0 var(--space-5) 0;
}
.divider {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 0;
}
</style>
```

### 6.3 — Data Table

```html
<table class="data-table">
  <thead>
    <tr>
      <th>ENTITY</th>
      <th class="num">VALUE</th>
      <th class="num">SHARE</th>
      <th class="num">ΔYOY</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Alpha Group</td>
      <td class="num">€4.2M</td>
      <td class="num">34%</td>
      <td class="num positive">+8.2%</td>
    </tr>
  </tbody>
</table>

<style>
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-body);
}
.data-table th {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  text-align: left;
  padding: var(--space-2) var(--space-3) var(--space-2) 0;
  border-bottom: 1px solid var(--color-border-strong);
}
.data-table td {
  padding: var(--space-3) var(--space-3) var(--space-3) 0;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-body);
}
.data-table .num { text-align: right; font-variant-numeric: tabular-nums; }
.data-table .positive { color: var(--color-accent); }
</style>
```

### 6.4 — Chart Container

```html
<div class="chart-block">
  <div class="chart-header">
    <span class="label">TREND ANALYSIS</span>
    <h3 class="chart-title">Monthly Active Users, 2024–2025</h3>
  </div>
  <div class="chart-area">
    <!-- Recharts / Chart.js / D3 renders here -->
  </div>
  <p class="chart-caption">Source: Internal analytics. Figures represent unique sessions.</p>
</div>

<style>
.chart-block {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
}
.chart-header { margin-bottom: var(--space-5); }
.chart-title {
  font-size: 1rem;
  font-weight: var(--weight-medium);
  color: var(--color-text-primary);
  margin: var(--space-2) 0 0 0;
}
.chart-area { width: 100%; min-height: 200px; }
.chart-caption {
  font-size: 11px;
  color: var(--color-text-faint);
  margin: var(--space-3) 0 0 0;
  letter-spacing: 0.02em;
}
</style>
```

### 6.5 — Dashboard Layout Shell

```html
<div class="dashboard">
  <header class="dash-header">
    <div class="dash-brand">
      <span class="label">≡ SYNTHESIS</span>
    </div>
    <div class="dash-meta">
      <span class="label">REPORT · Q1 2025</span>
    </div>
  </header>
  <main class="dash-body">
    <div class="dash-grid">
      <!-- Cards go here, use col-3 col-4 col-6 col-12 classes -->
    </div>
  </main>
</div>

<style>
.dashboard {
  font-family: var(--font-body);
  background: var(--color-bg);
  min-height: 100vh;
  padding: var(--space-6) var(--layout-padding);
  max-width: var(--layout-max-width);
  margin: 0 auto;
}
.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border-strong);
  margin-bottom: var(--space-8);
}
.dash-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--grid-gap);
}
.col-3  { grid-column: span 3; }
.col-4  { grid-column: span 4; }
.col-6  { grid-column: span 6; }
.col-8  { grid-column: span 8; }
.col-12 { grid-column: span 12; }
/* Responsive: collapse to 4-col on tablet, 1-col on mobile */
@media (max-width: 900px)  { .col-3,.col-4 { grid-column: span 6; } }
@media (max-width: 600px)  { .col-3,.col-4,.col-6,.col-8 { grid-column: span 12; } }
</style>
```

---

## 7. CHART STYLING RULES

For Recharts (React), Chart.js, Plotly, or D3 — always apply these settings:

```
- Chart background: transparent (no fill)
- Grid lines: stroke="#E2E2E2", strokeWidth=1, strokeDasharray="none"
- Axis lines: stroke="#C0C0C0", strokeWidth=1
- Axis tick labels: fill="#888888", fontSize=11, fontFamily="DM Sans", textTransform="uppercase"
- Bar fill (primary): #0A0A0A
- Bar fill (secondary): #C0C0C0
- Bar fill (highlighted): #2FCC6E
- Line stroke (primary): #0A0A0A, strokeWidth=2
- Line stroke (secondary): #C0C0C0, strokeWidth=1.5
- Area fill: use 15% opacity of line color, no gradient
- Dots/points: r=3, fill="white", stroke="currentColor", strokeWidth=2
- Tooltip: background="#FFFFFF", border="1px solid #E2E2E2", borderRadius=4, fontSize=12
- Legend: fontSize=11, textTransform="uppercase", letterSpacing="0.06em", color="#888888"
- No animation on initial render (static preferred for dashboards)
- Pie/donut charts: use only grayscale segments + one green segment for highlight
```

---

## 8. WRITING & LABEL CONVENTIONS

- **Section IDs** always start with `≡` followed by uppercase label: `≡ MARKET OVERVIEW`
- **Numbers** use European notation where appropriate: `€2.4M`, `34%`, `1,240`
- **Deltas** use `↑` / `↓` arrows, not `+/-` signs: `↑ 12.4%`
- **Dates** in labels: `Q1 2025`, `JAN–MAR 2025`, `2024 FY`
- **Source citations** always appear below charts in faint 11px text
- **No exclamation marks** anywhere in dashboards
- **No emoji** in any UI element

---

## 9. WHAT TO AVOID

| ❌ Never use | ✅ Instead use |
|---|---|
| Purple/teal/orange palette | Black, gray, white + one green accent |
| Rounded pill buttons | Sharp rect with 4px radius |
| Drop shadows on cards | 1px solid border |
| Gradient chart fills | Flat fills, single color |
| Centered headline layout | Left-aligned, editorial |
| Bold body text | Bold only on headlines/numbers |
| Multiple accent colors | Single accent (#2FCC6E) |
| Dark backgrounds | White/near-white only |
| Decorative icons | Text labels + unicode only |
| Auto-animations on charts | Static or one-time entrance |
| Sans-serif mixed with serif | DM Sans only throughout |

---

## 10. QUICK-START PROMPT TEMPLATE

When requesting a dashboard, use this structure:

```
[Paste full contents of this design reference]

---

Now create a [TYPE: dashboard / visualization / report page] about [TOPIC].

Data/context: [paste data or describe what the dashboard should show]

Requirements:
- Strictly follow the Synthesis Design Reference above
- Use the component patterns as written — do not invent new patterns
- HTML/CSS/JS (or React) in a single file
- Real placeholder numbers unless I provide data
- Include: [list sections, e.g. 4 KPI cards, 1 bar chart, 1 table]
```

---

*Synthesis Design Reference v1.0 — synthesiscg.com*  
*Generated from brand analysis of synthesiscg.com. Update when brand evolves.*
