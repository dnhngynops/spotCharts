# Theme & Design System

**Brand:** Milk & Honey LA (`milkhoneyla.com`)
**Source of truth:** `spotify-dashboard-figma-spec.html` (Figma Spec v1)

Files to keep in sync:
- `frontend/src/index.css` — CSS custom properties (React app)
- `frontend/src/theme.ts` — JS/TS constants (for canvas/chart color values)
- `src/core/config.py` — `SPOTIFY_THEME` dict (Jinja2 HTML + PDF rendering)

---

## Color Tokens

### Backgrounds

| CSS Variable | Value | Role |
|---|---|---|
| `--bg` | `#131C25` | Page body |
| `--surface` | `#1E2A36` | Cards, section panels |
| `--sidebar-bg` | `#07131D` | Sidebar |
| `--bar-bg` | `#263342` | Popularity/progress bar track |
| `--header-top` | `#1C242B` | Dashboard header gradient start |
| `--header-mid` | `#121D26` | Dashboard header gradient mid |

### Text

| CSS Variable | Value | Role |
|---|---|---|
| `--text-primary` | `#C8D0D8` | Body text (default) |
| `--text-bright` | `#E8EDF2` | Track names, emphasis |
| `--text-muted` | `#8C96A1` | Secondary / meta / labels |

### Brand & Accent

| CSS Variable | Value | Role |
|---|---|---|
| `--primary` | `#58C69D` | Primary teal accent, interactive elements |
| `--accent-light` | `#6BD1A6` | Heading teal (h1–h6 default) |
| `--brand-green-raw` | `#6CCA98` | Active nav items, trend-up/new badges |

### Semantic

| CSS Variable | Value | Role |
|---|---|---|
| `--danger` | `#E74C3C` | Explicit content bar, error states |
| `--trend-down` | `#E84393` | Trending-down badge |

### Borders

| CSS Variable | Value | Role |
|---|---|---|
| `--border` | `#313C45` | Input borders, hard dividers |
| `--border-subtle` | `rgba(255,255,255,0.08)` | Section/card edges |
| `--border-divider` | `rgba(255,255,255,0.10)` | Table/list row dividers |

### Component Tokens

Added in v3.6.0. Scope: React dashboard only (not in Jinja2 templates or `config.py`).

| CSS Variable | Value | Role |
|---|---|---|
| `--row-hover` | `rgba(255,255,255,0.03)` | Table row hover background |
| `--row-divider` | `rgba(255,255,255,0.05)` | Table/list row border-bottom |
| `--stat-card-bg` | `rgba(0,0,0,0.2)` | Stat/overlap card background |

### Interactive Tints (not CSS variables — use inline)

| Value | Role |
|---|---|
| `rgba(108,202,152,0.10)` | Active nav background |
| `rgba(108,202,152,0.12)` | Card/button hover background |
| `rgba(108,202,152,0.20)` | Stat badge background |
| `rgba(108,202,152,0.06)` | Charting (on-chart) table row tint |
| `rgba(255,255,255,0.05)` | List item hover |

### Legacy Aliases (do not remove — used by templates)

| Alias | Resolves to |
|---|---|
| `--text-track` | `var(--text-bright)` |
| `--text-artist` | `var(--text-muted)` |
| `--text-secondary` | `var(--text-primary)` |

---

## Typography

### Fonts

| Font | Use | Loaded via |
|---|---|---|
| **Libre Franklin** | Headings (h1–h6), section titles, modal titles | Google Fonts |
| **Roboto** | Body text, UI elements, tables | Google Fonts |
| **JetBrains Mono** | Code, monospace labels, spec annotations | Google Fonts |

### Heading Scale — Libre Franklin

| Element | Size (px) | Size (em) | Weight | Color |
|---|---|---|---|---|
| Dashboard `h1` | 40px | 2.86em | 600 | `--text-primary` |
| Section title | 24px | 1.71em | 600 | `--text-primary` + 2px `--primary` border-bottom |
| Modal title | 25.6px | 1.83em | 700 | `--text-primary` |
| Playlist title | 20.8px | 1.49em | 400 | `--text-primary` |

### Body Scale — Roboto

| Element | Size (px) | Weight | Color | Notes |
|---|---|---|---|---|
| Body base | 14px | 400 | `--text-primary` | Set on `body` |
| Summary card value | 40px / 2.86em | 700 | `--primary` | line-height: 1 |
| Subtitle | 16px / 1.14em | 400 | `--text-primary` | |
| Timestamp / meta | 14.4px | 400 | `--text-muted` | |
| Track name | 13.6px | 500 | `--text-bright` | |
| Artist name / metadata | 13.6px | 400 | `--text-muted` | |
| Table headers | 12px | 600 | `--text-muted` | uppercase, letter-spacing: 0.5px |
| Filter labels | 11px | 700 | `--text-muted` | uppercase, letter-spacing: 0.08em |
| Summary card label | 0.85em | 400 | `--text-muted` | |

---

## Border Radius Scale

| Token | Value | Used for |
|---|---|---|
| sm | 3px | Badges, small pills |
| md | 4px | Inputs, selects |
| lg | 6px | Buttons, filter inputs |
| xl | 8px | Summary cards, stat cells |
| 2xl | 12px | Section panels, modals, sidebar |
| pill | 20px | CTA buttons, genre tags |
| full | 999px | Chart badge pills |

---

## Interaction & Animation Conventions

| State | Style |
|---|---|
| Card/button hover | `background: rgba(88,198,157,0.12); transform: translateY(-1px); transition: 0.2s/0.15s ease` |
| Hyperlink hover | `color: var(--primary)` only — NO underline |
| Filter inputs/selects | `outline: none` on all states |
| Active nav item | `color: var(--brand-green-raw); background: rgba(108,202,152,0.10)` |
| Tab active | `color: var(--primary); border-bottom: 2px solid var(--primary)` |
| Reset btn hover | `border-color: var(--primary); color: var(--primary)` |
| CTA button hover | `transform: scale(1.05)` |
| Sidebar collapse | `width` transition `0.25s ease`; labels fade `opacity: 0` |

---

## Layout

| Context | Grid | Min column |
|---|---|---|
| Summary Cards | `auto-fit` | 200px |
| Analytics Grid | `auto-fit` | 400px |
| Popularity / Explicit Grid | `auto-fit` | 200px |
| Overlap Stats | 3 fixed columns | — |
| Modal Stats | `auto-fit` | 100px |

- Section padding: `30px`
- Grid gaps (analyticsGrid, analyticsGrid2, statsRow): `30px`
- Sidebar expanded: `220px` / collapsed: `60px`
- Main content: `overflow-y: auto`, scrolls independently of sidebar
