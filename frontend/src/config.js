export const PAYMENT_MODE = 'PI_ECOSYSTEM';

// Inline SVG patterns per theme (opacity baked in, ~40-60px tiles)
const PATTERNS = {
  Sahara: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Cpath d='M0 30 Q15 10 30 30 Q45 50 60 30' fill='none' stroke='%23EAB308' stroke-width='0.8' opacity='0.07'/%3E%3Cpath d='M0 50 Q15 30 30 50 Q45 70 60 50' fill='none' stroke='%23F97316' stroke-width='0.5' opacity='0.04'/%3E%3C/svg%3E")`,
  Amazon: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='50' height='50'%3E%3Cpath d='M25 5 Q30 15 25 25 Q20 15 25 5Z' fill='%2322C55E' opacity='0.06'/%3E%3Cpath d='M10 30 Q15 40 10 50 Q5 40 10 30Z' fill='%2310B981' opacity='0.04'/%3E%3Cpath d='M40 35 Q45 42 40 50 Q35 42 40 35Z' fill='%2322C55E' opacity='0.05'/%3E%3C/svg%3E")`,
  Ubud: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='56' height='56'%3E%3Cpath d='M28 8 C36 16 36 40 28 48 C20 40 20 16 28 8Z' fill='none' stroke='%23A7F3D0' stroke-width='0.6' opacity='0.06'/%3E%3Ccircle cx='28' cy='28' r='3' fill='%23F59E0B' opacity='0.04'/%3E%3C/svg%3E")`,
  Copacabana: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='32'%3E%3Cpath d='M0 16 Q16 0 32 16 Q48 32 64 16' fill='none' stroke='%2300A88F' stroke-width='0.7' opacity='0.07'/%3E%3Cpath d='M0 24 Q16 8 32 24 Q48 40 64 24' fill='none' stroke='%23FFB800' stroke-width='0.4' opacity='0.03'/%3E%3C/svg%3E")`,
  Kente: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Crect x='0' y='0' width='20' height='20' fill='none' stroke='%23D4A017' stroke-width='0.6' opacity='0.06'/%3E%3Crect x='20' y='20' width='20' height='20' fill='none' stroke='%23228B22' stroke-width='0.6' opacity='0.05'/%3E%3Cline x1='0' y1='0' x2='20' y2='20' stroke='%238B0000' stroke-width='0.4' opacity='0.04'/%3E%3Cline x1='20' y1='20' x2='40' y2='40' stroke='%23D4A017' stroke-width='0.4' opacity='0.04'/%3E%3C/svg%3E")`,
  Batik: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48'%3E%3Ccircle cx='24' cy='24' r='8' fill='none' stroke='%2306B6D4' stroke-width='0.6' opacity='0.06'/%3E%3Ccircle cx='24' cy='24' r='3' fill='%2306B6D4' opacity='0.04'/%3E%3Ccircle cx='0' cy='0' r='4' fill='none' stroke='%23E2E8F0' stroke-width='0.4' opacity='0.03'/%3E%3Ccircle cx='48' cy='0' r='4' fill='none' stroke='%23E2E8F0' stroke-width='0.4' opacity='0.03'/%3E%3Ccircle cx='0' cy='48' r='4' fill='none' stroke='%23E2E8F0' stroke-width='0.4' opacity='0.03'/%3E%3Ccircle cx='48' cy='48' r='4' fill='none' stroke='%23E2E8F0' stroke-width='0.4' opacity='0.03'/%3E%3C/svg%3E")`,
  MidnightVelvet: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Ccircle cx='10' cy='10' r='1' fill='%2338BDF8' opacity='0.08'/%3E%3Ccircle cx='40' cy='5' r='0.6' fill='%237DD3FC' opacity='0.05'/%3E%3Ccircle cx='55' cy='30' r='0.8' fill='%2338BDF8' opacity='0.06'/%3E%3Ccircle cx='20' cy='45' r='1.2' fill='%237DD3FC' opacity='0.07'/%3E%3Ccircle cx='45' cy='52' r='0.5' fill='%2338BDF8' opacity='0.04'/%3E%3Cline x1='10' y1='10' x2='40' y2='5' stroke='%2338BDF8' stroke-width='0.2' opacity='0.03'/%3E%3Cline x1='40' y1='5' x2='55' y2='30' stroke='%237DD3FC' stroke-width='0.2' opacity='0.03'/%3E%3C/svg%3E")`,
};

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
  root.style.setProperty('--bg-pattern', PATTERNS[themeName] || PATTERNS[DEFAULT_THEME]);
}
