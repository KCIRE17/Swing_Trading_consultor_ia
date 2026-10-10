---
name: Kinetic Alpha
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#7bd0ff'
  on-secondary: '#00354a'
  secondary-container: '#00a6e0'
  on-secondary-container: '#00374d'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#e29100'
  on-tertiary-container: '#523200'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#c4e7ff'
  secondary-fixed-dim: '#7bd0ff'
  on-secondary-fixed: '#001e2c'
  on-secondary-fixed-variant: '#004c69'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2.25rem
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.375rem
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1.125rem
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1.25rem
    letterSpacing: -0.01em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: 0.875rem
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system establishes a high-conviction decision cockpit engineered for multi-day swing trading (3 to 10 market sessions). Moving away from archaic, monochrome command-line terminals and overly noisy gamified consumer apps, this system prioritizes algorithmic clarity, institutional rigor, and intellectual poise. The aesthetic fuses **Technical Modernism** with crisp **Tactile Micro-Surfacing**: high-density metrics exist alongside breathing room, subtle luminous gradients, and authoritative operational signifiers.

The experience evokes precision, tactical control, and calm under volatility. The UI highlights predictive confidence scores, statistical time-series projections (ARIMA, mean-reversion envelopes), and discrete risk-reward parameters with zero ambiguity. Every visual tier reinforces immediate signal triage: actionable market opportunities instantly contrast against neutral slate depths without causing cognitive fatigue during sustained analytical sessions.

## Colors

The palette balances a low-luminance, rich slate bedrock with vibrant, unambiguous market action signals.

- **Bedrock & Neutral Architecture (`#0f172a`)**: Derived from deep twilight graphite and balanced slate tints rather than absolute lifeless blacks. Surfaces transition from `#090d16` (canvas substrate) to `#131d31` (elevated analytical cards) and `#1e293b` (structural borders and dividers), providing optical depth without glare.
- **Primary / Bullish Conviction (`#10b981`)**: An authoritative emerald green reserved for affirmative swing signals: `BUY`, `LONG`, target hit markers, upside breakout probabilities, and positive Sharpe ratios. 
- **Secondary / Algorithmic Intelligence (`#38bdf8`)**: A technical electric sky blue used for system-level intelligence: ARIMA regression corridors, AI inference confidence tags, trailing stop overlays, and interactive crosshairs.
- **Tertiary / Market Equilibrium (`#f59e0b`)**: A warm amber utilized for `HOLD`, consolidated neutral regimes, pending order brackets, and medium-risk volatility warnings.
- **Critical / Bearish Trigger (`#f43f5e`)**: A sharp crimson coral deployed strictly for `SELL`, `SHORT`, stop-loss breach thresholds, and downside invalidation boundaries.

Functional background states for decision badges utilize a 12% alpha fill paired with a solid 30% border in their respective functional hues, ensuring sharp contrast and legible metric parsing across varying ambient lighting conditions.

## Typography

Typography employs a strict dual-engine schema:

1. **Plus Jakarta Sans (Structural & Narrative)**: Applied to all contextual narratives, structural module headers, trade rationality cards, model summaries, and navigational interfaces. It brings modern balance and geometric legibility without sterile stiffness.
2. **JetBrains Mono (Quantitative & Execution)**: Applied exclusively to tickers, quantitative dimensions, execution price tags, ARIMA forecasted bands, percentage deltas, stop levels, and backtest results. Tabular alignment prevents layout shifting when financial streaming rates update.

All monospaced labels rely on distinct tracking adjustments (`0.02em` to `0.04em`) to safeguard instant optical recognition inside dense analytical tables, high-density order books, and time-series chart coordinates.

## Layout & Spacing

The layout is built upon an adaptive 12-column analytical grid geared for dense, high-frequency situational awareness.

