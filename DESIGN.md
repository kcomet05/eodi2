# Eodi design system — "노선도 for two"

The app is a subway map of a couple's dates. Every screen borrows from Seoul metro signage:
one red line, ringed station dots, station-name lettering, plain paper. It should feel like a
well-printed transit map, not a dashboard.

## Principles
1. **The line carries meaning.** The red route line and station rings appear only where there is a
   sequence: course stops, onboarding steps, live progress, the 노선도 timeline. Never as decoration.
2. **One accent.** Line red is the only action/selection colour. Yellow (`--sun`) is reserved for
   anniversaries and "hot" badges. Plum ink is text and the partner's avatar.
3. **Flat paper.** Cards are paper on paper: surface colour + 1px hairline. Shadows only on things
   that float (tab bar, sheets, toast, map controls).
4. **Content first, controls second.** Names and times lead; secondary tools sit in one compact
   icon row per item.
5. **Thumb reach.** Primary navigation is a bottom tab bar; every target is ≥44px.

## Tokens (`:root` in index.html; dark values under `prefers-color-scheme` and `[data-theme=dark]`)
| Group | Tokens |
|---|---|
| Colour | `--bg` paper · `--card` surface · `--sunk` inputs/insets · `--fg` ink · `--muted` secondary ink · `--soft` tint fill · `--hair` card border · `--line` control border · `--edge` strong neutral border · `--accent`/`--accent-fg` line red · `--tint` red tint (selected rows) · `--sun`/`--sun-fg` anniversary yellow |
| Type | `--display` Do Hyeon (headings, station names, buttons) · `--body` IBM Plex Sans KR. Scale `--t-xs 12 / --t-sm 13 / --t-md 15 / --t-base 16 / --t-lg 18 / --t-xl 22 / --t-2xl 28` |
| Space | 4-pt: `--s1 4 · --s2 8 · --s3 12 · --s4 16 · --s5 20 · --s6 24 · --s8 32` |
| Radius | `--r-sm 8` (inline inputs) · `--r-md 12` (buttons, controls, inner cards) · `--r-lg 16` (cards) · `--r-pill` (chips, badges) |
| Size | `--h-sm 44` (icon buttons, chips) · `--h-md 52` (buttons, inputs) · `--h-lg 56` (primary CTA) · `--tab` tab bar height |
| Elevation | `--sh-float` only for floating layers |

## Components
- **Card** `.card` (and the legacy `.panel .rec .livebox .daypanel .nearby .budget .rank .nextsp`) — surface, hairline, `--r-lg`, 16px padding.
- **Buttons** `.btn` 52px · `.btn.primary` red · `.btn.ghost` surface + border · `.btn.small` 44px · `.ib` 44px square icon button · `.danger` outlined red.
- **Chips** `.chip` pill 44px; pressed = red. `.chips.rail` scrolls horizontally on one line.
- **Station** `.n` ringed number; **Line** `.rail i` 6px red.
- **Inputs** 52px, `--sunk` fill, `--line` border, red on focus.
- **Icons** one SVG sprite (`#i-*`), 20px, `stroke: currentColor`, 2px. No emoji in UI chrome.
- **Loader** `.ldr` three station dots pulsing along a short line (respects reduced motion).
- **Tab bar** `#tabs` five destinations; hidden during onboarding.
- **Sheet** bottom sheet with grab bar; **Toast** sits above the tab bar.

## Layout
Mobile-first single column, max 440px. At ≥960px the planner becomes two columns (sticky map left,
course right); other screens stay a centred column because they are lists.
