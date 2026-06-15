export const PAYMENT_MODE = 'PI_ECOSYSTEM';

export const THEMES = {
  Batik: {
    primary: '#8B6F47',
    secondary: '#D4A574',
    background: '#110E09',
    surface: '#2A2118',
    text: '#F5E6D3',
    accent: '#C4956A',
    gradientHint: '#1F1810',
  },
  Ubud: {
    primary: '#5B8C5A',
    secondary: '#A3C9A8',
    background: '#080F08',
    surface: '#1A2E1A',
    text: '#E8F5E8',
    accent: '#7AB87A',
    gradientHint: '#0F1F0F',
  },
  Sahara: {
    primary: '#C49A6C',
    secondary: '#E8C9A0',
    background: '#120E05',
    surface: '#2E2414',
    text: '#F5EDE0',
    accent: '#D4A855',
    gradientHint: '#261C0C',
  },
  Kente: {
    primary: '#D4A017',
    secondary: '#8B0000',
    background: '#08080A',
    surface: '#1A1A14',
    text: '#F5F0E0',
    accent: '#228B22',
    gradientHint: '#14120A',
  },
  Copacabana: {
    primary: '#00A88F',
    secondary: '#FF6B35',
    background: '#060C10',
    surface: '#142028',
    text: '#E8F4F0',
    accent: '#FFB800',
    gradientHint: '#0C1820',
  },
  Amazon: {
    primary: '#2D6A4F',
    secondary: '#95D5B2',
    background: '#060E0A',
    surface: '#14201C',
    text: '#D8F3DC',
    accent: '#52B788',
    gradientHint: '#0E1C16',
  },
  MidnightVelvet: {
    primary: '#C5A880',
    secondary: '#B89970',
    background: '#0A0A0B',
    surface: '#141416',
    text: '#FFFFFF',
    accent: '#C5A880',
    gradientHint: '#16141A',
  },
};

export const THEME_NAMES = Object.keys(THEMES);
export const DEFAULT_THEME = 'MidnightVelvet';

export function applyTheme(themeName) {
  const theme = THEMES[themeName] || THEMES[DEFAULT_THEME];
  const root = document.documentElement;
  root.style.setProperty('--color-primary', theme.primary);
  root.style.setProperty('--color-secondary', theme.secondary);
  root.style.setProperty('--color-background', theme.background);
  root.style.setProperty('--color-surface', theme.surface);
  root.style.setProperty('--color-text', theme.text);
  root.style.setProperty('--color-accent', theme.accent);
  root.style.setProperty('--color-gradient-hint', theme.gradientHint);
}
