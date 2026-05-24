---
version: alpha
name: Streamlit Minimal Console
target: streamlit
description: Design rules for Codex when generating Streamlit apps with a restrained black-and-white enterprise console style.

streamlit:
  page_config:
    layout: wide
    initial_sidebar_state: expanded
  theme_config_path: .streamlit/config.toml
  css_path: styles/design.css
  preferred_primitives:
    - st.set_page_config
    - st.sidebar
    - st.container
    - st.columns
    - st.tabs
    - st.expander
    - st.status
    - st.dataframe
    - st.code
    - st.download_button
    - st.chat_message
    - st.chat_input

colors:
  primary: "#000000"
  primary-hover: "#282828"
  canvas: "#ffffff"
  canvas-soft: "#efefef"
  canvas-softer: "#f3f3f3"
  border: "#e2e2e2"
  border-strong: "#afafaf"
  ink: "#000000"
  body: "#5e5e5e"
  mute: "#8a8a8a"
  on-dark: "#ffffff"
  code-bg: "#111111"
  code-text: "#f3f3f3"
  link: "#0000ee"
  success: "#166534"
  success-bg: "#dcfce7"
  warning: "#92400e"
  warning-bg: "#fef3c7"
  danger: "#991b1b"
  danger-bg: "#fee2e2"
  info: "#1e3a8a"
  info-bg: "#dbeafe"

typography:
  display-xxl:
    size: 52px
    weight: 700
    lineHeight: 64px
  display-xl:
    size: 36px
    weight: 700
    lineHeight: 44px
  display-lg:
    size: 32px
    weight: 700
    lineHeight: 40px
  display-md:
    size: 24px
    weight: 700
    lineHeight: 32px
  display-sm:
    size: 20px
    weight: 700
    lineHeight: 28px
  body-lg:
    size: 18px
    weight: 500
    lineHeight: 24px
  body-md:
    size: 16px
    weight: 400
    lineHeight: 24px
  body-md-strong:
    size: 16px
    weight: 500
    lineHeight: 20px
  body-sm:
    size: 14px
    weight: 400
    lineHeight: 20px
  body-sm-strong:
    size: 14px
    weight: 500
    lineHeight: 16px
  caption:
    size: 12px
    weight: 400
    lineHeight: 20px

spacing:
  xxs: 4px
  xs: 6px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  2xl: 24px
  3xl: 32px
  4xl: 48px

rounded:
  none: 0px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 999px
  full: 9999px

elevation:
  flat: none
  subtle: "rgba(0, 0, 0, 0.08) 0px 2px 8px 0px"
  card: "rgba(0, 0, 0, 0.12) 0px 4px 16px 0px"
  float: "rgba(0, 0, 0, 0.16) 0px 2px 8px 0px"
---

## Overview

This `DESIGN.md` is written for Codex when building or modifying Streamlit apps. The intended UI is a restrained, engineering-grade console: black, white, grayscale, high readability, minimal decoration, and clear review-oriented workflows.

The app should feel like a reliable internal product rather than a marketing landing page. Use Streamlit's native primitives first, then add only light CSS polish where Streamlit's built-in theme cannot express the design.

The visual system is a black-and-white duet:

- `{colors.primary}` black is the conversion anchor for the single main action in a visible section.
- `{colors.canvas}` white is the default app background.
- `{colors.canvas-soft}` and `{colors.canvas-softer}` create quiet separation for inputs, sidebars, cards, tables, and code-adjacent surfaces.
- Semantic colors are allowed only for state communication: success, warning, danger, and info. They must not become brand accents.

Streamlit is not a pixel-perfect React canvas. Do not fight it with heavy DOM overrides. Prefer stable primitives like `st.container`, `st.columns`, `st.tabs`, `st.expander`, `st.status`, `st.dataframe`, `st.code`, `st.download_button`, `st.chat_message`, and `st.chat_input`.

**Key characteristics:**

- Minimal monochrome interface with one primary black action per screen or major section.
- Pill-shaped actions for buttons, chips, filters, and download controls.
- `{rounded.xl}` 16 px card geometry for panels, review blocks, forms, and generated-output regions.
- Wide desktop layout by default, with sidebar controls and a main review workspace.
- Native Streamlit widgets first; CSS only for wrappers, cards, badges, typography tightening, and selected button/card polish.
- Technical outputs such as SQL, Python, JSON, logs, DTOs, YAML, and Markdown previews must use code-style containers.
- Generated or AI-assisted outputs must clearly show their state: `draft`, `manual review required`, `validated`, `blocked`, or `failed`.

