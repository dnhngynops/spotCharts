/**
 * Milk & Honey LA design tokens — mirrors SPOTIFY_THEME in src/core/config.py.
 * Use CSS custom properties (var(--primary), etc.) in stylesheets.
 * Use these constants in JS/TS when you need the raw value (e.g. canvas charts).
 *
 * Source of truth: spotify-dashboard-figma-spec.html (Figma Spec v1)
 * Keep in sync with: frontend/src/index.css :root tokens
 */
export const THEME = {
  // Backgrounds
  background:    '#131C25',
  surface:       '#1E2A36',
  sidebarBg:     '#07131D',
  barBackground: '#263342',
  headerTop:     '#1C242B',
  headerMid:     '#121D26',
  // Text
  textPrimary:   '#C8D0D8',
  textBright:    '#E8EDF2',
  textMuted:     '#8C96A1',
  // Brand / Accent
  primary:       '#58C69D',
  accentLight:   '#6BD1A6',
  brandGreenRaw: '#6CCA98',
  // Semantic
  danger:        '#E74C3C',
  trendDown:     '#E84393',
  // Borders
  border:        '#313C45',
  // Component-specific backgrounds
  rowHover:      'rgba(255, 255, 255, 0.03)',
  rowDivider:    'rgba(255, 255, 255, 0.05)',
  statCardBg:    'rgba(0, 0, 0, 0.2)',
  // Legacy aliases — used by components not yet migrated to named tokens
  textTrack:     '#E8EDF2',   // = textBright
  textArtist:    '#8C96A1',   // = textMuted
  textSecondary: '#C8D0D8',   // = textPrimary
} as const
