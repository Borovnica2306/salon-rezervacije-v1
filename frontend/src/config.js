export const PAYMENT_MODE = 'PI_ECOSYSTEM';

export const THEMES = {
  Batik: {
    primary: '#8B6F47',
    secondary: '#D4A574',
    background: '#1A1410',
    surface: '#2A2118',
    text: '#F5E6D3',
    accent: '#C4956A',
  },
  Ubud: {
    primary: '#5B8C5A',
    secondary: '#A3C9A8',
    background: '#0D1A0D',
    surface: '#1A2E1A',
    text: '#E8F5E8',
    accent: '#7AB87A',
  },
  Sahara: {
    primary: '#C49A6C',
    secondary: '#E8C9A0',
    background: '#1A1408',
    surface: '#2E2414',
    text: '#F5EDE0',
    accent: '#D4A855',
  },
  Kente: {
    primary: '#D4A017',
    secondary: '#8B0000',
    background: '#0A0A08',
    surface: '#1A1A14',
    text: '#F5F0E0',
    accent: '#228B22',
  },
  Copacabana: {
    primary: '#00A88F',
    secondary: '#FF6B35',
    background: '#0A1014',
    surface: '#142028',
    text: '#E8F4F0',
    accent: '#FFB800',
  },
  Amazon: {
    primary: '#2D6A4F',
    secondary: '#95D5B2',
    background: '#0A100E',
    surface: '#14201C',
    text: '#D8F3DC',
    accent: '#52B788',
  },
  MidnightVelvet: {
    primary: '#C5A880',
    secondary: '#B89970',
    background: '#0A0A0B',
    surface: '#141416',
    text: '#FFFFFF',
    accent: '#C5A880',
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
}