## Streamlit implementation rules

### Required files

Use this structure for Streamlit UI work:

```text
project-root/
├─ DESIGN.md
├─ AGENTS.md
├─ streamlit_app.py
├─ .streamlit/
│  └─ config.toml
└─ styles/
   └─ design.css
```

`AGENTS.md` should instruct Codex to read `DESIGN.md` before changing any UI, Streamlit screen, CSS, layout, chart, form, or generated-output preview.

### Page configuration

At the top of the Streamlit entrypoint, configure the app before rendering UI:

```python
import streamlit as st

st.set_page_config(
    page_title="Agent Console",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

Use `layout="wide"` for admin, analytics, metadata, review, and chat-console interfaces. Use centered layout only for simple single-purpose forms.

### Theme configuration

Map design tokens into `.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#000000"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f3f3f3"
textColor = "#000000"
linkColor = "#0000ee"
codeBackgroundColor = "#111111"
codeTextColor = "#f3f3f3"
dataframeHeaderBackgroundColor = "#efefef"
baseRadius = "0.75rem"
buttonRadius = "999px"
borderColor = "#e2e2e2"
dataframeBorderColor = "#e2e2e2"
showWidgetBorder = true
showSidebarBorder = true
font = "sans-serif"
headingFont = "sans-serif"
codeFont = "monospace"

[theme.sidebar]
backgroundColor = "#f3f3f3"
secondaryBackgroundColor = "#ffffff"
textColor = "#000000"
```

Never rely only on ad hoc CSS for global color, border, radius, and type settings. Put what Streamlit supports into `config.toml`, then use `styles/design.css` for design-specific classes.

### CSS loading

Prefer this pattern:

```python
from pathlib import Path
import streamlit as st

css_path = Path("styles/design.css")
if css_path.exists():
    st.html(css_path)
```

Use CSS for wrapper classes, badges, cards, hero bands, compact labels, and callout surfaces. Avoid brittle selectors against generated Streamlit class names unless there is no stable alternative.

## Colors

### Brand and base

- **Primary black** (`{colors.primary}` — `#000000`): The only brand conversion color. Use it for primary Streamlit buttons, active step indicators, selected navigation, dark promo panels, and footer-like bands.
- **Primary hover** (`{colors.primary-hover}` — `#282828`): Hover or pressed treatment for black surfaces and black buttons.
- **Canvas** (`{colors.canvas}` — `#ffffff`): Default app background and main content surface.
- **Canvas soft** (`{colors.canvas-soft}` — `#efefef`): Soft gray fill for chips, filter rows, muted callouts, and secondary button areas.
- **Canvas softer** (`{colors.canvas-softer}` — `#f3f3f3`): Sidebar, widget regions, nested inputs, dataframe header alternatives, and subtle section backgrounds.
- **Border** (`{colors.border}` — `#e2e2e2`): Default card, dataframe, input, and divider border.
- **Border strong** (`{colors.border-strong}` — `#afafaf`): Focus-adjacent dividers, disabled boundaries, and secondary metadata borders.

### Text

- **Ink** (`{colors.ink}` — `#000000`): Headings and primary body text.
- **Body** (`{colors.body}` — `#5e5e5e`): Secondary paragraphs, help text, captions, form descriptions, and muted labels.
- **Mute** (`{colors.mute}` — `#8a8a8a`): Placeholder-like copy, run IDs, timestamps, low-priority metadata.
- **On dark** (`{colors.on-dark}` — `#ffffff`): Text on black panels and dark code-adjacent surfaces.
- **Link** (`{colors.link}` — `#0000ee`): Inline links only. Do not use link blue as a button or chart accent.

### Code and data

- **Code background** (`{colors.code-bg}` — `#111111`): Use for `st.code`-style technical output when custom wrappers are needed.
- **Code text** (`{colors.code-text}` — `#f3f3f3`): Text on dark code surfaces.

### Semantic states

Semantic colors exist because Streamlit apps often contain validation, data quality, AI output review, and job status states. Use them only for badges, validation summaries, alert rows, and state labels.

- **Success** (`{colors.success}` / `{colors.success-bg}`): Completed, validated, safe, accepted.
- **Warning** (`{colors.warning}` / `{colors.warning-bg}`): Needs review, draft-only, partial confidence, manual action required.
- **Danger** (`{colors.danger}` / `{colors.danger-bg}`): Failed, blocked, invalid, destructive, unsafe.
- **Info** (`{colors.info}` / `{colors.info-bg}`): Neutral explanation, run context, guidance, secondary status.