- **Breakpoints**: Mobile views (< 768px) stack modules into single-column priority feeds focusing on high-conviction signals and execution buttons. Tablet views (768px - 1199px) feature a multi-tier 6-column configuration. Desktop displays (1200px+) deliver a complete 12-column command panel: a 3-column screener and watchlist sidebar, a 6-column primary workspace for time-series charts and prediction intervals, and a 3-column AI rationale and trade management terminal.
- **Rhythm Rules**: Margins and internal gutters scale from `1rem` on compact displays to `1.5rem` / `2rem` on wide desktop workstations. Core components maintain internal padding based on `space-sm` (`0.5rem`) for compact data tables, `space-md` (`1rem`) for standard operational widgets, and `space-lg` (`1.5rem`) for primary signal spotlight hero cards.

## Elevation & Depth

Visual hierarchy operates through deliberate tonal progression, faint atmospheric edge glows, and calibrated dark-surface layering:

- **Level 0 (Canvas Core)**: `#090d16`. Ground-level canvas for charting backgrounds, canvas boundaries, and backtest logs.
- **Level 1 (Module Plates)**: `#111a2e`. Primary surfaces for charts, indicator bars, and signal lists. Framed with a 1px low-contrast structural border (`rgba(255, 255, 255, 0.07)`).
- **Level 2 (Active Focus & Flyouts)**: `#18243c`. Elevates popovers, parameter adjusters, trade setup details, and active time-series nodes. Features a subtle, tinted directional shadow (`0 8px 24px -4px rgba(2, 6, 23, 0.65)`).
- **Signal Ambient Aura**: High-conviction decision cards utilize an internal top-edge gradient line (1px tall) reflecting the trade state (Emerald for Buy, Crimson for Sell, Amber for Hold) paired with a muted downward gradient wash (`opacity: 0.04`) to establish clarity without visual clutter.

## Shapes

The interface adopts a disciplined, modern shape language (`roundedness: 1`). Subtly smoothed corners (`0.25rem` base, scaling to `0.5rem` on cards, and `0.75rem` on detached modal viewports) preserve the precise, instrumental feel appropriate for quantitative financial software. Pure circular shapes are restricted strictly to status indicators and progress rings. Pill-shaped buttons are explicitly avoided to preserve screen real estate and maintain visual density across compact data layouts.

## Components

### Action Buttons & Signal Triggers
- **Primary Decision Triggers**: Full-bleed background using functional colors (`#10b981` for long entries, `#f43f5e` for short exits), matched with dark high-contrast typography (`#090d16`, font weight 600) for maximum legibility. Hover states apply an internal brightness boost (+8%) rather than a layout-shifting shadow.
- **Secondary System Actions**: Flat slate plate (`#1e293b`) with an integrated 1px border (`rgba(255, 255, 255, 0.1)`), carrying neutral-to-sky typography for backtest iterations, time-horizon adjustments, and model recalibrations.

### Analytical Badges & Decision Chips
- Structured for instantaneous scanning: a monospaced ticker tag alongside a stylized conviction pill.
- **Signal Chips**: Feature a 10% saturated background, matching 1px border, a solid 6px status bead, and uppercase monospaced labels (`label-md`). Example: `[● BUY 8.4/10]`, `[▲ ARIMA +4.2%]`.

### Quantitative Data Tables & Lists
- Row heights are locked to 44px for balanced density, accented with hairline dividers (`rgba(255, 255, 255, 0.05)`).
- Hover states apply an interactive row illumination (`#152138`).
- Numeric values are right-aligned using `JetBrains Mono` with fixed tabular figures (`tnum`).

### Input Fields & Parameter Controls
- Inputs use `#0c1322` background fills with an inset 1px outline (`rgba(255, 255, 255, 0.12)`).
- Focus states display an electric sky highlight border (`#38bdf8`) paired with an ambient `0 0 0 3px rgba(56, 189, 248, 0.15)` focus ring. Unit tags (e.g., `USD`, `Rounds`, `σ`) sit inside the field using muted monospaced text.

### Signal Cards & Projection Panels
- Contain structured zones: (1) Asset Identity & Time Frame, (2) Horizon Window (e.g., "5-7 Ruedas"), (3) AI Model Consensus with dynamic ARIMA trajectory sparklines, and (4) Direct Target / Stop-Loss Matrix.
- Cards maintain structural border boundaries with no blurred glass artifacts, ensuring swift rendering during real-time data streaming.