export const PAYMENT_MODE = 'PI_ECOSYSTEM';

export const THEMES = {
  Batik: {
    primary: '#06B6D4',
    secondary: '#E2E8F0',
    background: '#0B132B',
    surface: '#1C2541',
    text: '#F1F5F9',
    accent: '#06B6D4',
    gradientHint: '#1C2541',
  },
  Ubud: {
    primary: '#A7F3D0',
    secondary: '#F59E0B',
    background: '#121713',
    surface: '#1E2A20',
    text: '#ECFDF5',
    accent: '#A7F3D0',
    gradientHint: '#14532D',
  },
  Sahara: {
    primary: '#EAB308',
    secondary: '#F97316',
    background: '#1C1310',
    surface: '#2C1E18',
    text: '#FEF3C7',
    accent: '#EAB308',
    gradientHint: '#451A03',
  },
  Kente: {
    primary: '#D4A017',
    secondary: '#8B0000',
    background: '#0A0A08',
    surface: '#1A1A14',
    text: '#F5F0E0',
    accent: '#228B22',
    gradientHint: '#14120A',
  },
  Copacabana: {
    primary: '#00A88F',
    secondary: '#FF6B35',
    background: '#0A1014',
    surface: '#142028',
    text: '#E8F4F0',
    accent: '#FFB800',
    gradientHint: '#0C1820',
  },
  Amazon: {
    primary: '#22C55E',
    secondary: '#10B981',
    background: '#05140B',
    surface: '#0D2818',
    text: '#D1FAE5',
    accent: '#22C55E',
    gradientHint: '#064E3B',
  },
  MidnightVelvet: {
    primary: '#38BDF8',
    secondary: '#7DD3FC',
    background: '#0A0D14',
    surface: '#131825',
    text: '#F0F9FF',
    accent: '#38BDF8',
    gradientHint: '#1E293B',
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