Do not use rainbow chart palettes by default. For charts, prefer grayscale plus one semantic color only when the state requires it.

## Typography

### Font family

Use Streamlit's `sans-serif` theme font by default. If the project explicitly installs a font, Inter is the preferred substitute because it works well for dense data apps and technical dashboards.

- Headings: sans-serif, weight 700.
- Body: sans-serif, weight 400.
- Emphasis and button labels: sans-serif, weight 500.
- Code: monospace.

Do not introduce decorative fonts, italic display styles, or letter-spaced hero text.

### Hierarchy

| Token | Size | Weight | Line Height | Streamlit use |
|---|---:|---:|---:|---|
| `{typography.display-xxl}` | 52px | 700 | 64px | Landing-style app title or rare hero header. |
| `{typography.display-xl}` | 36px | 700 | 44px | Main page title. |
| `{typography.display-lg}` | 32px | 700 | 40px | Section title in a wide layout. |
| `{typography.display-md}` | 24px | 700 | 32px | Card title, tab panel title, result title. |
| `{typography.display-sm}` | 20px | 700 | 28px | Sub-card heading, sidebar group title. |
| `{typography.body-lg}` | 18px | 500 | 24px | Lead paragraph or important explanation. |
| `{typography.body-md}` | 16px | 400 | 24px | Default copy and form help. |
| `{typography.body-md-strong}` | 16px | 500 | 20px | Button label, selected nav label, strong inline text. |
| `{typography.body-sm}` | 14px | 400 | 20px | Captions, metadata, table helper text. |
| `{typography.body-sm-strong}` | 14px | 500 | 16px | Badge label, chip label, compact table header. |
| `{typography.caption}` | 12px | 400 | 20px | Run ID, timestamp, file path, footnote. |

### Principles

- Use sentence-case for headings, buttons, and section labels.
- Use uppercase only for tiny badges or system states such as `DRAFT`, `FAILED`, `READY`.
- Keep labels direct: `Generate preview`, `Validate`, `Download SQL`, `Review evidence`.
- Avoid marketing-style headlines in internal tools.
- Do not hide important state in helper text; use a visible badge or alert.

## Layout

### Streamlit page anatomy

A typical Streamlit app should use this structure:

```text
Top title / context row
├─ Sidebar
│  ├─ app navigation
│  ├─ filters
│  ├─ profile/environment settings
│  └─ run controls
└─ Main area
   ├─ status strip
   ├─ input or search panel
   ├─ result tabs
   ├─ evidence / preview / validation columns
   └─ download or export actions
```

Use the sidebar for controls that change the working context. Use the main area for work product, review, evidence, and generated output.

### Spacing system

- Base unit: 4 px.
- Widget-to-widget spacing should feel compact but not cramped.
- Use `{spacing.lg}` 16 px inside small cards.
- Use `{spacing.2xl}` 24 px inside review cards and generated-output sections.
- Use `{spacing.3xl}` 32 px between major blocks.
- Use `{spacing.md}` 12 px between sibling buttons, chips, and inline badges.

### Grid and columns

Prefer these Streamlit layouts:

- **2-column review layout**: left for inputs/options, right for preview/evidence.
- **3-column KPI row**: metrics or run summary cards only.
- **Tabs**: separate `Overview`, `Evidence`, `Preview`, `Validation`, and `Logs`.
- **Expanders**: use for optional details, raw JSON, debug traces, or long evidence lists. Do not hide errors or blockers in collapsed expanders.

For a two-column design, use proportions like:

```python
left, right = st.columns([0.38, 0.62], gap="large")
```

For review output, prefer:

```python
overview_tab, evidence_tab, preview_tab, validation_tab, logs_tab = st.tabs(
    ["Overview", "Evidence", "Preview", "Validation", "Logs"]
)
```

### Responsive strategy

Streamlit handles much of the responsive behavior, but Codex should follow these rules:

- Keep the app usable on tablet widths.
- Avoid more than three columns in the main area.
- Avoid deeply nested columns.
- Put essential controls in the sidebar or at the top of the main panel.
- Long technical outputs must scroll horizontally in code blocks rather than breaking layout.
- Do not create fixed-pixel layouts that require a 1200 px viewport.

### Empty, loading, and error states

Every data-heavy section must have a state:

- Empty: explain what input/action is needed.
- Loading: use `st.status`, `st.spinner`, or a visible progress message.
- Success: show what changed and where the result is.
- Warning: show what needs manual review.
- Error: show the blocker and the next safe action.

Do not leave blank panels.

## Elevation and depth

| Level | Treatment | Use |
|---|---|---|
| Level 0 — Flat | No shadow, optional border. | Default Streamlit containers, tables, sidebars. |
| Level 1 — Subtle | `rgba(0,0,0,0.08) 0px 2px 8px` | Lightweight cards, summary panels. |
| Level 2 — Card | `rgba(0,0,0,0.12) 0px 4px 16px` | Primary input card, generated preview card, modal-like panels. |
| Level 3 — Float | `rgba(0,0,0,0.16) 0px 2px 8px` | Floating badge/pill or highly important callout only. |

Default to flat surfaces with clear borders. Use shadows sparingly. Streamlit apps often contain dense controls; excessive elevation makes them noisy.

## Shapes

### Radius scale

| Token | Value | Use |
|---|---:|---|
| `{rounded.none}` | 0px | Full-width dark bands, table grid edges when required. |
| `{rounded.md}` | 8px | Inputs, text areas, select boxes, compact internal fields. |
| `{rounded.lg}` | 12px | Small cards, status callouts. |
| `{rounded.xl}` | 16px | Main cards, review panels, generated-output regions. |
| `{rounded.pill}` | 999px | Primary buttons, secondary buttons, chips, tags, filters. |
| `{rounded.full}` | 9999px | Circular icon-only elements. |

Buttons and chips are pill-shaped. Cards are not pills. Generated-output panels use `{rounded.xl}`.

## Components

### App shell

**`app-shell`** — the whole Streamlit page.

- Use `st.set_page_config(layout="wide")`.
- Keep the default background `{colors.canvas}`.
- Use the sidebar for app-level controls and navigation.
- The main body starts with title, caption, and an optional status strip.

**`sidebar-control-panel`** — context and filters.

- Background follows Streamlit sidebar theme.
- Use compact labels and clear grouping.
- Put environment/profile selectors here.
- Do not put generated artifacts in the sidebar.

### Buttons

**`button-primary`** — the main action.

- Use `st.button(..., type="primary")`.
- Background `{colors.primary}`.
- Shape `{rounded.pill}` via `buttonRadius` in `config.toml`.
- One primary action per visible panel.
- Labels must be verbs: `Generate preview`, `Run analysis`, `Validate`, `Search`.

**`button-secondary`** — secondary action.

- Use regular `st.button` or a quiet custom pill.
- Background white or `{colors.canvas-soft}`.
- Text `{colors.ink}`.
- Use for `Clear`, `Reset`, `Refresh`, `Copy`, `Open details`.

**`download-button`** — export action.

- Use `st.download_button`.
- Keep it visually secondary unless exporting is the primary workflow result.
- File labels must specify the artifact type: `Download SQL preview`, `Download DTO draft`, `Download report`.

**`danger-action`** — destructive or risky action.

- Avoid destructive actions in Streamlit unless the user explicitly needs them.
- Never style destructive actions as the black primary conversion button.
- Use visible confirmation text and a danger badge.

### Cards and containers

**`card-content`** — default panel.

- Background `{colors.canvas}`.
- Border `{colors.border}`.
- Shape `{rounded.xl}`.
- Padding `{spacing.2xl}`.
- Use for form groups, result summaries, configuration blocks.

**`card-soft`** — muted panel.

- Background `{colors.canvas-softer}`.
- Border `{colors.border}`.
- Shape `{rounded.xl}`.
- Use for helper regions, empty states, and secondary explanations.

**`card-dark`** — polarity-flipped callout.

- Background `{colors.primary}`.
- Text `{colors.on-dark}`.
- Shape `{rounded.xl}`.
- Use sparingly for high-level app state, final summary, or prominent review warning.

**`generated-preview-card`** — generated artifact area.

- Use for SQL, DTO, Python, JSON, Markdown, Mermaid, YAML, or logs.
- Must include a visible badge such as `DRAFT` or `MANUAL REVIEW REQUIRED`.
- Must not include an action labeled `Execute`, `Deploy`, or `Apply` unless explicitly approved by project safety rules.

### Forms and inputs

**`text-input` / `text-area`**

- Use native `st.text_input` and `st.text_area`.
- Keep labels short and sentence-case.
- Use placeholder text for examples only, not required instructions.
- Put longer instructions above the widget as body text or inside a helper panel.

**`select` / `multiselect` / `radio` / `toggle`**

- Use native Streamlit widgets.
- Group related controls in the sidebar or a form card.
- Do not scatter critical controls across unrelated tabs.

**`form-submit`**

- Use `st.form` when multiple inputs should be submitted together.
- Keep the submit button at the bottom of the form.
- Use a primary button only for the form's main action.

### Tables and dataframes

**`dataframe`**

- Use `st.dataframe(..., use_container_width=True)` for interactive tables.
- Use `st.table` only for small static tables.
- Keep dataframe headers calm: grayscale, no loud accent backgrounds.
- Use semantic badges or a status column for `passed`, `warning`, `failed`, `draft`.

**`metric-row`**

- Use `st.metric` only for true numeric summaries.
- Do not overuse metrics for labels that are not numeric.
- Use no more than three or four metrics in a row.

### Technical output

**`code-preview`**

- Use `st.code(content, language="sql")`, `st.code(..., language="python")`, or the appropriate language.
- Long content should live in a tab or generated-preview card.
- Pair every generated preview with an explicit review state.

**`json-preview`**

- Use `st.json` for raw structured data.
- Use expanders for raw debug JSON when it is not the primary artifact.

**`logs-panel`**

- Logs are secondary. Put them in a `Logs` tab or expander.
- Errors and blockers are primary. Surface them above logs with a visible state badge.

### Chat UI

**`chat-console`**

- Use `st.chat_message` and `st.chat_input` for conversational flows.
- The chat transcript should stay clean and compact.
- Generated output should not be buried inside chat bubbles when it needs review. Put reviewable artifacts in a separate preview panel or tab.

**`assistant-message`**

- Use concise summaries.
- Include evidence links, run IDs, or source metadata when relevant.
- Avoid playful avatars or decorative icons unless they clarify role/state.

### Status and validation

**`status-strip`**

- Use a horizontal row of badges or compact cards near the top of the main area.
- Show `profile`, `environment`, `run status`, `last updated`, and `review state` when relevant.

**`status-badge`**

- Use semantic background colors only.
- Badge labels may be uppercase because they are system states.
- Examples: `DRAFT`, `RUNNING`, `VALIDATED`, `WARNING`, `FAILED`, `BLOCKED`.

**`validation-summary`**

- Show blockers first.
- Warnings second.
- Passed checks last.
- Do not hide failed validation inside collapsed sections.

### Navigation

**`sidebar-nav`**

- Use sidebar navigation for multipage apps.
- Keep labels short: `Design`, `Search`, `Analysis`, `Artifacts`, `Settings`.
- Active navigation uses black text and a subtle left border or pill fill.

**`tabs`**

- Use tabs for parallel views of the same result, not for unrelated pages.
- Recommended order: `Overview`, `Evidence`, `Preview`, `Validation`, `Logs`.

### Dark bands

Use black bands sparingly inside the main page. They are useful for:

- final run summary,
- manual-review warning,
- production-safety boundary,
- important callout.

Do not put large forms inside dark bands unless the form is the only interaction on the page.

## CSS utility classes

Create `styles/design.css` with utility classes Codex can reuse:

```css
.agent-card {
  background: #ffffff;
  border: 1px solid #e2e2e2;
  border-radius: 16px;
  padding: 24px;
  box-shadow: none;
}

.agent-card-soft {
  background: #f3f3f3;
  border: 1px solid #e2e2e2;
  border-radius: 16px;
  padding: 24px;
}

.agent-card-elevated {
  background: #ffffff;
  border: 1px solid #e2e2e2;
  border-radius: 16px;
  padding: 24px;
  box-shadow: rgba(0, 0, 0, 0.12) 0px 4px 16px 0px;
}

.agent-dark-band {
  background: #000000;
  color: #ffffff;
  border-radius: 16px;
  padding: 24px;
}

.agent-muted {
  color: #5e5e5e;
  font-size: 14px;
  line-height: 20px;
}

.agent-caption {
  color: #8a8a8a;
  font-size: 12px;
  line-height: 20px;
}

.agent-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  line-height: 16px;
}

.agent-badge-draft,
.agent-badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.agent-badge-success {
  background: #dcfce7;
  color: #166534;
}

.agent-badge-danger {
  background: #fee2e2;
  color: #991b1b;
}

.agent-badge-info {
  background: #dbeafe;
  color: #1e3a8a;
}

.agent-code-label {
  color: #5e5e5e;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
}
```

Avoid complex CSS that depends on Streamlit's generated DOM class names. If a selector looks like a hashed or generated class, do not use it unless it is isolated and explained.

## Example screen patterns

### Pattern 1 — Review console

Use for metadata design, code generation, analysis review, document extraction, or validation workflows.

```text
Sidebar
- Profile
- Environment
- Mode
- Filters
- Run options

Main
- Title + caption
- Status strip
- Left column: request/input form
- Right column: tabs for Overview / Evidence / Preview / Validation / Logs
- Download buttons under preview artifacts
```

Rules:

- The submit action is the only primary button.
- Generated outputs must show `DRAFT` or `MANUAL REVIEW REQUIRED`.
- Do not include production execution actions in the preview panel.

### Pattern 2 — Search and inspect

Use for metadata search, artifact search, dependency lookup, and table browsing.

```text
Sidebar
- Search scope
- Filters
- Sort options

Main
- Search query
- Results dataframe
- Selected row detail card
- Evidence / raw JSON expander
```

Rules:

- Use `st.dataframe` for results.
- Use tabs or columns for detail views.
- Keep filters in the sidebar unless they are part of the primary query.

### Pattern 3 — Chat plus artifact preview

Use for LLM-assisted workflows.

```text
Left/main column
- Chat transcript
- Chat input

Right column
- Current artifact preview
- Evidence
- Validation
- Download actions
```

Rules:

- Chat is for interaction; preview panels are for review.
- Do not make users scroll through chat bubbles to find generated SQL, code, or reports.
- Always separate model reasoning summaries from final artifacts.

### Pattern 4 — Run monitor

Use for asynchronous jobs or polling workflows.

```text
Top
- Run status strip

Main
- Progress/status container
- Current step
- Warnings/blockers
- Logs tab
- Result preview when complete
```

Rules:

- Use `st.status` or equivalent visible state.
- Surface failures immediately.
- Put raw logs behind a tab or expander.

## Wording rules

Use safe, review-oriented labels:

- `Generate preview`
- `Run analysis`
- `Validate draft`
- `Review evidence`
- `Download preview`
- `Download draft`
- `Refresh status`
- `Clear inputs`

Avoid labels that imply unsafe automation unless the project explicitly supports it:

- `Execute SQL`
- `Apply DDL`
- `Deploy to production`
- `Run stored procedure`
- `Auto-fix database`
- `Overwrite source`

Generated artifacts should use explicit state labels:

- `Draft-only`
- `Manual review required`
- `Validated`
- `Blocked`
- `Failed`

## Do's and Don'ts

### Do

- Do use `.streamlit/config.toml` as the first layer of visual styling.
- Do use `styles/design.css` for cards, badges, dark bands, and small design polish.
- Do use native Streamlit widgets before custom HTML.
- Do keep one black primary button per visible workflow section.
- Do use pill-shaped buttons and chips.
- Do use `{rounded.xl}` cards for review panels and generated-output areas.
- Do show generated output as draft/reviewable unless the workflow explicitly says otherwise.
- Do use `st.code`, `st.json`, and `st.dataframe` for technical content.
- Do keep errors, blockers, and validation failures visible.

### Don't

- Don't copy marketing-page patterns directly into Streamlit.
- Don't introduce extra brand accent colors for decoration.
- Don't use heavy gradients, decorative illustrations, or loud chart palettes.
- Don't rely on fragile generated Streamlit DOM selectors for core layout.
- Don't hide failed validation inside collapsed expanders.
- Don't make every card elevated; flat plus border is the default.
- Don't style destructive or risky actions as the primary black CTA.
- Don't bury generated SQL, code, DTOs, or reports inside chat messages only.
- Don't use all-caps headings; reserve uppercase for compact state badges.
- Don't use pixel-perfect fixed layouts that break on tablet widths.

## Codex checklist

Before finishing any Streamlit UI change, verify:

1. `DESIGN.md` was followed.
2. `.streamlit/config.toml` contains the theme mapping.
3. `st.set_page_config` is set in the entrypoint.
4. Primary actions are black, pill-shaped, and limited in number.
5. Cards use `{rounded.xl}` and calm borders.
6. Generated outputs are visibly marked as draft/reviewable.
7. Errors and validation blockers are visible without expanding hidden sections.
8. CSS is limited to stable utility classes or clearly justified overrides.
9. The UI works with Streamlit's wide layout and remains usable on narrower screens.
10. The implementation avoids unsafe wording such as `Execute`, `Apply DDL`, or `Deploy` unless explicitly required and approved.
